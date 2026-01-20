import pdfplumber

file_path = "data/raw/synevo/12002582294.pdf"

print(f"--- Extracting {file_path} ---")
with pdfplumber.open(file_path) as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"--- Page {i+1} ---")
        chars = page.chars
        print(f"Total Characters: {len(chars)}")
        if len(chars) > 0:
            print("First 10 chars:", chars[:10])
            # Print a sample of text by joining chars
            full_text = "".join([c['text'] for c in chars])
            print("Raw Char Text:\n", full_text[:500])
