from backend.database import SessionLocal
from backend.models import Document, TestResult
from sqlalchemy import func

def check():
    session = SessionLocal()
    docs = session.query(Document).all()
    print(f"Total Docs: {len(docs)}")
    
    empty_count = 0
    for d in docs:
        count = session.query(TestResult).filter_by(document_id=d.id).count()
        if count == 0:
            print(f"[EMPTY] {d.filename} (ID: {d.id})")
            empty_count += 1
            
    print(f"Total Empty Documents: {empty_count}")
    session.close()

if __name__ == "__main__":
    check()
