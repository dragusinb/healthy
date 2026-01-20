from backend.processors.ai_parser import AIParser
import os
import sys

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Mock text from a Regina report
SAMPLE_TEXT = """
Regina Maria
Laborator Central
Pacient: Popescu Ion
CNP: 1800101123456
Data: 2024-01-01

Rezultate Analize
Denumire Test      Rezultat     UM       Interval
Hemoglobina        14.5         g/dL     13.0 - 17.0
VSH                12           mm/1h    < 15
Colesterol Total   240          mg/dL    < 200
Comentariu: Proba usor hemolizata.
"""

def run():
    # Key from user request
    USER_KEY = os.getenv("OPENAI_API_KEY")
    
    print("--- Testing AI Parser (OpenAI GPT-4o) ---")
    
    parser = AIParser(api_key=USER_KEY)
    print("Sending Request to OpenAI...")
    
    res = parser.parse_text(SAMPLE_TEXT)
    
    if "error" in res:
        print(f"API Error: {res['error']}")
    else:
        print(f"Success! Extracted {len(res['results'])} items:")
        import json
        print(json.dumps(res, indent=2))

if __name__ == "__main__":
    run()
