# Vectorization & RAG Tool

This tool provides a pipeline to ingest text and PDF documents, chunk them, embedding them using Google Gemini, and store them in a local ChromaDB vector database. It includes mechanisms for rate limiting and API key rotation for free tier usage.

## Features
- **Data Ingestion**: Supports `.txt` and `.pdf` files.
- **RAG Pipeline**: Chunking -> Embedding -> Vector Store (ChromaDB).
- **Google Client**: Uses `langchain-google-genai` (Gemini).
- **Rate Limiter**: Automatically pauses to respect RPM/TPM limits.
- **Key Rotation**: Automatically switches API keys on Quota errors.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys**:
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEYS=your_key_1,your_key_2,your_key_3
   ```

## Usage

### Ingest Data
Place your files in `data/` folder, then run:
```bash
python src/main.py ingest
```

### Query Data
```bash
python src/main.py query "Your question here"
```

## Configuration
Adjust settings in `src/config.py`:
- `RPM_LIMIT`, `TPM_LIMIT`: Tune for your specific plan.
- `CHUNK_SIZE`: Adjust text splitting size.

# Tài liệu tam tạng sử dụng
- https://tipitaka.org/romn/#4 
- https://www.tamtangpaliviet.net/ 

# Một số rào cản hiện tại
- Phần "Tìm kiếm" (Vector Database): Phụ thuộc vào Gemini Embedding
Dữ liệu trong Database hiện tại được mã hóa (vector hóa) bởi model text-embedding-004 của Google.
Do đó, để tìm kiếm được trong DB này, bạn bắt buộc phải dùng đúng model text-embedding-004 để mã hóa câu hỏi đầu vào. Bạn không thể dùng OpenAI hay model khác để tìm kiếm trực tiếp trên dữ liệu vector này (vì "ngôn ngữ số" của mỗi hãng khác nhau).
- Phần "Trả lời/Chat" (Generation): HOÀN TOÀN TỰ DO
Sau khi hệ thống tìm ra được các đoạn văn bản (Context) liên quan, đó chỉ là văn bản thuần túy (text).
Bạn có thể lấy các đoạn văn bản này đưa cho BẤT KỲ model nào (GPT-4, Claude, Llama 3 chạy local, hay Gemini) để nhờ nó đọc và trả lời câu hỏi.
- Tóm lại:
    - Bạn bị "khóa" với Gemini ở khâu Lưu trữ & Tìm kiếm (trừ khi bạn xóa DB và chạy ingest lại bằng model khác).
    - Bạn thoải mái chọn model để Hỏi đáp/Chat. Ví dụ: Dùng Gemini (miễn phí) để tìm tài liệu, rồi dùng GPT-4 để viết câu trả lời cho hay.