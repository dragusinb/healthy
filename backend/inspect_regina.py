import pdfplumber

FILES = [
    "data/raw/regina_maria/rezultat_33862887_2025.12.08 07.37.44.pdf",
    "data/raw/regina_maria/rezultat_16022867_2025.12.08 12.08.52.pdf"
]

def inspect(path):
    print(f"\n--- Inspecting {path} ---")
    try:
        with pdfplumber.open(path) as pdf:
            page = pdf.pages[0]
            print(f"Page Size: {page.width}x{page.height}")
            
            # Text dump
            text = page.extract_text()
            print("--- TEXT SAMPLE (First 500 chars) ---")
            print(text[:500])
            print("--- END TEXT SAMPLE ---")
            
            # Word dump (Looking for headers)
            words = page.extract_words()
            headers = [w for w in words if w['text'].lower() in ['analiza', 'nume', 'test', 'rezultat', 'valoare', 'um', 'u.m.', 'interval', 'referinta']]
            print(f"\nFound {len(headers)} potential header words:")
            for h in headers:
                print(f"  '{h['text']}' at X={h['x0']:.2f}, Y={h['top']:.2f}")

            # Looking for Homocisteina
            targets = [w for w in words if "homocis" in w['text'].lower()]
            if targets:
                print(f"\nFound Target 'Homocisteina' matches:")
                for t in targets:
                     print(f"  '{t['text']}' at X={t['x0']:.2f}, Y={t['top']:.2f}")
            else:
                print("\nNo 'Homocisteina' found on page 1.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    for f in FILES:
        inspect(f)
