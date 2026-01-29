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

    # Query command (Raw Retrieval)
    query_parser = subparsers.add_parser("query", help="Raw retrieval from vector database")
    query_parser.add_argument("text", type=str, help="Query text")

    # Cloud Chat command
    chat_cloud_parser = subparsers.add_parser("chat-cloud", help="Chat using Cloud LLMs (Gemini, OpenAI, Claude)")
    chat_cloud_parser.add_argument("question", type=str, help="Your question")
    chat_cloud_parser.add_argument("--provider", type=str, default="gemini", choices=["gemini", "openai", "anthropic"], help="LLM Provider")

    # Local Chat command
    chat_local_parser = subparsers.add_parser("chat-local", help="Chat using Local LLM (Ollama)")
    chat_local_parser.add_argument("question", type=str, help="Your question")

    args = parser.parse_args()

    if args.command == "ingest":
        run_ingest()
    elif args.command == "query":
        run_query(args.text)
    elif args.command == "chat-cloud":
        from src.chat_cloud import ChatCloud
        bot = ChatCloud(provider=args.provider)
        print(f"🤖 (Cloud - {args.provider}) Thinking...")
        answer = bot.chat(args.question)
        print(f"\n💡 Answer:\n{answer}\n")
    elif args.command == "chat-local":
        from src.chat_local import ChatLocal
        bot = ChatLocal()
        print(f"🤖 (Local - Ollama) Thinking...")
        answer = bot.chat(args.question)
        print(f"\n💡 Answer:\n{answer}\n")

if __name__ == "__main__":
    main()
