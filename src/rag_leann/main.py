from leann import LeannBuilder, LeannChat  
from pathlib import Path  
  
# Build index từ folder /data  
builder = LeannBuilder(  
    backend_name="hnsw",  
    embedding_mode="sentence-transformers",  
    embedding_model="intfloat/multilingual-e5-large",
    graph_degree=32,  
    complexity=64,  
    is_recompute=True,  # Tiết kiệm storage  
    is_compact=True  
)  
  
# Load markdown files từ folder /data  
data_dir = Path("./data/Truong_Bo_Kinh_Final")  
md_files = list(data_dir.glob("*.md"))  
  
for md_file in md_files:  
    with open(md_file, 'r', encoding='utf-8') as f:  
        content = f.read()  
        builder.add_text(content, metadata={"source": str(md_file)})  
  
# Build index 
print("[DEBUG] Building index...")  
index_path = "./truong_bo_kinh.leann"  
builder.build_index(index_path)  
print(f"[DEBUG] Index saved to: {index_path}")
# Chat với dữ liệu  
chat = LeannChat(  
    index_path=index_path,  
    llm_config={"type": "ollama", "model": "qwen2.5:7b"}  
)  
  
response = chat.ask(  
    "Kinh Phạm võng trình bày nội dung gì?",  
    top_k=5,  
    llm_kwargs={  
        "max_tokens": 512,  
        "temperature": 0.7  
    }  
)  
  
print(f"AI: {response}")