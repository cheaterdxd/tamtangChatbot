import os
import pandas as pd
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from collections import Counter

# --- CẤU HÌNH ---
DB_PATH = "./chroma_db3" # Đảm bảo đúng đường dẫn DB bạn vừa tạo
MODEL_NAME = "intfloat/multilingual-e5-large-instruct"

def inspect_chroma_db():
    if not os.path.exists(DB_PATH):
        print(f"❌ Lỗi: Không tìm thấy thư mục {DB_PATH}")
        return

    print("⏳ Đang tải Embedding model (cần để khởi tạo class Chroma)...")
    # Thực ra chỉ cần class wrapper, không cần load model nặng vào VRAM nếu chỉ get metadata
    # Tuy nhiên LangChain bắt buộc có embedding_function
    embedding_model = HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        model_kwargs={'device': 'cpu'}, # Dùng CPU cho nhẹ vì không tính toán vector
        encode_kwargs={'normalize_embeddings': True}
    )

    print(f"📂 Đang kết nối vào DB tại: {DB_PATH}")
    vectorstore = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embedding_model
    )

    # Lấy toàn bộ dữ liệu (chỉ lấy metadata để đếm cho nhanh)
    # db.get() trả về dict keys: ['ids', 'embeddings', 'documents', 'metadatas']
    print("📊 Đang quét dữ liệu...")
    data = vectorstore.get() 
    
    total_chunks = len(data['ids'])
    metadatas = data['metadatas']
    
    print(f"\n=== TỔNG QUAN ===")
    print(f"Tổng số chunks trong DB: {total_chunks}")
    
    # Đếm theo tên bài kinh
    counter = Counter()
    for m in metadatas:
        # Lấy key Ten_bai_kinh, nếu không có thì ghi là 'Unknown'
        name = m.get('Ten_bai_kinh', 'Unknown')
        counter[name] += 1
        
    # Hiển thị dạng bảng đẹp
    print("\n=== THỐNG KÊ CHI TIẾT ===")
    df = pd.DataFrame.from_dict(counter, orient='index', columns=['Số lượng Chunks'])
    df.index.name = 'Tên Bài Kinh'
    df = df.sort_values(by='Số lượng Chunks', ascending=False)
    
    pd.set_option('display.max_rows', None) # Hiện hết bảng
    pd.set_option('display.max_colwidth', None)
    print(df)
    
    # Kiểm tra riêng Kinh Phạm Võng (vì bạn quan tâm)
    target = "Kinh Phạm Võng" # Hoặc tên chính xác trong DB
    found = False
    for name in df.index:
        if target.lower() in name.lower():
            print(f"\n✅ Tìm thấy '{name}': {df.loc[name, 'Số lượng Chunks']} chunks")
            found = True
            
    if not found:
        print(f"\n⚠️ Cảnh báo: Không tìm thấy bài nào tên giống '{target}'")

if __name__ == "__main__":
    inspect_chroma_db()