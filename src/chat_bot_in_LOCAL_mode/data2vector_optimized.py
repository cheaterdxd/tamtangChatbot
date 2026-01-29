import os
import glob
import torch # Uncomment if cuda debugging is needed
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# --- CONFIGURATION ---
DATA_FOLDER = "data/Truong_Bo_Kinh_Final"
DB_PATH = "./chroma_db3"
model_name = "intfloat/multilingual-e5-large-instruct"

# Configuration for running on GPU 1050Ti
model_kwargs = {'device': 'cuda'}
encode_kwargs = {'normalize_embeddings': True} # E5 requires normalization for accurate cosine similarity calculation

print(f"Loading model {model_name}...")
embedding_model = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)
# Check if GPU is detected (Optional)
print(f"GPU Available: {torch.cuda.is_available()}") 
print(f"GPU Name: {torch.cuda.get_device_name(0)}")

# 1. Splitter Configuration (Keep as is)
headers_to_split_on = [
    ("#", "Ten_bo_kinh"),
    ("##", "Ten_pham"),
    ("###", "Ten_bai_kinh"),
]
markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", " ", ""], # Ưu tiên ngắt đoạn trước
    chunk_size=1024, # Tăng lên vì E5-large support tới 512 tokens (~1500 chars), 512 là hơi ít cho song ngữ
    chunk_overlap=100
)
# 3. Logical processing function
def process_files():
    all_final_chunks = []
    md_files = glob.glob(os.path.join(DATA_FOLDER, "*.md"))

    for file_path in md_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 1. Tách metadata theo Header
        md_docs = markdown_splitter.split_text(content)
        
        for doc in md_docs:
            # 2. Xử lý Metadata chuẩn
            ten_bo_kinh = doc.metadata.get("Ten_bo_kinh", "Unknown")
            ten_pham = doc.metadata.get("Ten_pham", "")
            ten_bai_kinh = doc.metadata.get("Ten_bai_kinh", "")
            
            # Cập nhật metadata chuẩn để Router dùng được
            doc.metadata["Ten_bo_kinh"] = ten_bo_kinh
            doc.metadata["Ten_bai_kinh"] = ten_bai_kinh
            # Thêm một field chung để dễ search nếu cần
            doc.metadata["search_key"] = f"{ten_bo_kinh} {ten_bai_kinh}"

            # 3. CHUNKING CHIẾN LƯỢC: 
            # Dùng separator ưu tiên \n\n để giữ nguyên đoạn văn
            # Tăng chunk_size để bao trọn cả Pali và Việt (khoảng 1000-1500 chars)
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1200, 
                chunk_overlap=200,
                separators=["\n\n", "\n", "(?<=.)", " ", ""] # Regex lookbehind giữ dấu chấm
            )
            
            sub_docs = splitter.split_documents([doc])
            
            for sub_doc in sub_docs:
                # 4. CONTEXT ENRICHMENT
                # Đưa thông tin kinh vào đầu nhưng ngắn gọn hơn
                header_context = f"Kinh: {ten_bai_kinh} ({ten_bo_kinh})."
                
                # Format lại page_content: Context + Nội dung gốc
                sub_doc.page_content = f"{header_context}\n{sub_doc.page_content}"
                
                all_final_chunks.append(sub_doc)

    return all_final_chunks

# 4. Main program execution
if __name__ == "__main__":
    chunks = process_files() # You may need to redefine this function as above
    
    if chunks:
        print("Initializing embedding model on GPU GTX 1050Ti...")

        print("Vectorizing and saving to ChromaDB...")
        db = Chroma.from_documents(
            documents=chunks, 
            embedding=embedding_model, 
            persist_directory=DB_PATH
        )
        print("COMPLETED! 1050Ti processing finished.")