import time
import google.api_core.exceptions
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from src import config
from src.key_manager import key_manager
from src.rate_limiter import rate_limiter

class VectorStore:
    def __init__(self):
        self.persist_directory = config.DB_DIR
        self.embeddings = self._init_embeddings()
        self.db = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )

    def _init_embeddings(self):
        """Initializes embeddings with the current active key."""
        return GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004", 
            google_api_key=key_manager.get_current_key(),
            task_type="retrieval_document"
        )
    
    def _refresh_embeddings(self):
        """Re-initializes embeddings with a new key (after rotation)."""
        self.embeddings = self._init_embeddings()
        # Update the DB's embedding function reference if needed
        self.db._embedding_function = self.embeddings

    def add_documents(self, chunks):
        """Adds documents to ChromaDB with retry logic for Quota errors."""
        attempt = 0
        # Allow cycling through all keys multiple times (e.g., 3 rounds)
        max_attempts = len(key_manager.keys) * 3 
        
        while attempt < max_attempts:
            # Apply Rate Limiting
            rate_limiter.wait_if_needed()

            try:
                self.db.add_documents(chunks)
                rate_limiter.record_request()
                print(f"✅ Added {len(chunks)} chunks to DB.")
                return  # Success
            except Exception as e:
                # Check for Quota/ResourceExhausted errors
                is_quota_error = "429" in str(e) or "ResourceExhausted" in str(e)
                
                if is_quota_error:
                    print(f"❌ Quota exceeded (Attempt {attempt+1}/{max_attempts}). Switching key...")
                    key_manager.switch_key()
                    self._refresh_embeddings()
                    attempt += 1
                    
                    # If we've tried all keys, wait significantly longer before next round
                    if attempt > 0 and attempt % len(key_manager.keys) == 0:
                        wait_time = 20 * (attempt // len(key_manager.keys))
                        print(f"🛑 All keys hit limits. Sleeping {wait_time}s to cool down...")
                        time.sleep(wait_time)
                    else:
                        time.sleep(2) # Short wait for key switch
                else:
                    print(f"❌ Error adding documents: {e}")
                    raise e
        
        print("❌ Failed to add documents after multiple attempts/key rotations.")
        raise Exception("Persistent Quota Exceeded across all provided API keys.")

    def query(self, query_text, k=5):
        """Queries the database."""
        # Querying also consumes quota, should rate limit?
        # Typically retrieval query is cheap/free on some models or consumes read quota.
        # Embedding the query string consumes quota.
        
        retries = 0
        while retries < len(key_manager.keys) * 2:
            try:
                # Need to update embedding function if key changed previously? 
                # Yes, make sure db uses current embeddings
                self.db._embedding_function = self.embeddings
                
                results = self.db.similarity_search(query_text, k=k)
                return results
            except Exception as e:
                is_quota_error = "429" in str(e) or "ResourceExhausted" in str(e)
                if is_quota_error:
                    print(f"❌ Quota exceeded during query. Switching key...")
                    key_manager.switch_key()
                    self._refresh_embeddings()
                    retries += 1
                    time.sleep(1)
                else:
                    raise e
        return []

vector_store = VectorStore()
