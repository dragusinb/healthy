from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import SessionLocal
from backend.models import TestResult, Document

def cleanup_duplicates():
    db = SessionLocal()
    try:
        print("Scanning for duplicates...")
        # Find duplicates grouping by (document_id, test_name, value)
        # We want to keep the one with the lowest ID (first imported) or highest? 
        # Usually redundant imports happen later, so maybe delete higher IDs.
        
        duplicates = db.query(
            TestResult.document_id,
            TestResult.test_name,
            TestResult.value,
            func.count(TestResult.id)
        ).group_by(
            TestResult.document_id,
            TestResult.test_name,
            TestResult.value
        ).having(func.count(TestResult.id) > 1).all()
        
        total_deleted = 0
        
        for doc_id, name, val, count in duplicates:
            # Get IDs
            rows = db.query(TestResult).filter(
                TestResult.document_id == doc_id,
                TestResult.test_name == name,
                TestResult.value == val
            ).order_by(TestResult.id.asc()).all()
            
            # Keep first, delete rest
            to_delete = rows[1:]
            for r in to_delete:
                db.delete(r)
                total_deleted += 1
                
        db.commit()
        print(f"Cleanup complete. Removed {total_deleted} duplicate entries.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_duplicates()
