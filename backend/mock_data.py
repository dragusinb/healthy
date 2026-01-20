import os
import sys
import datetime
import random
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import SessionLocal, engine, Base
from backend.models import Provider, Document, TestResult

def create_mock_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Create Providers
    providers = ["regina_maria", "synevo", "medlife"]
    db_providers = {}
    for p_name in providers:
        provider = db.query(Provider).filter(Provider.name == p_name).first()
        if not provider:
            provider = Provider(name=p_name, username="mock_user", encrypted_credentials="mock_password")
            db.add(provider)
            db.commit()
            db.refresh(provider)
        db_providers[p_name] = provider
    
    # 2. Mock Test Definitions
    lab_tests = [
        {"name": "Hemoglobina", "unit": "g/dL", "ref": "12.0 - 15.0"},
        {"name": "Leucocite", "unit": "mii/µL", "ref": "4.0 - 10.0"},
        {"name": "VSH", "unit": "mm/1h", "ref": "< 20"},
        {"name": "Glicemie", "unit": "mg/dL", "ref": "74 - 106"},
        {"name": "Colesterol Total", "unit": "mg/dL", "ref": "< 200"},
        {"name": "LDL Colesterol", "unit": "mg/dL", "ref": "< 100"},
        {"name": "Trigliceride", "unit": "mg/dL", "ref": "< 150"},
        {"name": "Fier Seric", "unit": "µg/dL", "ref": "37 - 145"},
        {"name": "Magneziu", "unit": "mg/dL", "ref": "1.6 - 2.55"},
        {"name": "Vitamina D", "unit": "ng/mL", "ref": "30 - 100"},
    ]

    # 3. Create Documents & Results over time
    start_date = datetime.datetime.now() - datetime.timedelta(days=730) # 2 years history
    
    for i in range(20): # 20 mock documents
        date = start_date + datetime.timedelta(days=random.randint(1, 700))
        provider_name = random.choice(providers)
        provider = db_providers[provider_name]
        
        doc = Document(
            provider_id=provider.id,
            filename=f"Analize_{date.strftime('%Y-%m-%d')}_{i}.pdf",
            file_path=f"/mock/path/to/Analize_{i}.pdf",
            file_type="PDF",
            document_date=date,
            category="Analize Laborator"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Add random test results to this doc
        num_tests = random.randint(3, 8)
        selected_tests = random.sample(lab_tests, num_tests)
        
        for test in selected_tests:
            # Generate value logic (mostly normal, some abnormal)
            is_abnormal = random.random() < 0.2
            
            # Simple parsing of ref range for mock generation (very basic)
            val = 0.0
            flag = "NORMAL"
            
            try:
                if "-" in test["ref"]:
                    low, high = map(float, test["ref"].replace("<", "").replace(">", "").split("-"))
                    mid = (low + high) / 2
                    if is_abnormal:
                        if random.random() < 0.5:
                            val = low - (low * 0.1)
                            flag = "LOW"
                        else:
                            val = high + (high * 0.1)
                            flag = "HIGH"
                    else:
                        val = random.uniform(low, high)
                elif "<" in test["ref"]:
                    high = float(test["ref"].replace("<", "").strip())
                    if is_abnormal:
                         val = high + 10
                         flag = "HIGH"
                    else:
                         val = random.uniform(high/2, high)
                else:
                    val = 50.0 # fallback
            except:
                val = 50.0
                
            result = TestResult(
                document_id=doc.id,
                test_name=test["name"],
                value=f"{val:.2f}",
                unit=test["unit"],
                reference_range=test["ref"],
                flags=flag
            )
            db.add(result)
        
        db.commit()

    print("Mock data generated successfully.")
    db.close()

if __name__ == "__main__":
    create_mock_data()
