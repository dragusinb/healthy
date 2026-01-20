import pdfplumber

def inspect():
    path = "data/raw/synevo/31033112056.pdf"
    with pdfplumber.open(path) as pdf:
        words = pdf.pages[0].extract_words()
        print(f"Total Words: {len(words)}")
        for w in words[:100]: # First 100 words
            print(f"Word: '{w['text']}'")
            
        print("--- Searching for Denumire ---")
        for w in words:
            if "numire" in w['text'].lower() or "rezultat" in w['text'].lower():
                print(f"MATCH: '{w['text']}' at {w['top']}")

if __name__ == "__main__":
    inspect()
