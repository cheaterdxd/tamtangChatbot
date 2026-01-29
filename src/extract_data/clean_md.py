import os
import glob

# --- CẤU HÌNH ---
# Đường dẫn thư mục chứa file md bạn muốn kiểm tra
DATA_FOLDER = "data/Truong_Bo_Kinh_Final"

def scan_files():
    # Lấy danh sách file
    md_files = glob.glob(os.path.join(DATA_FOLDER, "*.md"))

    if not md_files:
        print(f"❌ Not found any .md file in folder: {DATA_FOLDER}")
        return

    print(f"🔍 Scanning {len(md_files)} files in '{DATA_FOLDER}'...\n")
    print("-" * 80)
    print(f"{'FILE NAME':<40} | {'STATUS':<30}")
    print("-" * 80)

    count_error = 0
    count_ok = 0

    for file_path in md_files:
        file_name = os.path.basename(file_path)

        has_h1 = False
        has_h2 = False
        has_h3 = False
        has_bad_h1 = False
        has_bad_h2 = False
        has_bad_h3 = False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped = line.strip()

                    # Check H1
                    if stripped.startswith("# "):
                        has_h1 = True
                    elif stripped.startswith("#") and not stripped.startswith("##"):
                        if len(stripped) > 1 and stripped[1] != " ":
                            has_bad_h1 = True

                    # Check H2
                    if stripped.startswith("## "):
                        has_h2 = True
                    elif stripped.startswith("##") and not stripped.startswith("###"):
                        if len(stripped) > 2 and stripped[2] != " ":
                            has_bad_h2 = True

                    # Check H3
                    if stripped.startswith("### "):
                        has_h3 = True
                    elif stripped.startswith("###") and not stripped.startswith("####"):
                        if len(stripped) > 3 and stripped[3] != " ":
                            has_bad_h3 = True

            # Determine Status
            status_list = []
            file_error = False

            # H1 status
            if has_h1: status_list.append("H1:✅")
            elif has_bad_h1: 
                status_list.append("H1:⚠️")
                file_error = True
            else: 
                status_list.append("H1:❌")
                file_error = True

            # H2 status
            if has_h2: status_list.append("H2:✅")
            elif has_bad_h2: 
                status_list.append("H2:⚠️")
                file_error = True
            else: 
                status_list.append("H2:❌")
                file_error = True

            # H3 status
            if has_h3: status_list.append("H3:✅")
            elif has_bad_h3: 
                status_list.append("H3:⚠️")
                file_error = True
            else: 
                status_list.append("H3:❌")
                file_error = True

            status_str = " ".join(status_list)

            if not file_error:
                # print(f"{file_name:<40} | {status_str}") # Uncomment to see all OK files
                count_ok += 1
            else:
                print(f"{file_name:<40} | {status_str}")
                count_error += 1

        except Exception as e:
            print(f"{file_name:<40} | ❌ Error reading file: {e}")

    print("-" * 80)
    print(f"Result: {count_ok} perfect/ {count_error} need check.")
    if count_error > 0:
        print("\n💡 Legend: ✅ OK | ❌ Found no header | ⚠️ Missing space after #")
        print("   LangChain requires a space after '#' to identify headers correctly.")


def add_header(new_line, n=0):
    """
    Inserts a new line at the n-th position (0-indexed) of all .md files in DATA_FOLDER.
    """
    md_files = glob.glob(os.path.join(DATA_FOLDER, "*.md"))

    if not md_files:
        print(f"❌ No .md files found in {DATA_FOLDER}")
        return

    for file_path in md_files:
        file_name = os.path.basename(file_path)

        try:
            # Read existing content
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Insert the new line
            # Ensure the new line ends with a newline character
            if not new_line.endswith('\n'):
                new_line += '\n'

            lines.insert(n, new_line)

            # Write back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            print(f"✅ Added line to {file_name} at position {n}")
        except Exception as e:
            print(f"❌ Error processing {file_name}: {e}")



if __name__ == "__main__":
    # Scan files to check headers
    scan_files()