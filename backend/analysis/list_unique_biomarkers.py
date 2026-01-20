from backend.database import SessionLocal
from backend.models import TestResult
from sqlalchemy import func

def list_unique_tests():
    session = SessionLocal()
    # Query distinct names with their occurrence count
    results = session.query(
        TestResult.test_name, 
        func.count(TestResult.test_name).label('count')
    ).group_by(TestResult.test_name).order_by(func.count(TestResult.test_name).desc()).all()
    
    print(f"--- Founds {len(results)} unique test names ---")
    
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    for name, count in results:
        print(f"[{count}] {name}")
    
    session.close()

if __name__ == "__main__":
    list_unique_tests()
