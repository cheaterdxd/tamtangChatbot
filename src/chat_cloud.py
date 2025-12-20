from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from src import config
from src.vector_store import vector_store
from src.prompts import RAG_PROMPT
from src.key_manager import key_manager

class ChatCloud:
    def __init__(self, provider="gemini"):
        self.provider = provider.lower()
        self.llm = self._init_llm()
        self.retriever = vector_store.db.as_retriever(search_kwargs={"k": 5})

    def _init_llm(self):
        if self.provider == "gemini":
            # Uses the current rotating key from key_manager
            return ChatGoogleGenerativeAI(
                model="models/gemini-2.5-flash",
                google_api_key=key_manager.get_current_key(),
                convert_system_message_to_human=True
            )
        elif self.provider == "openai":
            if not config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not found in .env")
            return ChatOpenAI(model="gpt-4o", api_key=config.OPENAI_API_KEY)
        elif self.provider == "anthropic":
            if not config.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not found in .env")
            return ChatAnthropic(model="claude-3-opus-20240229", api_key=config.ANTHROPIC_API_KEY)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def chat(self, question):
        """
        Executes the RAG chain: Retrieve -> Augmented Prompt -> LLM -> Answer
        """
        # Re-init Gemini key in case it rotated during retrieval (though less likely for Generation)
        if self.provider == "gemini":
             self.llm.google_api_key = key_manager.get_current_key()

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | RAG_PROMPT
            | self.llm
            | StrOutputParser()
        )

        return rag_chain.invoke(question)
