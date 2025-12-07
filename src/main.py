import argparse
import sys
import os

# Ensure src is in path if run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingester import ingester
from src.vector_store import vector_store

def run_ingest():
    print("🚀 Starting Ingestion Process...")
    docs = ingester.load_documents()
    if not docs:
        print("⚠️ No documents found to ingest.")
        return

    chunks = ingester.split_documents(docs)
    
    # Batch process to be safe and efficient
    BATCH_SIZE = 1  # Reduced batch size to mitigate Rate Limit / Quota issues
    total_chunks = len(chunks)
    
    for i in range(0, total_chunks, BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        print(f"Processing batch {i//BATCH_SIZE + 1}/{(total_chunks + BATCH_SIZE - 1)//BATCH_SIZE}...")
        vector_store.add_documents(batch)
        
    print("✅ Ingestion Complete.")

def run_query(query_text):
    print(f"🔍 Querying: '{query_text}'")
    results = vector_store.query(query_text)
    
    print("\n--- Results ---\n")
    for i, doc in enumerate(results):
        print(f"[{i+1}] Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"Content: {doc.page_content[:200]}...") # Preview
        print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description="Vectorization Tool CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Ingest command
    subparsers.add_parser("ingest", help="Ingest documents from /data folder")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query the vector database")
    query_parser.add_argument("text", type=str, help="Query text")

    args = parser.parse_args()

    if args.command == "ingest":
        run_ingest()
    elif args.command == "query":
        run_query(args.text)

if __name__ == "__main__":
    main()
