from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import TestResult, Document
import collections

def inspect_duplicates():
    db = SessionLocal()
    try:
        # Check specifically for Homocisteina
        results = db.query(TestResult).join(Document).filter(TestResult.test_name.ilike("%Homocisteina%")).all()
        
        print(f"Found {len(results)} results for Homocisteina:")
        for r in results:
            print(f"ID: {r.id}, Value: {r.value}, Date: {r.document.document_date}, DocID: {r.document_id}, DocName: {r.document.filename}")
            
        # Check for exact duplicates (Same Test, Same Value, Same Date) across ALL data
        print("\n--- Checking for Global Duplicates ---")
        all_results = db.query(TestResult).join(Document).all()
        
        # Key = (test_name, value, date)
        seen = collections.defaultdict(list)
        for r in all_results:
            key = (r.test_name, r.value, r.document.document_date)
            seen[key].append(r)
            
        dup_count = 0
        for key, items in seen.items():
            if len(items) > 1:
                dup_count += 1
                if dup_count < 5: # Print first few
                    print(f"Duplicate Group: {key}")
                    for item in items:
                        print(f"  - ID: {item.id}, Doc: {item.document.filename}")
        
        print(f"\nTotal Duplicated Groups: {dup_count}")

    finally:
        db.close()

if __name__ == "__main__":
    inspect_duplicates()
