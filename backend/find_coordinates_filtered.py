import pdfplumber

def run():
    path = "data/raw/synevo/31033112056.pdf"
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        words = page.extract_words()
        
        for w in words:
            txt = w['text'].lower()
            if "rezultat" in txt or "result" in txt or "negativ" in txt:
                print(f"'{w['text']}' X={w['x0']:.1f} Y={w['top']:.1f}")

if __name__ == "__main__":
    run()
