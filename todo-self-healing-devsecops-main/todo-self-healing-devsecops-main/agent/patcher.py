import os


def overwrite_file(file_path, new_code):
    """Write the fixed code back to the file, creating parent dirs if needed."""
    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_code)
    print(f"[patcher] Wrote fix to: {file_path}")
