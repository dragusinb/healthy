import pdfplumber

file_path = "data/raw/synevo/12002582294.pdf"

print(f"--- Dumping Words ---")
with pdfplumber.open(file_path) as pdf:
    with open("all_words.txt", "w", encoding="utf-8") as f:
        for page in pdf.pages:
            words = page.extract_words()
            for w in words:
                f.write(w['text'] + "\n")
print("Done.")
