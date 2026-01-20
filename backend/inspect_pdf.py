import pdfplumber
import os

import sys

# Path to a sample file
file_path = "data/raw/regina_maria/rezultat_8588165_2025.12.08 12.09.17.pdf"

if len(sys.argv) > 1:
    file_path = sys.argv[1]

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    files = os.listdir("data/raw/regina_maria")
    pdf_files = [f for f in files if f.endswith(".pdf")]
    if pdf_files:
        file_path = os.path.join("data/raw/regina_maria", pdf_files[0])
        print(f"Falling back to: {file_path}")
    else:
        print("No PDF found")
        exit()

print(f"Inspecting: {file_path}")

text = ""
with pdfplumber.open(file_path) as pdf:
    for page in pdf.pages:
        # Try extract_text with layout=True
        text += page.extract_text(layout=True) + "\n\n"
        # Also try table extraction
        tables = page.extract_tables()
        text += f"\n--- TABLES found on page {page.page_number} ---\n"
        for table in tables:
            for row in table:
                text += str(row) + "\n"
        text += "\n----------------------------------------\n"

# Write to file
with open("data/sample_text_plumber.txt", "w", encoding="utf-8") as f:
    f.write(text)

print("Text written to data/sample_text_plumber.txt")
