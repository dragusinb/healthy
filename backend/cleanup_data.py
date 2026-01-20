from backend.database import SessionLocal
from backend.models import Document, TestResult

def cleanup_mock_data():
    session = SessionLocal()
    
    # Mock data filenames start with "Analize_" based on mock_data.py
    mock_docs = session.query(Document).filter(Document.filename.like("Analize_%")).all()
    
    print(f"Found {len(mock_docs)} mock documents to delete.")
    
    count = 0
    for doc in mock_docs:
        # Cascade delete results (if not configured in DB, do it manually)
        session.query(TestResult).filter(TestResult.document_id == doc.id).delete()
        session.delete(doc)
        count += 1
        
    session.commit()
    print(f"Successfully deleted {count} mock documents. Only real data remains.")
    session.close()

if __name__ == "__main__":
    cleanup_mock_data()
