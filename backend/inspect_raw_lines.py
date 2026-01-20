import pdfplumber
import glob
import os

def scan_files():
    files = glob.glob("data/raw/regina_maria/*.pdf")
    print(f"Scanning {len(files)} files...")
    
    for f in files:
        try:
            with pdfplumber.open(f) as pdf:
                for page in pdf.pages:
                    text = page.extract_text(layout=True)
                    if not text: continue
                    lines = text.split('\n')
                    for line in lines:
                        # minimal match
                        if "Hemoglobina" in line or "HOMOCISTEINA" in line:
                            # Print the line clearly with quotes to see whitespace
                            print(f"[{os.path.basename(f)}] -> '{line}'")
        except Exception as e:
            pass

if __name__ == "__main__":
    scan_files()
