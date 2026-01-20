from backend.database import SessionLocal
from backend.models import TestResult

s = SessionLocal()
count = s.query(TestResult).count()
print(f"TOTAL_RESULTS: {count}")
