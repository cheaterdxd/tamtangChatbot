from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from src import config
from src.vector_store import vector_store
from src.prompts import RAG_PROMPT

class ChatLocal:
    def __init__(self):
        self.llm = ChatOllama(
            base_url=config.OLLAMA_BASE_URL,
            model=config.OLLAMA_MODEL
        )
        self.retriever = vector_store.db.as_retriever(search_kwargs={"k": 5})

    def chat(self, question):
        """
        Executes the RAG chain locally.
        Make sure Ollama is running: `ollama serve` and `ollama pull <model>`
        """
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | RAG_PROMPT
            | self.llm
            | StrOutputParser()
        )

        try:
            return rag_chain.invoke(question)
        except Exception as e:
            return f"Error connecting to Local LLM (Ollama). Is it running? Details: {e}"
