import pdfplumber
import glob
import os

def scan_files():
    files = glob.glob("data/raw/regina_maria/*.pdf")
    # print(f"Scanning {len(files)} files...")
    
    for f in files:
        try:
            with pdfplumber.open(f) as pdf:
                for page in pdf.pages:
                    text = page.extract_text(layout=True)
                    if not text: continue
                    lines = text.split('\n')
                    for line in lines:
                        if "UREE SERICA" in line:
                            # Print with quotes to see spacing
                            print(f"[{os.path.basename(f)}]\n'{line}'")
                            # Also print the header indices if possible? 
                            # Hard without running the full parser logic, but visual inspection is paramount.
        except Exception as e:
            pass

if __name__ == "__main__":
    scan_files()
