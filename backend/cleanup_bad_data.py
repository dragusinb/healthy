from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import TestResult, Document

def cleanup_and_inspect():
    db = SessionLocal()
    try:
        # 1. Cleanup Bad Data
        bad_patterns = ["%Constantin%", "%Receptie%", "%Sector%"]
        total_deleted = 0
        
        for pat in bad_patterns:
            rows = db.query(TestResult).filter(TestResult.test_name.ilike(pat)).all()
            if rows:
                print(f"Deleting {len(rows)} rows matching '{pat}':")
                for r in rows:
                    print(f"  - {r.test_name} (Doc: {r.document_id})")
                    db.delete(r)
                total_deleted += len(rows)
        
        db.commit()
        print(f"Total deleted: {total_deleted}")

        # 2. Inspect Homocisteina
        print("\n--- Inspecting Homocisteina ---")
        homo_results = db.query(TestResult).join(Document).filter(TestResult.test_name.ilike("%Homocisteina%")).all()
        for r in homo_results:
            print(f"ID: {r.id} | Val: {r.value} | Date: {r.document.document_date} | Flags: {r.flags}")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_and_inspect()
