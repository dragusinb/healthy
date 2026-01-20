from backend.database import SessionLocal
from backend.models import TestResult

s = SessionLocal()
results = s.query(TestResult).all()
print(f"Total: {len(results)}")
for r in results:
    input(f"[{r.id}] {r.test_name} = {r.value}") # Input forces flush? No just print.
    print(f"[{r.id}] {r.test_name} : {r.value}")
