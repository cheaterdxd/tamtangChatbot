import chainlit as cl
from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os, difflib, re

# ==================================================
# 1. CẤU HÌNH & XỬ LÝ DỮ LIỆU LIST.MD (QUAN TRỌNG)
# ==================================================

def load_and_parse_list_kinh(file_path):
    """
    Đọc file list.md và tách ra 2 danh sách:
    1. full_lines: Để gửi cho LLM đọc hiểu ngữ cảnh.
    2. clean_metadata_keys: Chỉ chứa phần Header 3 (cột cuối cùng) để filter DB.
    """
    full_lines = []
    clean_metadata_keys = []
    
    try:
        if not os.path.exists(file_path):
            print(f"⚠️ Cảnh báo: Không tìm thấy file {file_path}")
            return [], []
            
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue # Bỏ qua dòng trống hoặc header
                
                full_lines.append(line)
                
                # Logic Parse: Tách theo dấu '|' và lấy phần tử cuối cùng
                # Vì cấu trúc file của bạn là: No. Name | Header 1 | Header 2 | Header 3 (Metadata Target)
                parts = line.split("|")
                if len(parts) > 1:
                    # Lấy phần cuối cùng và xóa khoảng trắng thừa
                    target_key = parts[-1].strip()
                    clean_metadata_keys.append(target_key)
                else:
                    # Fallback nếu dòng không có dấu |
                    clean_metadata_keys.append(line)
                    
        return full_lines, clean_metadata_keys
    except Exception as e:
        print(f"❌ Lỗi đọc file list.md: {e}")
        return [], []
# Load dữ liệu
LIST_FILE_PATH = "data/Truong_Bo_Kinh_Final/list.md"
LIST_KINH_FULL, LIST_METADATA_CLEAN = load_and_parse_list_kinh(LIST_FILE_PATH)

print(f"DEBUG: Đã load {len(LIST_METADATA_CLEAN)} kinh target.")

if LIST_METADATA_CLEAN:
    print(f"DEBUG Sample Target: '{LIST_METADATA_CLEAN[1]}'") # Nên ra: Brahmajālasuttaṃ(Kinh Phạm Võng)

def normalize_kinh_name(llm_output, metadata_list):
    """
    So khớp output của LLM với danh sách Metadata CHUẨN (cột cuối cùng).
    """
    if not llm_output or "None" in llm_output:
        return None
        
    # 1. Vệ sinh Output của LLM (Xóa số thứ tự kiểu "1. ", "07. ")
    # LLM thường trả về: "1. Brahmajālasuttaṃ" -> cần clean thành "Brahmajālasuttaṃ"
    clean_output = re.sub(r'^\d+[\.\s]+', '', llm_output).strip()
    
    # 2. Tìm kiếm chính xác trước (Case insensitive)
    for key in metadata_list:
        if clean_output.lower() == key.lower():
            return key
            
    # 3. Tìm kiếm gần đúng (Fuzzy Match)
    # cutoff=0.4: Chấp nhận độ giống 40% (vì output LLM thường ngắn hơn tên đầy đủ trong DB)
    matches = difflib.get_close_matches(clean_output, metadata_list, n=1, cutoff=0.4)
    
    if matches:
        return matches[0]
    
    # 4. Fallback: Kiểm tra "chứa trong" (Contains)
    # Ví dụ LLM ra "Phạm Võng" -> Match với "Brahmajālasuttaṃ(Kinh Phạm Võng)"
    for key in metadata_list:
        if clean_output.lower() in key.lower():
            return key
            
    return None

# Cấu hình Local LLM
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "qwen2.5:7b"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large-instruct"
DB_VECTOR="./chroma_db3"
# ==================================================
# 2. HÀM ROUTER (TRÍCH XUẤT FILTER)
# ==================================================
def extract_filter(query: str, llm):
    """
    Hàm này hỏi LLM xem câu hỏi thuộc về bộ kinh nào trong LIST_KINH.
    """
    router_template = """
    Bạn là một trợ lý phân loại tài liệu Phật giáo.
    Nhiệm vụ: Xác định xem câu hỏi của người dùng đang đề cập đến bộ kinh nào trong danh sách dưới đây.
    
    DANH SÁCH KINH:
    {list_kinh}
    
    CÂU HỎI: {question}
    
    YÊU CẦU:
    - Nếu câu hỏi nhắc đến tên kinh hoặc nội dung đặc thù của một kinh trong danh sách, hãy trả về CHÍNH XÁC tên đó.
    - Nếu không xác định được hoặc câu hỏi chung chung, hãy trả về "None".
    - CHỈ TRẢ VỀ TÊN KINH HOẶC "None". KHÔNG GIẢI THÍCH.
    """
    
    prompt = ChatPromptTemplate.from_template(router_template)
    chain = prompt | llm | StrOutputParser()
    
    try:
        # Gửi FULL LIST cho LLM để nó có ngữ cảnh (bao gồm cả tên Pali và Việt ở cột đầu)
        result = chain.invoke({"list_kinh": "\n".join(LIST_KINH_FULL), "question": query})
        cleaned_result = result.strip().replace("'", "").replace('"', "")
        return cleaned_result
    except Exception as e:
        print(f"Lỗi Router: {e}")
        return "None"

