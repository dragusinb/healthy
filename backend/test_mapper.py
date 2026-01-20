from backend.analysis.mapper import BiomarkerMapper
import sys
sys.stdout.reconfigure(encoding='utf-8')

TEST_CASES = [
    "VSH",
    "Viteza de sedimentare a hematiilor",
    "Hemoglobina",
    "Hb",
    "TGP",
    "Alaninaminotransferaza (ALT/TGP)",
    "Colesterol LDL",
    "Colesterol LDL calculat",
    "Unknown Test 123"
]

def run():
    print("--- Testing Biomarker Mapper ---")
    for raw in TEST_CASES:
        std = BiomarkerMapper.map_to_standard(raw)
        print(f"'{raw}' -> '{std}'")

if __name__ == "__main__":
    run()
