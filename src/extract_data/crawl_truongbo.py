import asyncio
import re
import os
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup

# --- CẤU HÌNH ---
BASE_URL = "https://tipitaka.com.vn/category/tipi%e1%b9%adaka/tipi%e1%b9%adaka-mula/suttapitaka-tang-kinh/dighanikaya-kinh-truong-bo/"
OUTPUT_FOLDER = "Truong_Bo_Kinh_Final"
TOTAL_PAGES = 34 

# Tạo thư mục
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def clean_text(text):
    if not text: return ""
    # Xóa xuống dòng và khoảng trắng thừa
    text = text.replace('\xa0', ' ').replace('\n', ' ').replace('\r', '').strip()
    return re.sub(r'\s+', ' ', text)

def sanitize_filename(name):
    # Giữ lại các ký tự chữ, số, dấu chấm, gạch ngang, khoảng trắng
    # Loại bỏ các ký tự không hợp lệ cho tên file hệ thống: / \ : * ? " < > |
    safe_name = re.sub(r'[\\/*?:"<>|]', "", name)
    return safe_name.strip()

async def crawl_page(crawler, page_num):
    if page_num == 1:
        url = BASE_URL
    else:
        url = f"{BASE_URL}page/{page_num}/"

    print(f"⏳ Trang {page_num}/{TOTAL_PAGES}: {url}")

    result = await crawler.arun(
        url=url,
        bypass_cache=True,
        wait_for="div.entry-content"
    )

    if not result.success:
        print(f"   ❌ Lỗi tải trang {page_num}")
        return

    soup = BeautifulSoup(result.html, 'html.parser')
    entry_content = soup.select_one("div.entry-content")

    if not entry_content:
        return

    # Lấy tất cả các dòng trong các bảng
    rows = entry_content.select("table tr")
    md_output = []
    
    # Biến để lưu tên file (Mặc định nếu không tìm thấy sẽ là Page_X)
    filename_title = f"Page_{page_num}"
    found_title = False

    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            pali = clean_text(cols[0].get_text())
            viet = clean_text(cols[1].get_text())

            # Bỏ qua dòng rác (Tipitaka.org...)
            if (not pali and not viet) or "Tipitaka.org" in pali or "Việt dịch" in viet:
                continue

            # --- LOGIC TÌM TÊN FILE ---
            # Dòng tiêu đề thường là dòng đầu tiên có nội dung thực sự.
            # Đặc điểm: Chứa số thứ tự bài kinh (VD: "11.") và tên kinh (VD: "sutta", "Kinh")
            if not found_title:
                # Kiểm tra nếu dòng này trông giống tiêu đề (ngắn gọn < 150 ký tự và có từ khóa)
                if len(pali) < 150 and ("sutta" in pali.lower() or "kinh" in viet.lower()):
                    # ĐÂY LÀ DÒNG BẠN MUỐN LÀM TÊN FILE
                    # Format: "11. Dasuttarasuttaṃ - 34. Kinh Thập thượng"
                    raw_title = f"{pali} - {viet}"
                    filename_title = sanitize_filename(raw_title)
                    
                    # Thêm vào nội dung file MD dưới dạng Header 1
                    md_output.append(f"# {raw_title}\n")
                    
                    found_title = True
                    continue # Đã lấy làm tiêu đề rồi thì bỏ qua, không in lại thành nội dung thường

            # --- NỘI DUNG CHÍNH ---
            # Format: [Pali] \n [Việt]
            md_output.append(f"[{pali}]\n[{viet}]\n")

    # --- LƯU FILE ---
    if md_output:
        # Tên file cuối cùng: VD "11. Dasuttarasuttaṃ - 34. Kinh Thập thượng.md"
        file_path = os.path.join(OUTPUT_FOLDER, f"{filename_title}.md")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Source: {url}\n\n")
            f.write("\n".join(md_output))
        
        print(f"   ✅ Đã lưu: {filename_title}.md")
    else:
        print(f"   ⚠️ Trang {page_num} không có dữ liệu.")

async def main():
    async with AsyncWebCrawler(verbose=False) as crawler:
        # Chạy vòng lặp qua 34 trang
        for i in range(1, TOTAL_PAGES + 1):
            await crawl_page(crawler, i)
            await asyncio.sleep(1) # Nghỉ ngắn

if __name__ == "__main__":
    asyncio.run(main())