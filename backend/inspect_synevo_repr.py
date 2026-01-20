import pdfplumber

def inspect():
    path = "data/raw/synevo/31033112056.pdf"
    with pdfplumber.open(path) as pdf:
        text = pdf.pages[0].extract_text()
        lines = text.split('\n')
        with open("debug_repr.txt", "w", encoding="utf-8") as f:
            for line in lines:
                if "Antigen" in line:
                    f.write(f"LINE: {line}\n")
                    f.write(f"REPR: {repr(line)}\n")

if __name__ == "__main__":
    inspect()
