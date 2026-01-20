import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.processors.regina_maria import ReginaMariaParser
import glob

def verify():
    parser = ReginaMariaParser()
    # Find a file with UREE SERICA
    files = glob.glob("data/raw/regina_maria/*.pdf")
    found_count = 0
    for f in files:
        if found_count > 3: break
        try:
            data = parser.parse(f)
            for res in data["results"]:
                if "UREE SERICA" in res["test_name"].upper():
                    print(f"File: {os.path.basename(f)}")
                    print(f"  Name: {res['test_name']}")
                    print(f"  Value: '{res['value']}'")
                    print(f"  Unit: '{res['unit']}'")
                    print(f"  Range: '{res['reference_range']}'")
                    found_count += 1
        except Exception as e:
            pass

if __name__ == "__main__":
    verify()
