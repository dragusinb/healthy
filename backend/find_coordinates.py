import pdfplumber

def run():
    path = "data/raw/synevo/31033112056.pdf"
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        words = page.extract_words()
        
        print(f"DEBUG: Processing {len(words)} words.")
        for w in words:
            txt = w['text'].lower()
            if "rezultat" in txt or "result" in txt or "negativ" in txt:
                print(f"MATCH: '{w['text']}' X0={w['x0']:.2f} X1={w['x1']:.2f} Top={w['top']:.2f}")

if __name__ == "__main__":
    run()
