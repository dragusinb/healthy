import pdfplumber

def inspect_coords():
    # Target the problematic qualitative file
    path = "data/raw/synevo/31033112056.pdf"
    
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        words = page.extract_words()
        
        print(f"--- Page 1 (Width: {page.width}) ---")
        
        # Look for headers
        headers = ["Denumire", "Rezultat", "UM", "Interval", "referinta"]
        found_headers = []
        
        for w in words:
            if any(h in w["text"] for h in headers) or "Streptococ" in w["text"] or "Negativ" in w["text"]:
                print(f"Word: '{w['text']}' | x0: {w['x0']:.2f} | x1: {w['x1']:.2f} | top: {w['top']:.2f}")
                
if __name__ == "__main__":
    inspect_coords()
