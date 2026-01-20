from backend.database import SessionLocal
from backend.models import Document, TestResult, Provider

def verify():
    session = SessionLocal()
    
    docs = session.query(Document).all()
    print(f"Total Documents: {len(docs)}")
    
    real_docs = [d for d in docs if "rezultat_" in d.filename or "bilet_" in d.filename]
    mock_docs = [d for d in docs if "Analize_" in d.filename]
    
    print(f"Real Documents (Regina Maria): {len(real_docs)}")
    print(f"Mock Documents: {len(mock_docs)}")
    
    if real_docs:
        print(f"\n--- Checking for Empty Values ---")
        empty_count = 0
        total_count = 0
        
        for d in real_docs[:5]: # Check first 5
            print(f"Document: {d.filename}")
            results = session.query(TestResult).filter(TestResult.document_id == d.id).all()
            total_count += len(results)
            for r in results:
                is_empty = not r.value or r.value.strip() == ""
                if is_empty:
                    empty_count += 1
                    print(f"  [EMPTY] Name:'{r.test_name}' Unit:'{r.unit}' Ref:'{r.reference_range}'")
                # else:
                #    print(f"  [OK] Name:'{r.test_name}' Val:'{r.value}'")
        
        print(f"\nSummary: Found {empty_count} empty values out of {total_count} checked results.")
            
    session.close()

if __name__ == "__main__":
    verify()
