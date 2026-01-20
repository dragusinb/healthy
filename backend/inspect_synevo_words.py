import pdfplumber
import json

file_path = "data/raw/synevo/12002582294.pdf"

print(f"--- Extracting Words from {file_path} ---")
with pdfplumber.open(file_path) as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"--- Page {i+1} ---")
        words = page.extract_words()
        
        # Group words by Y-coordinate (tolerance 3px)
        lines = []
        current_line = []
        last_top = -100
        
        # Sort by vertical position first, then horizontal
        words.sort(key=lambda w: (w['top'], w['x0']))
        
        for w in words:
            if abs(w['top'] - last_top) > 3:
                # New line
                if current_line:
                    lines.append(current_line)
                current_line = [w]
                last_top = w['top']
            else:
                current_line.append(w)
        if current_line: lines.append(current_line)
        
        # Print reconstructed lines
        print(f"--- Reconstructed {len(lines)} lines")
        for line_words in lines:
            # Join words with space (simple) or calculate spacing
            text_line = " ".join([w['text'] for w in line_words])
            print(f"LINE: {text_line}")
