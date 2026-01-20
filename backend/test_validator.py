from backend.analysis.validator import BiomarkerValidator
from backend.database import SessionLocal, Base, engine

# Ensure tables exist
Base.metadata.create_all(bind=engine)

def test_validator():
    validator = BiomarkerValidator()
    
    test_cases = [
        "Hemoglobina",       # Should be Valid (Exact/Fuzzy)
        "Glucoza serica",    # Should be Valid
        "Str. Lunga nr. 4",  # Should be BLOCKED
        "Bucuresti Sector 3", # Should be BLOCKED
        "Borrelia burgdorferi", # Should be Valid (if in KB) or Pending
        "Random Noise Here",  # Should be PENDING
    ]
    
    print("--- Testing Validator ---")
    for case in test_cases:
        result = validator.validate(case)
        print(f"'{case}' -> {result['is_valid']} ({result['reason']}) [{result.get('standardized_name')}]")
        
    validator.close()

if __name__ == "__main__":
    test_validator()
