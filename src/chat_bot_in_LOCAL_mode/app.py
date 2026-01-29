import chainlit as cl
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama
# sử dụng langchain_core
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- CẤU HÌNH ---
DB_PATH = "./chroma_db"  # Đường dẫn tới folder DB bạn vừa tạo
EMBEDDING_MODEL = "intfloat/multilingual-e5-large-instruct" # Phải khớp với model lúc Ingest
LLM_MODEL = "qwen2.5:7b" # Model chạy trên Ollama


llm = ChatOllama(
    model=LLM_MODEL,
    temperature=0.3, # Giữ cho câu trả lời trang nghiêm, ít sáng tạo linh tinh
    base_url="http://localhost:11434"
)

def extract_filter(user_query, llm):
    """
    Hàm này dùng LLM để trích xuất tên kinh từ câu hỏi.
    Trả về: Tên kinh chính xác hoặc "None"
    """
    router_template = """
    Bạn là một hệ thống phân loại dữ liệu. 
    Dưới đây là danh sách các bộ Kinh có trong cơ sở dữ liệu:
    {list_kinh}
    
    Câu hỏi của người dùng: "{query}"
    
    Nhiệm vụ: 
    Hãy xem trong câu hỏi của người dùng có nhắc đến tên bộ Kinh nào trong danh sách trên không?
    - Nếu có: Hãy trả về tên chính xác của bộ Kinh đó (copy y hệt từ danh sách).
    - Nếu không: Hãy trả về đúng chữ "None".
    
    Chỉ trả về kết quả, không giải thích gì thêm.
    """
    
    prompt = ChatPromptTemplate.from_template(router_template)
    chain = prompt | llm | StrOutputParser()
    
    # Chạy chain để lấy tên kinh
    extracted_kinh = chain.invoke({
        "list_kinh": "\n".join(LIST_KINH), 
        "query": user_query
    })
    
    return extracted_kinh.strip()

# 1. Khởi tạo tài nguyên (Chạy 1 lần khi app start)
@cl.on_chat_start
async def on_chat_start():
    msg = cl.Message(content="🙏 Đang khởi động hệ thống Chatbot Phật học...")
    await msg.send()

    # A. Load Embedding Model (Chạy trên GPU 1050Ti)
    embedding = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cuda'}, # Dùng GPU để vector hóa câu hỏi user cho nhanh
        encode_kwargs={'normalize_embeddings': True}
    )

    # B. Load ChromaDB
    vectorstore = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embedding
    )
    
    # C. Tạo Retriever (Người tìm kiếm)
    # k=3: Lấy 3 đoạn kinh văn liên quan nhất
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3} 
    )

    # # D. Load LLM (Chạy trên CPU Xeon - qua Ollama)
    # llm = ChatOllama(
    #     model=LLM_MODEL,
    #     temperature=0.3, # Giữ cho câu trả lời trang nghiêm, ít sáng tạo linh tinh
    #     base_url="http://localhost:11434"
    # )

    # E. Thiết kế Prompt (Câu thần chú)
    template = """Bạn là một trợ lý ảo Phật học uy tín, thông tuệ kinh điển.
    Hãy trả lời câu hỏi của người dùng dựa trên thông tin được cung cấp trong phần Context bên dưới.

    Yêu cầu bắt buộc:
    1. Trả lời bằng ngôn ngữ trang trọng, từ bi, đúng chánh pháp.
    2. Nếu trong Context có đoạn tiếng Pali, hãy trích dẫn nguyên văn câu Pali đó ra.
    3. Cuối câu trả lời, hãy ghi rõ nguồn trích dẫn (Tên Kinh, Tên Phẩm) có trong Context.
    4. Nếu thông tin không có trong Context, hãy nói "Tại hạ chưa tìm thấy thông tin này trong kho dữ liệu hiện tại", tuyệt đối không được tự bịa ra.

    Context (Kinh văn tham khảo):
    {context}

    Câu hỏi của thí chủ: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

    # F. Tạo Chain (Dây chuyền xử lý)
    def format_docs(docs):
        return "\n\n".join([doc.page_content for doc in docs])

    # Lưu retriever và runable vào session user để dùng lại
    cl.user_session.set("retriever", retriever)
    
    # Định nghĩa luồng RAG cơ bản
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    cl.user_session.set("rag_chain", rag_chain)
    
    msg.content = f"🪷 Hệ thống đã sẵn sàng! Đang sử dụng trí tuệ của {LLM_MODEL}."
    await msg.update()

# 2. Xử lý khi người dùng chat
@cl.on_message
async def on_message(message: cl.Message):
    rag_chain = cl.user_session.get("rag_chain")
    retriever = cl.user_session.get("retriever")

    detected_kinh = await cl.make_async(extract_filter)(message.content, llm)
    search_kwargs = {"k": 3}
    if detected_kinh != "None" and detected_kinh in LIST_KINH:
        print(f"🎯 Đang lọc theo: {detected_kinh}") # Log để debug
        search_kwargs["filter"] = {"Ten_Kinh": detected_kinh}
        
        # Gửi thông báo nhỏ cho user biết (Optional)
        await cl.Message(content=f"🔍 Đang tìm kiếm giới hạn trong: **{detected_kinh}**").send()
    else:
        print("🌐 Đang tìm trên toàn bộ dữ liệu")
    # Bước 1: Tìm kiếm tài liệu nguồn (để hiển thị cho user xem)
    source_documents = await cl.make_async(retriever.invoke)(message.content)
    
    # Tạo các element hiển thị nguồn (Text Box đẹp mắt)
    text_elements = []
    if source_documents:
        for i, doc in enumerate(source_documents):
            source_name = f"Nguồn {i+1}: {doc.metadata.get('Ten_Kinh', 'N/A')} - {doc.metadata.get('Ten_Pham', 'N/A')}"
            text_elements.append(
                cl.Text(content=doc.page_content, name=source_name, display="side")
            )

    # Bước 2: Gửi câu hỏi cho LLM và Stream câu trả lời về
    msg = cl.Message(content="", elements=text_elements)
    
    async for chunk in rag_chain.astream(message.content):
        await msg.stream_token(chunk)

    await msg.send()