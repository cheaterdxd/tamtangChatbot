import asyncio
import re
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup

# Hàm làm sạch text
def clean_text(text):
    if not text: return ""
    # Xóa khoảng trắng thừa, thay thế xuống dòng bằng khoảng trắng
    text = text.replace('\xa0', ' ').replace('\n', ' ').strip()
    return re.sub(r'\s+', ' ', text)

async def main():
    # Link bài kinh (Đã verify là chạy được)
    url = "https://tipitaka.com.vn/category/tipi%e1%b9%adaka/tipi%e1%b9%adaka-mula/suttapitaka-tang-kinh/dighanikaya-kinh-truong-bo/"

    async with AsyncWebCrawler(verbose=True) as crawler:
        print(f"🚀 Đang tải HTML từ: {url}")
        
        result = await crawler.arun(
            url=url,
            bypass_cache=True,
            wait_for="div.entry-content"
        )

        if not result.success:
            print("❌ Lỗi tải trang.")
            return

        soup = BeautifulSoup(result.html, 'html.parser')
        entry_content = soup.select_one("div.entry-content")
        
        if not entry_content:
            print("❌ Không tìm thấy nội dung.")
            return

        rows = entry_content.select("table tr")
        print(f"✅ Đang xử lý {len(rows)} dòng dữ liệu...")

        md_output = []
        
        # Thêm tiêu đề file (tùy chọn, có thể bỏ nếu muốn file sạch trơn)
        # md_output.append(f"# Dữ liệu Kinh Trường Bộ\n") 

        for row in rows:
            cols = row.find_all("td")
            
            # Chỉ lấy dòng có đủ 2 cột
            if len(cols) >= 2:
                pali = clean_text(cols[0].get_text())
                viet = clean_text(cols[1].get_text())

                # 1. Lọc bỏ các dòng rác/tiêu đề bảng
                if (not pali and not viet) or "Tipitaka.org" in pali or "Việt dịch" in viet:
                    continue
                
                # 2. Xử lý các dòng tiêu đề lớn (như "11. Dasuttarasuttaṃ")
                # Nếu bạn muốn giữ tiêu đề này nhưng format khác, hoặc bỏ qua thì sửa ở đây.
                # Hiện tại tôi sẽ để nó vào format [] luôn cho đồng bộ, hoặc bạn có thể dùng if để tách.
                
                # Format đúng yêu cầu:
                # [đoạn pali]
                # [đoạn tiếng việt tương ứng]
                formatted_block = f"[{pali}]\n[{viet}]\n"
                
                md_output.append(formatted_block)

        # Xuất file
        filename = "Kinh_Pali_Viet.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(md_output))
            
        print(f"🎉 Đã xuất file đúng format: {filename}")

if __name__ == "__main__":
    asyncio.run(main())