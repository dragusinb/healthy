from backend_v2.database import SessionLocal
from backend_v2.models import User, Document, TestResult
import datetime
import os

def seed_demo():
    db = SessionLocal()
    user = db.query(User).filter(User.email == "dragusinb@gmail.com").first()
    
    if not user:
        print("User not found!")
        return

    # 1. Create Demo Document
    # We'll just point to a fake path, frontend doesn't download it yet anyway
    demo_doc = Document(
        user_id=user.id,
        filename="Analize_Synevo_Demo.pdf",
        file_path="data/uploads/demo.pdf",
        provider="Synevo",
        document_date=datetime.datetime(2023, 10, 15),
        upload_date=datetime.datetime.now(),
        is_processed=True
    )
    db.add(demo_doc)
    db.commit()
    db.refresh(demo_doc)
    
    # 2. Add Test Results
    results = [
        {"name": "Hemoglobina", "val": "14.2", "num": 14.2, "unit": "g/dL", "ref": "12 - 16", "flag": "NORMAL"},
        {"name": "Hematocrit", "val": "42.0", "num": 42.0, "unit": "%", "ref": "36 - 46", "flag": "NORMAL"},
        {"name": "Leucocite", "val": "6.5", "num": 6.5, "unit": "mii/µL", "ref": "4.0 - 10.0", "flag": "NORMAL"},
        {"name": "VSH", "val": "18", "num": 18.0, "unit": "mm/h", "ref": "< 20", "flag": "NORMAL"},
        {"name": "Colesterol Total", "val": "235", "num": 235.0, "unit": "mg/dL", "ref": "< 200", "flag": "HIGH"},
        {"name": "Trigliceride", "val": "150", "num": 150.0, "unit": "mg/dL", "ref": "< 150", "flag": "NORMAL"},
        {"name": "Glucoza Serica", "val": "98", "num": 98.0, "unit": "mg/dL", "ref": "74 - 106", "flag": "NORMAL"},
        {"name": "TGP", "val": "45", "num": 45.0, "unit": "U/L", "ref": "< 41", "flag": "HIGH"},
    ]
    
    for r in results:
        tr = TestResult(
            document_id=demo_doc.id,
            test_name=r["name"],
            value=r["val"],
            numeric_value=r["num"],
            unit=r["unit"],
            reference_range=r["ref"],
            flags=r["flag"]
        )
        db.add(tr)
        
    # Add older history for Evolution Graph testing
    demo_doc_old = Document(
        user_id=user.id,
        filename="Analize_Synevo_Old.pdf",
        file_path="data/uploads/demo_old.pdf",
        provider="Synevo",
        document_date=datetime.datetime(2023, 1, 10),
        upload_date=datetime.datetime.now(),
        is_processed=True
    )
    db.add(demo_doc_old)
    db.commit()
    db.refresh(demo_doc_old)

    old_results = [
        {"name": "Hemoglobina", "val": "13.8", "num": 13.8, "unit": "g/dL", "ref": "12 - 16", "flag": "NORMAL"},
        {"name": "Colesterol Total", "val": "210", "num": 210.0, "unit": "mg/dL", "ref": "< 200", "flag": "HIGH"},
        {"name": "TGP", "val": "35", "num": 35.0, "unit": "U/L", "ref": "< 41", "flag": "NORMAL"},
    ]
    for r in old_results:
        tr = TestResult(
            document_id=demo_doc_old.id,
            test_name=r["name"],
            value=r["val"],
            numeric_value=r["num"],
            unit=r["unit"],
            reference_range=r["ref"],
            flags=r["flag"]
        )
        db.add(tr)

    db.commit()
    print("Demo data seeded successfully!")

if __name__ == "__main__":
    seed_demo()
