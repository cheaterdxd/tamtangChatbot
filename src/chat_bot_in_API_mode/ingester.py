import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src import config

class Ingester:
    def __init__(self):
        self.data_dir = config.DATA_DIR
        self.chunk_size = config.CHUNK_SIZE
        self.chunk_overlap = config.CHUNK_OVERLAP

    def load_documents(self):
        """Loads PDFs and Text files from the data directory."""
        documents = []
        
        # Load .txt files
        if os.path.exists(self.data_dir):
            txt_loader = DirectoryLoader(self.data_dir, glob="**/*.txt", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"})
            txt_docs = txt_loader.load()
            documents.extend(txt_docs)
            print(f"Loaded {len(txt_docs)} text documents.")

            # Load .pdf files
            pdf_loader = DirectoryLoader(self.data_dir, glob="**/*.pdf", loader_cls=PyPDFLoader)
            pdf_docs = pdf_loader.load()
            documents.extend(pdf_docs)
            print(f"Loaded {len(pdf_docs)} PDF documents.")
        else:
            print(f"Data directory {self.data_dir} does not exist.")

        return documents

    def split_documents(self, documents):
        """Splits documents into chunks."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Split {len(documents)} docs into {len(chunks)} chunks.")
        return chunks

ingester = Ingester()
