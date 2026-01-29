import os
import glob

DATA_FOLDER = "data/Truong_Bo_Kinh_Final"
OUTPUT_FILE = "data/Truong_Bo_Kinh_Final/list.md"

def extract_headers():
    md_files = sorted(glob.glob(os.path.join(DATA_FOLDER, "*.md")))
    results = []

    for i, file_path in enumerate(md_files, 1):
        file_name = os.path.basename(file_path)
        if file_name == "list.md":
            continue
            
        h1 = "N/A"
        h2 = "N/A"
        h3 = "N/A"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("# ") and h1 == "N/A":
                    h1 = stripped[2:].strip()
                elif stripped.startswith("## ") and h2 == "N/A":
                    h2 = stripped[3:].strip()
                elif stripped.startswith("### ") and h3 == "N/A":
                    h3 = stripped[4:].strip()
                
                # If we have all three, we can move to the next file
                if h1 != "N/A" and h2 != "N/A" and h3 != "N/A":
                    break

        results.append(f"{i}. {file_name} | {h1} | {h2} | {h3}")

    if results:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("# List of Headers in Truong Bo Kinh\n\n")
            f.write("\n".join(results))
            f.write("\n")
        print(f"✅ Extracted info for {len(results)} files to {OUTPUT_FILE}")
    else:
        print("⚠️ No headers found.")

if __name__ == "__main__":
    extract_headers()
