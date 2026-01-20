from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import TestResult
from backend.data.biomarkers import get_biomarker_info

def migrate_categories():
    db = SessionLocal()
    try:
        results = db.query(TestResult).all()
        updated_count = 0
        
        print(f"Checking {len(results)} results...")
        
        for r in results:
            info = get_biomarker_info(r.test_name)
            if info and "category" in info:
                new_cat = info["category"]
                if r.category != new_cat:
                    print(f"Updating {r.test_name}: {r.category} -> {new_cat}")
                    r.category = new_cat
                    updated_count += 1
        
        if updated_count > 0:
            db.commit()
            print(f"Successfully updated {updated_count} records.")
        else:
            print("No records needed updating.")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_categories()
