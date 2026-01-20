from backend.processors.universal import UniversalTableParser
from backend.processors.registry import get_parser_config

def test_parser():
    config = get_parser_config("synevo")
    # UniversalTableParser takes (provider_name, config)
    parser = UniversalTableParser("synevo", config)
    
    files = [
        "data/raw/synevo/31033112056.pdf", # Qualitative (Antigen)
        "data/raw/synevo/31031681616.pdf"  # Address Issue
    ]
    
    for file_path in files:
        print(f"\n========================================")
        print(f"Testing {file_path}")
        print(f"========================================")
        
        try:
            result = parser.parse(file_path)
            if "error" in result:
                print(f"ERROR: {result['error']}")
                continue
                
            print(f"Provider: {result['provider']}")
            print(f"Date: {result['collection_date']}")
            print(f"Results Found: {len(result['results'])}")
            print("-" * 40)
            
            for r in result['results']:
                # Print clean name and raw/clean inputs for verification
                print(f"Test: {r['test_name']}")
                print(f"  Value: {r['value']} [{r['unit']}]")
                print(f"  Ref:   {r['reference_range']}")
                print(f"  Flag:  {r['flags']}")
                print(f"  Cat:   {r['category']}")
                print("-" * 20)
                
        except Exception as e:
             # Print full traceback for clearer debugging of Logic Errors
             import traceback
             traceback.print_exc()
             print(f"CRASH: {e}")

if __name__ == "__main__":
    test_parser()
