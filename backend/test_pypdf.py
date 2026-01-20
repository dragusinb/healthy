from pypdf import PdfReader

file_path = "data/raw/synevo/12002582294.pdf"

print(f"--- Extracting {file_path} with pypdf ---")
try:
    reader = PdfReader(file_path)
    for i, page in enumerate(reader.pages):
        print(f"--- Page {i+1} ---")
        text = page.extract_text()
        print(text)
except Exception as e:
    print(f"Error: {e}")
