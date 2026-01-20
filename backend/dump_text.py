import pdfplumber
import os

def dump():
    path = r"c:\OldD\_Projects\Healthy\data\raw\regina_maria\rezultat_8245707_2025.12.08 07.39.06.pdf"
    with pdfplumber.open(path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
            
    with open("debug_text_dump.txt", "w", encoding="utf-8") as f:
        f.write(full_text)
    print("Dumped text to debug_text_dump.txt")

if __name__ == "__main__":
    dump()