# ==================================================
# 3. KHỞI TẠO SESSION (ON START)
# ==================================================
@cl.on_chat_start
async def on_chat_start():
    print("--- Bắt đầu khởi tạo App ---")
    
    # A. Load Embeddings 
    model_kwargs = {'device': 'cpu'} # Hoặc cuda
    encode_kwargs = {'normalize_embeddings': True}
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
        multi_process=False
    )
    
    # B. Load VectorStore (Chroma)
    # Giả sử bạn lưu DB ở thư mục "./chroma_db"
    if not os.path.exists(DB_VECTOR):
         await cl.Message("⚠️ Lỗi: Không tìm thấy thư mục './chroma_db2'. Vui lòng Ingest dữ liệu trước!").send()
         return

    vectorstore = Chroma(
        persist_directory=DB_VECTOR,
        embedding_function=embeddings # Đổi tên collection nếu bạn đặt khác
    )
    
    # C. Load LLM (Ollama)
    llm = ChatOllama(
        base_url=OLLAMA_URL,
        model=MODEL_NAME,
        temperature=0.2 # Router cần chính xác, temperature thấp
    )
    
    # D. Lưu vào Session để dùng lại ở mỗi tin nhắn
    cl.user_session.set("vectorstore", vectorstore)
    cl.user_session.set("llm", llm)
    
    await cl.Message(content="Trợ lý ảo đã sẵn sàng!").send()

# ==================================================
# 4. XỬ LÝ TIN NHẮN (MAIN LOGIC)
# ==================================================
@cl.on_message
async def on_message(message: cl.Message):
    llm = cl.user_session.get("llm")
    vectorstore = cl.user_session.get("vectorstore")
    
    user_query = f"Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery: {message.content}"
    
    msg_processing = cl.Message(content="🤔 Đang suy nghĩ...")
    await msg_processing.send()
    
    # 1. Router chạy
    detected_kinh_raw = await cl.make_async(extract_filter)(user_query, llm)
    print(f"🤖 Router Output: {detected_kinh_raw}") # VD: 1. Brahmajālasuttaṃ
    
    # 2. Chuẩn hóa: Map output của LLM vào LIST_METADATA_CLEAN
    detected_kinh = normalize_kinh_name(detected_kinh_raw, LIST_METADATA_CLEAN)
    print(f"🎯 DB Key Normalized: {detected_kinh}")

    search_kwargs = {"k": 3}
    
    if detected_kinh:
        # QUAN TRỌNG: Lúc này detected_kinh đã khớp 100% với DB Metadata
        search_kwargs["filter"] = {
            "$or": [    
                {"Ten_bai_kinh": detected_kinh},
                {"Ten_bo_kinh": detected_kinh}
            ]
        }
        filter_msg = f"\n*(Giới hạn tìm kiếm: **{detected_kinh}**)*"
    else:
        # Nếu Router ra None hoặc map không được -> Tìm tất cả
        print("🌐 Searching all documents (Fallback)")
        filter_msg = "\n*(Tìm kiếm trên toàn bộ dữ liệu)*"

    print(f"DEBUG FILTER KWARGS: {search_kwargs}") # Kiểm tra lần cuối ở đây

    # 3. Retrieve
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs
    )
    
    docs = await retriever.ainvoke(user_query)
    
    # Debug in ra terminal (nếu muốn)
    print(f"DEBUG: Tìm thấy {len(docs)} docs")

    # Tạo các phần tử UI (Sources) để hiển thị trên Chainlit
    source_elements = []
    for i, doc in enumerate(docs):
        # Lấy tên nguồn từ metadata
        source_name = f"Nguồn {i+1} ({doc.metadata.get('Ten_bai_kinh', 'Doc')})"
        
        # Tạo text element
        source_elements.append(
            cl.Text(content=doc.page_content, name=source_name, display="side")
        )
    
    if not docs:
        await msg_processing.remove()
        await cl.Message(content=filter_msg + "\n\nXin lỗi, tôi không tìm thấy thông tin liên quan trong kinh điển để trả lời câu hỏi này.").send()
        return

# --- BƯỚC 5: GENERATION (CHỈ CÒN LLM) ---
    
    rag_template = """
    Dựa vào các đoạn văn sau đây từ kinh điển để trả lời câu hỏi.
    Nếu không có thông tin, hãy nói là không biết, đừng bịa ra.
    
    Context:
    {context}
    
    Câu hỏi: {question}
    
    Yêu cầu: Trả lời (chi tiết và trang nghiêm) theo các thông tin đã có.
    Ngôn ngữ: chỉ sử dụng ngôn ngữ tiếng Việt. 
    """
    rag_prompt = ChatPromptTemplate.from_template(rag_template)
    
    # Format docs thành chuỗi string
    context_str = "\n\n".join(doc.page_content for doc in docs)
    
    # Định nghĩa Chain (Lúc này chỉ còn Prompt -> LLM -> Parser)
    # Vì ta đã có context_str rồi, không cần retriever trong chain nữa
    runnable = rag_prompt | llm | StrOutputParser()
    
    # --- BƯỚC 6: STREAM KẾT QUẢ ---
    # Gửi message có đính kèm source_elements
    res = cl.Message(content=filter_msg + "\n\n", elements=source_elements)
    
    # Chạy chain với input trực tiếp
    async for chunk in runnable.astream({"context": context_str, "question": user_query}):
        await res.stream_token(chunk)
    
    await res.send()
    await msg_processing.remove()