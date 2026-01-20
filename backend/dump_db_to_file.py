from backend.database import SessionLocal
from backend.models import TestResult

s = SessionLocal()
with open("db_dump.txt", "w", encoding="utf-8") as f:
    results = s.query(TestResult).all()
    f.write(f"Total: {len(results)}\n")
    for r in results:
        f.write(f"[{r.id}] Name='{r.test_name}' Value='{r.value}'\n")
