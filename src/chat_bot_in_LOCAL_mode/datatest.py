import os
import time
import random
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# --- CẤU HÌNH (Sửa lại cho khớp với lúc Ingest) ---
DB_PATH = "./chroma_db3"
MODEL_NAME = "intfloat/multilingual-e5-large-instruct" 

def main():
    print("⏳ Đang tải model và kết nối Database...")
    
    # 1. Load Model (Dùng GPU 1050Ti để test cho nhanh)
    try:
        embedding_model = HuggingFaceEmbeddings(
            model_name=MODEL_NAME,
            model_kwargs={'device': 'cpu'}, # Đổi thành 'cpu' nếu muốn test trên CPU
            encode_kwargs={'normalize_embeddings': True}
        )
    except Exception as e:
        print(f"❌ Lỗi load model: {e}")
        return

    # 2. Load ChromaDB
    if not os.path.exists(DB_PATH):
        print(f"❌ Không tìm thấy thư mục DB tại: {DB_PATH}")
        return

    db = Chroma(
        persist_directory=DB_PATH, 
        embedding_function=embedding_model
    )
    
    # 3. KIỂM TRA THỐNG KÊ CƠ BẢN
    # Truy cập trực tiếp vào collection bên dưới của Chroma để lấy số liệu thực
    collection_count = db._collection.count()
    print("\n" + "="*50)
    print(f"📊 THỐNG KÊ DATABASE")
    print("="*50)
    print(f"✅ Tổng số đoạn văn (chunks) trong DB: {collection_count}")
    
    if collection_count == 0:
        print("⚠️ Database rỗng! Hãy chạy lại script ingest_data.py.")
        return

    # 4. KIỂM TRA NGẪU NHIÊN (Sanity Check)
    # Lấy thử 1 dòng bất kỳ để xem Metadata có chuẩn không
    print("\n🔍 KIỂM TRA MẪU DỮ LIỆU NGẪU NHIÊN:")
    print("-" * 30)
    try:
        # Lấy random 1 ID
        random_idx = random.randint(0, collection_count - 1)
        # Chroma lưu ID mặc định dạng UUID, nhưng ta lấy list data để peek
        sample = db._collection.get(limit=1, offset=random_idx)
        
        if sample['documents']:
            print(f"📝 Nội dung (trích): {sample['documents'][0][:100]}...")
            print(f"🏷️  Metadata: {sample['metadatas'][0]}")
        else:
            print("⚠️ Không lấy được mẫu dữ liệu.")
    except Exception as e:
        print(f"⚠️ Không thể kiểm tra ngẫu nhiên: {e}")

    # 5. TEST TÌM KIẾM (INTERACTIVE LOOP)
    print("\n" + "="*50)
    print("🔎 CHẾ ĐỘ TEST TÌM KIẾM (Gõ 'exit' để thoát)")
    print("="*50)

    
    # Câu thần chú bắt buộc của E5
    E5_PREFIX = "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery: "

    while True:
        query = input("\nNhập câu hỏi test: ")
        if query.lower() in ['exit', 'quit', 'thoat']:
            break
            
        print(f"⏳ Đang tìm kiếm với E5: '{query}'...")
        
        # --- QUAN TRỌNG: Ghép chuỗi Instruct ---
        final_query = E5_PREFIX + query
        
        start_time = time.time()
        
        # Model E5 dùng Cosine Similarity (Khoảng cách Cosine)
        # Điểm càng thấp càng tốt (trong Chroma L2) hoặc càng cao càng tốt (nếu dùng Cosine)
        # Chroma mặc định trả về L2 Distance.
        results = db.similarity_search_with_score(final_query, k=3)
        
        end_time = time.time()
        
        print(f"\n--- Kết quả (trong {end_time - start_time:.4f}s) ---")
        
        for i, (doc, score) in enumerate(results):
            print(f"\n" + "-"*40)
            print(f"🏆 KẾT QUẢ #{i+1} | Score: {score:.4f}")
            print("-" * 40)
            
            # 1. In Nội dung
            print(f"📄 NỘI DUNG (Trích):")
            print(f"   {doc.page_content[:300].replace(chr(10), ' ')}...") # In 300 ký tự đầu, xóa xuống dòng thừa
            
            # 2. In Metadata (TOÀN BỘ)
            print(f"\n🏷️  METADATA:")
            if doc.metadata:
                # Duyệt qua từng cặp Key-Value trong metadata để in ra
                for key, value in doc.metadata.items():
                    print(f"   • {key}: {value}")
            else:
                print("   (Không có metadata)")
            
            print("-" * 40)
if __name__ == "__main__":
    main()