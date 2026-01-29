import asyncio
import re
import os
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup

# --- CẤU HÌNH ---
# Link danh mục Kinh Trung Bộ
BASE_URL = "https://tipitaka.com.vn/category/tipi%e1%b9%adaka/tipi%e1%b9%adaka-mula/suttapitaka-tang-kinh/majjhimanikaya-kinh-trung-bo/"
OUTPUT_FOLDER = "data/Kinh_Trung_Bo_Data"
START_PAGE = 1
# Kinh Trung Bộ có 152 bài, ta cứ cho chạy dư ra 1 chút, code sẽ tự dừng nếu hết bài
MAX_PAGES = 160 

# Tạo thư mục lưu trữ
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def clean_text(text):
    if not text: return ""
    # Xóa các ký tự xuống dòng thừa, khoảng trắng kép
    text = text.replace('\xa0', ' ').replace('\n', ' ').replace('\r', '').strip()
    return re.sub(r'\s+', ' ', text)

def sanitize_filename(name):
    # Loại bỏ các ký tự không được phép trong tên file Windows/Mac
    safe_name = re.sub(r'[\\/*?:"<>|]', "", name)
    return safe_name.strip()

async def crawl_page(crawler, page_num):
    # Tạo URL: Trang 1 là base url, các trang sau thêm /page/x/
    if page_num == 1:
        url = BASE_URL
    else:
        url = f"{BASE_URL}page/{page_num}/"

    print(f"⏳ Đang xử lý Trang {page_num}: {url}")

    # Crawl và chờ thẻ div.entry-content xuất hiện
    result = await crawler.arun(
        url=url,
        bypass_cache=True,
        wait_for="div.entry-content"
    )

    if not result.success:
        print(f"   ❌ Không thể truy cập trang {page_num} (Có thể đã hết bài).")
        return False # Báo hiệu dừng lại

    soup = BeautifulSoup(result.html, 'html.parser')
    entry_content = soup.select_one("div.entry-content")

    if not entry_content:
        print(f"   ⚠️ Trang {page_num} không có nội dung bài kinh.")
        return False

    # Lấy tất cả các dòng trong bảng
    rows = entry_content.select("table tr")
    md_output = []
    
    # Biến lưu tên file
    filename_title = f"Bai_kinh_so_{page_num}"
    found_title = False

    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            pali = clean_text(cols[0].get_text())
            viet = clean_text(cols[1].get_text())

            # Bỏ qua các dòng rác hệ thống
            if (not pali and not viet) or "Tipitaka.org" in pali or "Việt dịch" in viet:
                continue

            # --- LOGIC TÌM TÊN BÀI KINH ĐỂ ĐẶT TÊN FILE ---
            # Thường dòng tiêu đề sẽ chứa từ "sutta" (kinh) và ngắn gọn
            if not found_title:
                if len(pali) < 150 and ("sutta" in pali.lower() or "kinh" in viet.lower()):
                    # Tạo tên file: VD "01. Mūlapariyāyasuttaṃ - Kinh pháp môn căn bản"
                    raw_title = f"{pali} - {viet}"
                    filename_title = sanitize_filename(raw_title)
                    
                    # Đưa tiêu đề vào nội dung file luôn
                    md_output.append(f"# {raw_title}\n")
                    found_title = True
                    continue 

            # --- NỘI DUNG ---
            # Format: [Pali] \n [Việt]
            md_output.append(f"[{pali}]\n[{viet}]\n")

    # --- LƯU FILE ---
    if md_output:
        # Nếu không tìm thấy tiêu đề trong bảng, ta dùng số trang làm tên
        file_path = os.path.join(OUTPUT_FOLDER, f"{filename_title}.md")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Source: {url}\n\n")
            f.write("\n".join(md_output))
        
        print(f"   ✅ Đã lưu: {filename_title}.md")
        return True # Tiếp tục trang sau
    else:
        print(f"   ⚠️ Trang {page_num} trống dữ liệu bảng.")
        return False # Dừng lại

async def main():
    async with AsyncWebCrawler(verbose=False) as crawler:
        print(f"🚀 Bắt đầu crawl Kinh Trung Bộ ({MAX_PAGES} trang dự kiến)...")
        
        for i in range(START_PAGE, MAX_PAGES + 1):
            success = await crawl_page(crawler, i)
            
            # Nếu gặp lỗi hoặc hết trang thì dừng vòng lặp
            if not success:
                print("🛑 Đã hết bài hoặc gặp lỗi. Dừng chương trình.")
                break
                
            # Nghỉ 1 giây để server không chặn
            await asyncio.sleep(1) 
            
        print("\n🎉 HOÀN TẤT! Kiểm tra thư mục 'Kinh_Trung_Bo_Data'")

if __name__ == "__main__":
    asyncio.run(main())