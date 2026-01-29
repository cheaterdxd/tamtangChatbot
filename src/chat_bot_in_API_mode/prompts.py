from langchain_core.prompts import ChatPromptTemplate

RAG_PROMPT = ChatPromptTemplate.from_template("""
You are a helpful AI assistant. Answer the user's question based strictly on the provided context below.
If the answer is not in the context, say "I don't have enough information in the provided documents to answer this."

<context>
{context}
</context>

Question: {question}
Answer:
""")
