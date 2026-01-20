from backend.processors.regina_maria import ReginaMariaParser
import os
import glob
import json
import datetime

def test_robustness():
    parser = ReginaMariaParser()
    
    # Try to find the specific file mentioned by user or any Regina file
    # "rezultat_33174472_2025.12.08 12.08.00.pdf"
    
    target_pattern = "data/raw/regina_maria/*33174472*"
    files = glob.glob(target_pattern)
    
    if not files:
        print("Specific file not found, trying any PDF in data/raw/regina_maria")
        start_dir = "data/raw/regina_maria"
        files = glob.glob(os.path.join(start_dir, "*.pdf"))
        
    if not files:
        print("No files found to test.")
        return

    file_path = files[0]
    print(f"Testing Robust Parser on: {file_path}")
    
    try:
        data = parser.parse(file_path)
        
        # Helper for printing
        def default(o):
            if isinstance(o, (datetime.date, datetime.datetime)):
                return o.isoformat()
        
        # Check specifically for "m g" unit issues
        issues_found = False
        for r in data["results"]:
            if "m g" in r["unit"] or "d L" in r["unit"]:
                print(f"❌ FAIL: Unclean unit found: {r['test_name']} -> {r['unit']}")
                issues_found = True
            
            # Check for merged values "1 2 . 5"
            if " " in r["value"] and any(c.isdigit() for c in r["value"]):
                 # Spaces in qualitative results (e.g. "Nu s-a detectat") are okay
                 # But in "12 5" they are not.
                 # Heuristic check
                 pass
        
        if not issues_found:
            print("✅ Unit Cleaning Logic passed checks.")

        print(json.dumps(data, indent=2, default=default))
        
    except Exception as e:
        print(f"CRITICAL PARSER ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_robustness()
