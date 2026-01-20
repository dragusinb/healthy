from backend.processors.regina import ReginaTableParser
import os

FILES = [
    # Homocisteina file
    "data/raw/regina_maria/rezultat_33862887_2025.12.08 07.37.44.pdf",
    # "LOT of biomarkers" file
    "data/raw/regina_maria/rezultat_16022867_2025.12.08 12.08.52.pdf"
]

import sys
sys.stdout.reconfigure(encoding='utf-8')

def run():
    parser = ReginaTableParser()
    
    for f in FILES:
        if not os.path.exists(f):
            print(f"File not found: {f}")
            continue
            
        try:
            print(f"\n--- Parsing {os.path.basename(f)} ---")
            res = parser.parse(f)
            results = res.get("results", [])
            
            print(f"Extracted {len(results)} results.")
            for r in results:
                print(f"  {r['test_name']} = {r['value']} (Unit: {r['unit']}) [Flags: {r['flags']}]")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"CRASH: {e}")

if __name__ == "__main__":
    run()
