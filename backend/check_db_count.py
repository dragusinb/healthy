from backend.database import SessionLocal
from backend.models import TestResult, Document

session = SessionLocal()
count = session.query(TestResult).count()
docs = session.query(Document).count()
print(f"Total Documents: {docs}")
print(f"Total Test Results: {count}")

if count == 0:
    print("CRITICAL: Database is empty of results.")
else:
    # Print sample
    results = session.query(TestResult).limit(5).all()
    for r in results:
        print(f" - {r.test_name}: {r.value} [{r.unit}] (Doc ID: {r.document_id})")

session.close()
