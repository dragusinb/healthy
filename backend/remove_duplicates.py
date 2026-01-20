import re
from backend.database import SessionLocal
from backend.models import Document, TestResult

def remove_duplicates():
    session = SessionLocal()
    docs = session.query(Document).all()
    
    # Map report_id -> list of docs
    grouped = {}
    
    # Regex to extract the ID: rezultat_123456_...
    pattern = re.compile(r"rezultat_(\d+)_")
    
    for doc in docs:
        match = pattern.search(doc.filename)
        if match:
            report_id = match.group(1)
            if report_id not in grouped:
                grouped[report_id] = []
            grouped[report_id].append(doc)
        else:
            print(f"Skipping format check for: {doc.filename}")

    deleted_count = 0
    unique_count = 0
    
    for report_id, duplicates in grouped.items():
        unique_count += 1
        if len(duplicates) > 1:
            # Sort by ID descending (assuming higher ID = newer ingestion, or parse timestamp)
            # Actually, let's keep the one with the most results, or just the latest added.
            # Using ID is a safe proxy for "latest ingested" if timestamps are close.
            duplicates.sort(key=lambda x: x.id, reverse=True)
            
            to_keep = duplicates[0]
            to_delete = duplicates[1:]
            
            print(f"Report {report_id}: Keeping ID {to_keep.id}, deleting {len(to_delete)} duplicates.")
            
            for d in to_delete:
                # Delete associated results
                session.query(TestResult).filter(TestResult.document_id == d.id).delete()
                session.delete(d)
                deleted_count += 1
                
    session.commit()
    print(f"Cleanup Complete. Unique Reports: {unique_count}. Deleted Duplicates: {deleted_count}.")
    session.close()

if __name__ == "__main__":
    remove_duplicates()
