from backend_v2.database import SessionLocal
from backend_v2.models import User, Document, TestResult

def inspect_data():
    db = SessionLocal()
    user = db.query(User).filter(User.email == "dragusinb@gmail.com").first()
    
    if not user:
        print("User not found!")
        return

    print(f"--- Documents for {user.email} ---")
    docs = db.query(Document).filter(Document.user_id == user.id).all()
    for d in docs:
        print(f"ID: {d.id} | Date: {d.document_date} | Provider: {d.provider} | File: {d.filename} | Processed: {d.is_processed}")
        
        results = db.query(TestResult).filter(TestResult.document_id == d.id).all()
        print(f"    -> Contains {len(results)} biomarkers.")
        for r in results[:3]: # Show first 3 only
             print(f"       - {r.test_name}: {r.value} ({r.flags})")
        if len(results) > 3:
             print("       ...")

if __name__ == "__main__":
    inspect_data()
