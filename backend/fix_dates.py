from backend.database import SessionLocal
from backend.models import Document
import datetime

def fix_dates():
    session = SessionLocal()
    docs = session.query(Document).filter(Document.document_date == None).all()
    print(f"Found {len(docs)} documents with NULL date.")
    
    count = 0
    for d in docs:
        # Fallback to upload_date or now
        new_date = d.upload_date or datetime.datetime.now()
        d.document_date = new_date
        count += 1
        
    session.commit()
    print(f"Fixed {count} documents.")
    session.close()

if __name__ == "__main__":
    fix_dates()
