import os
import glob
import torch # Uncomment if cuda debugging is needed
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# --- CONFIGURATION ---
DATA_FOLDER = "data/Truong_Bo_Kinh_Final"
DB_PATH = "./chroma_db2"
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
    
    # 1. Lấy danh sách file
    md_files = glob.glob(os.path.join(DATA_FOLDER, "*.md"))
    print(f"Tìm thấy {len(md_files)} file markdown.")

    for file_path in md_files:
        print(f"Processing: {os.path.basename(file_path)}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # A. Tách theo Header (để lấy Metadata)
        md_docs = markdown_splitter.split_text(content)
        
        # B. Tách nhỏ (Recursive)
        chunked_docs = text_splitter.split_documents(md_docs)
        
        # --- C. HEADER INJECTION (QUAN TRỌNG NHẤT VỚI E5) ---
        for doc in chunked_docs:
            # Lấy thông tin metadata
            ten_bo_kinh = doc.metadata.get("Ten_bo_kinh", "Không rõ")
            ten_pham = doc.metadata.get("Ten_pham", "")
            ten_bai_kinh = doc.metadata.get("Ten_bai_kinh", "")
            
            # Tạo chuỗi ngữ cảnh
            # Với E5, ta viết thẳng nội dung bổ sung vào
            context_str = f"Bộ kinh: {ten_bo_kinh}"
            if ten_pham:
                context_str += f" - Phẩm: {ten_pham}"
            if ten_bai_kinh:
                context_str += f" - Bài: {ten_bai_kinh}"

            # GHI ĐÈ NỘI DUNG CŨ:
            # Biến đoạn văn từ: "Như vầy tôi nghe..."
            # Thành: "Tài liệu: Kinh Phạm Võng... \nNội dung: Như vầy tôi nghe..."
            doc.page_content = f"{context_str}\nNội dung: {doc.page_content}"
            
            # Metadata kỹ thuật (giữ nguyên)
            doc.metadata["source_file"] = os.path.basename(file_path)
            
        all_final_chunks.extend(chunked_docs)

    print(f"-> Tổng cộng đã tạo ra {len(all_final_chunks)} chunks dữ liệu.")
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