import pdfplumber

def run():
    path = "data/raw/regina_maria/rezultat_16022867_2025.12.08 12.08.52.pdf"
    try:
        with pdfplumber.open(path) as pdf:
            words = pdf.pages[0].extract_words()
            print(f"Total Words: {len(words)}")
            for w in words:
                txt = w['text']
                if txt.lower() in ["denumire", "rezultate", "interval", "referinta", "homocisteina", "biologic", "um", "u.m."]:
                    print(f"KEY: '{txt}' X={w['x0']:.2f} Top={w['top']:.2f}")
                
            # Also print first 5 homocisteina context words (if any)
            # Actually just print everything logic-like

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
