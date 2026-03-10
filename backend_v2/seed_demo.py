"""
Seed script to create demo accounts for client presentation.
Run on the server: cd /opt/healthy/backend_v2 && venv/bin/python seed_demo.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import json
import uuid
from dotenv import load_dotenv

# Load .env file (same directory as the script, i.e. backend_v2/.env)
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Import app models
from models import (
    User, LinkedAccount, Document, TestResult, HealthReport,
    FamilyGroup, FamilyMember, Subscription, UsageTracker,
    NotificationPreference, FoodPreference, Medication
)

# Database connection - same as the app
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://healthy_user:healthy_pass_2024@localhost/healthy_db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============================================================
# CONFIG
# ============================================================
MOTHER_EMAIL = "elena.popescu@demo.analize.online"
MOTHER_PASSWORD = "DemoPass123!"
SON_EMAIL = "andrei.popescu@demo.analize.online"
SON_PASSWORD = "DemoPass123!"

# ============================================================
# CLEANUP - Remove existing demo accounts
# ============================================================
def cleanup():
    for email in [MOTHER_EMAIL, SON_EMAIL]:
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Delete family memberships
            db.query(FamilyMember).filter(FamilyMember.user_id == user.id).delete()
            db.query(FamilyGroup).filter(FamilyGroup.owner_id == user.id).delete()
            db.query(FoodPreference).filter(FoodPreference.user_id == user.id).delete()
            db.query(Medication).filter(Medication.user_id == user.id).delete()
            db.query(NotificationPreference).filter(NotificationPreference.user_id == user.id).delete()
            db.query(Subscription).filter(Subscription.user_id == user.id).delete()
            db.query(UsageTracker).filter(UsageTracker.user_id == user.id).delete()
            db.query(HealthReport).filter(HealthReport.user_id == user.id).delete()
            # Delete test results via documents
            docs = db.query(Document).filter(Document.user_id == user.id).all()
            for doc in docs:
                db.query(TestResult).filter(TestResult.document_id == doc.id).delete()
            db.query(Document).filter(Document.user_id == user.id).delete()
            db.query(LinkedAccount).filter(LinkedAccount.user_id == user.id).delete()
            db.delete(user)
    db.commit()
    print("Cleanup done.")

# ============================================================
# CREATE USERS
# ============================================================
def create_users():
    now = datetime.utcnow()

    mother = User(
        email=MOTHER_EMAIL,
        hashed_password=pwd_context.hash(MOTHER_PASSWORD),
        is_active=True,
        is_admin=False,
        language="ro",
        email_verified=True,
        created_at=now - timedelta(days=90),
        terms_accepted_at=now - timedelta(days=90),
        privacy_accepted_at=now - timedelta(days=90),
        terms_version="1.0",
        privacy_version="1.0",
        # Profile (plaintext for demo - no vault needed)
        full_name="Elena Popescu",
        date_of_birth=datetime(1985, 3, 15),
        gender="female",
        height_cm=165.0,
        weight_kg=68.0,
        blood_type="A+",
        allergies=json.dumps(["Polen", "Praf"]),
        chronic_conditions=json.dumps(["Miopie", "Gonartroza genunchi drept"]),
        current_medications=json.dumps(["Ibuprofen la nevoie", "Ocuvit Plus"]),
        smoking_status="never",
        alcohol_consumption="occasional",
        physical_activity="light",
    )

    son = User(
        email=SON_EMAIL,
        hashed_password=pwd_context.hash(SON_PASSWORD),
        is_active=True,
        is_admin=False,
        language="ro",
        email_verified=True,
        created_at=now - timedelta(days=90),
        terms_accepted_at=now - timedelta(days=90),
        privacy_accepted_at=now - timedelta(days=90),
        terms_version="1.0",
        privacy_version="1.0",
        full_name="Andrei Popescu",
        date_of_birth=datetime(2012, 7, 22),
        gender="male",
        height_cm=152.0,
        weight_kg=42.0,
        blood_type="A+",
        allergies=json.dumps(["Acarieni", "Ambrozie", "Lactoza"]),
        chronic_conditions=json.dumps(["Scolioza toracica", "Rinita alergica"]),
        current_medications=json.dumps(["Aerius 5mg", "Vitamina D3 2000UI"]),
        smoking_status="never",
        alcohol_consumption="none",
        physical_activity="moderate",
    )

    db.add(mother)
    db.add(son)
    db.flush()
    print(f"Created mother: {mother.email} (ID: {mother.id})")
    print(f"Created son: {son.email} (ID: {son.id})")
    return mother, son

# ============================================================
# LINKED ACCOUNTS
# ============================================================
def create_linked_accounts(mother, son):
    now = datetime.utcnow()
    accounts = []
    for user in [mother, son]:
        for provider in ["Regina Maria", "Sanador"]:
            acc = LinkedAccount(
                user_id=user.id,
                provider_name=provider,
                username=user.email.split("@")[0],
                last_sync=now - timedelta(days=2),
                status="ACTIVE",
                sync_enabled=True,
                sync_frequency="weekly",
                consecutive_failures=0,
            )
            db.add(acc)
            accounts.append(acc)
    db.flush()
    print(f"Created {len(accounts)} linked accounts.")
    return accounts

# ============================================================
# DOCUMENTS & BIOMARKERS - MOTHER
# ============================================================
def create_mother_data(mother):
    now = datetime.utcnow()

    # --- Document 1: Regina Maria - Hemoleucograma completa (6 months ago) ---
    doc1 = Document(
        user_id=mother.id,
        filename="Hemoleucograma_completa_sept2025.pdf",
        provider="Regina Maria",
        upload_date=now - timedelta(days=180),
        document_date=now - timedelta(days=180),
        is_processed=True,
        patient_name="Elena Popescu",
        file_hash=uuid.uuid4().hex[:32],
    )
    db.add(doc1)
    db.flush()

    biomarkers_doc1 = [
        ("Hemoglobina", "Hemoglobina", "11.2", 11.2, "g/dL", "12.0-16.0", "LOW", "Hematologie"),
        ("Hematocrit", "Hematocrit", "34.5", 34.5, "%", "36.0-46.0", "LOW", "Hematologie"),
        ("Fier seric", "Fier seric", "35", 35.0, "μg/dL", "60-170", "LOW", "Hematologie"),
        ("Feritina", "Feritina", "8.5", 8.5, "ng/mL", "13-150", "LOW", "Hematologie"),
        ("TIBC", "TIBC", "420", 420.0, "μg/dL", "250-370", "HIGH", "Hematologie"),
        ("Leucocite (WBC)", "Leucocite", "6.8", 6.8, "x10³/μL", "4.0-10.0", "NORMAL", "Hematologie"),
        ("Trombocite", "Trombocite", "245", 245.0, "x10³/μL", "150-400", "NORMAL", "Hematologie"),
        ("Eritrocite (RBC)", "Eritrocite", "4.1", 4.1, "x10⁶/μL", "4.0-5.5", "NORMAL", "Hematologie"),
        ("VEM (MCV)", "VEM", "76.2", 76.2, "fL", "80-100", "LOW", "Hematologie"),
        ("HEM (MCH)", "HEM", "25.8", 25.8, "pg", "27-33", "LOW", "Hematologie"),
    ]

    for name, canonical, val, num, unit, ref, flag, cat in biomarkers_doc1:
        db.add(TestResult(document_id=doc1.id, test_name=name, canonical_name=canonical,
                          value=val, numeric_value=num, unit=unit, reference_range=ref, flags=flag, category=cat))

    # --- Document 2: Sanador - Profil biochimic (6 months ago) ---
    doc2 = Document(
        user_id=mother.id,
        filename="Profil_biochimic_complet_sept2025.pdf",
        provider="Sanador",
        upload_date=now - timedelta(days=178),
        document_date=now - timedelta(days=178),
        is_processed=True,
        patient_name="Elena Popescu",
        file_hash=uuid.uuid4().hex[:32],
    )
    db.add(doc2)
    db.flush()

    biomarkers_doc2 = [
        ("Glicemie", "Glicemie", "92", 92.0, "mg/dL", "70-100", "NORMAL", "Metabolism"),
        ("Colesterol total", "Colesterol total", "215", 215.0, "mg/dL", "<200", "HIGH", "Profil Lipidic"),
        ("LDL Colesterol", "LDL Colesterol", "138", 138.0, "mg/dL", "<130", "HIGH", "Profil Lipidic"),
        ("HDL Colesterol", "HDL Colesterol", "52", 52.0, "mg/dL", ">50", "NORMAL", "Profil Lipidic"),
        ("Trigliceride", "Trigliceride", "125", 125.0, "mg/dL", "<150", "NORMAL", "Profil Lipidic"),
        ("ALT (GPT)", "ALT", "22", 22.0, "U/L", "0-35", "NORMAL", "Funcție Hepatică"),
        ("AST (GOT)", "AST", "19", 19.0, "U/L", "0-35", "NORMAL", "Funcție Hepatică"),
        ("Creatinina", "Creatinina", "0.78", 0.78, "mg/dL", "0.6-1.1", "NORMAL", "Funcție Renală"),
        ("Acid uric", "Acid uric", "4.2", 4.2, "mg/dL", "2.6-6.0", "NORMAL", "Metabolism"),
        ("Vitamina D (25-OH)", "Vitamina D", "28", 28.0, "ng/mL", "30-100", "LOW", "Vitamine"),
        ("Vitamina B12", "Vitamina B12", "310", 310.0, "pg/mL", "200-900", "NORMAL", "Vitamine"),
        ("Calciu total", "Calciu total", "9.2", 9.2, "mg/dL", "8.5-10.5", "NORMAL", "Minerale"),
        ("Magneziu", "Magneziu", "1.85", 1.85, "mg/dL", "1.7-2.2", "NORMAL", "Minerale"),
        ("TSH", "TSH", "2.8", 2.8, "mUI/L", "0.4-4.0", "NORMAL", "Tiroidă"),
        ("Proteina C reactiva (CRP)", "CRP", "3.8", 3.8, "mg/L", "<3.0", "HIGH", "Inflamație"),
    ]

    for name, canonical, val, num, unit, ref, flag, cat in biomarkers_doc2:
        db.add(TestResult(document_id=doc2.id, test_name=name, canonical_name=canonical,
                          value=val, numeric_value=num, unit=unit, reference_range=ref, flags=flag, category=cat))

    # --- Document 3: Regina Maria - Control oftalmologic (3 months ago) ---
    doc3 = Document(
        user_id=mother.id,
        filename="Examen_oftalmologic_dec2025.pdf",
        provider="Regina Maria",
        upload_date=now - timedelta(days=90),
        document_date=now - timedelta(days=90),
        is_processed=True,
        patient_name="Elena Popescu",
        file_hash=uuid.uuid4().hex[:32],
    )
    db.add(doc3)
    db.flush()

    biomarkers_doc3 = [
        ("Presiune intraoculara OD", "Presiune intraoculara OD", "19", 19.0, "mmHg", "10-21", "NORMAL", "Oftalmologie"),
        ("Presiune intraoculara OS", "Presiune intraoculara OS", "22", 22.0, "mmHg", "10-21", "HIGH", "Oftalmologie"),
        ("Acuitate vizuala OD", "Acuitate vizuala OD", "0.7", 0.7, "", "1.0", "LOW", "Oftalmologie"),
        ("Acuitate vizuala OS", "Acuitate vizuala OS", "0.6", 0.6, "", "1.0", "LOW", "Oftalmologie"),
    ]

    for name, canonical, val, num, unit, ref, flag, cat in biomarkers_doc3:
        db.add(TestResult(document_id=doc3.id, test_name=name, canonical_name=canonical,
                          value=val, numeric_value=num, unit=unit, reference_range=ref, flags=flag, category=cat))

    # --- Document 4: Sanador - Analize recente (2 weeks ago) ---
    doc4 = Document(
        user_id=mother.id,
        filename="Hemoleucograma_control_feb2026.pdf",
        provider="Sanador",
        upload_date=now - timedelta(days=14),
        document_date=now - timedelta(days=14),
        is_processed=True,
        patient_name="Elena Popescu",
        file_hash=uuid.uuid4().hex[:32],
    )
    db.add(doc4)
    db.flush()

    biomarkers_doc4 = [
        ("Hemoglobina", "Hemoglobina", "11.8", 11.8, "g/dL", "12.0-16.0", "LOW", "Hematologie"),
        ("Hematocrit", "Hematocrit", "35.8", 35.8, "%", "36.0-46.0", "LOW", "Hematologie"),
        ("Fier seric", "Fier seric", "48", 48.0, "μg/dL", "60-170", "LOW", "Hematologie"),
        ("Feritina", "Feritina", "12.0", 12.0, "ng/mL", "13-150", "LOW", "Hematologie"),
        ("Vitamina D (25-OH)", "Vitamina D", "32", 32.0, "ng/mL", "30-100", "NORMAL", "Vitamine"),
        ("CRP", "CRP", "2.5", 2.5, "mg/L", "<3.0", "NORMAL", "Inflamație"),
        ("VSH", "VSH", "18", 18.0, "mm/h", "0-20", "NORMAL", "Inflamație"),
        ("Leucocite (WBC)", "Leucocite", "7.1", 7.1, "x10³/μL", "4.0-10.0", "NORMAL", "Hematologie"),
    ]

    for name, canonical, val, num, unit, ref, flag, cat in biomarkers_doc4:
        db.add(TestResult(document_id=doc4.id, test_name=name, canonical_name=canonical,
                          value=val, numeric_value=num, unit=unit, reference_range=ref, flags=flag, category=cat))

    # --- Health Reports ---
    # General health report
    general_report = HealthReport(
        user_id=mother.id,
        report_type="general",
        title="Evaluare Generala Sanatate",
        summary=json.dumps({
            "summary": "Pacienta prezintă anemie feriprivă persistentă cu tendință ușoară de ameliorare, valori limită ale presiunii intraoculare la ochiul stâng necesitând monitorizare, și un profil lipidic ușor crescut. Gonartroza genunchiului drept necesită program de kinetoterapie.",
            "findings": [
                {"area": "Hematologie", "status": "attention", "detail": "Anemie feriprivă moderată — Hemoglobina 11.8 g/dL, Feritina 12 ng/mL. Ușoară ameliorare față de acum 6 luni (Hb 11.2), dar încă sub normal."},
                {"area": "Oftalmologie", "status": "attention", "detail": "Presiune intraoculară crescută la ochiul stâng (22 mmHg, limita superioară). Acuitate vizuală redusă bilateral (OD 0.7, OS 0.6). Se recomandă monitorizare glaucom."},
                {"area": "Profil Lipidic", "status": "attention", "detail": "Colesterol total 215 mg/dL și LDL 138 mg/dL ușor crescute. Risc cardiovascular moderat."},
                {"area": "Ortopedic", "status": "attention", "detail": "Gonartroza genunchi drept — necesită program de kinetoterapie pentru întărirea musculaturii și menținerea mobilității articulare."},
                {"area": "Inflamație", "status": "normal", "detail": "CRP normalizat la 2.5 mg/L (anterior 3.8). VSH normal. Tendință pozitivă."},
                {"area": "Tiroidă", "status": "normal", "detail": "TSH normal (2.8 mUI/L). Funcție tiroidiană normală."},
            ],
            "recommendations": [
                "Continuarea suplimentării cu fier (Tardyferon sau similar) — consultați medicul pentru doza optimă",
                "Control oftalmologic la 3 luni pentru monitorizarea presiunii intraoculare",
                "Kinetoterapie 2-3 ședințe/săptămână pentru gonartroza genunchi drept — exerciții de întărire cvadriceps",
                "Dietă bogată în fier: carne roșie, spanac, linte, sfeclă roșie",
                "Reducere colesterol prin dietă: limitare grăsimi saturate, creștere fibre",
                "Vitamina D3 suplimentar 2000 UI/zi în perioada iarnă-primăvară",
            ],
            "health_score": 68,
            "risk_areas": ["Anemie feriprivă", "Risc glaucom", "Gonartroza"],
        }),
        risk_level="attention",
        created_at=now - timedelta(days=13),
        biomarkers_analyzed=33,
    )
    db.add(general_report)

    # Nutrition report
    nutrition_report = HealthReport(
        user_id=mother.id,
        report_type="nutrition",
        title="Nutrition Recommendations",
        summary=json.dumps({
            "summary": "Plan alimentar conceput pentru combaterea anemiei feriprive, reducerea colesterolului și susținerea sănătății oculare. Accent pe alimente bogate în fier, omega-3 și antioxidanți.",
            "daily_targets": {"calories": "1800-2000 kcal", "protein": "65-75g", "hydration": "2.0L", "meal_frequency": "3 mese + 2 gustări"},
            "meal_plan": [
                {"day": "Ziua 1 - Luni", "meals": [
                    {"meal": "Mic dejun", "time": "7:30-8:30", "items": ["Terci de ovăz cu miere și nuci - 250g", "1 portocală", "Ceai verde - 200ml"], "calories": "~380 kcal", "notes": "Ovăzul oferă fibre solubile care reduc colesterolul", "recipe": "1. Fierbe 80g fulgi de ovăz în 250ml apă, 5 min. 2. Adaugă 1 lingură miere și 30g nuci cernuți. 3. Servește cu portocala feliată alături."},
                    {"meal": "Prânz", "time": "12:30-13:30", "items": ["Ciorbă de linte cu legume - 350ml", "Pâine integrală - 1 felie", "Salată de spanac cu semințe de dovleac - 150g"], "calories": "~520 kcal", "notes": "Lintea și spanacul sunt surse excelente de fier vegetal", "recipe": "1. Călește ceapa, morcovul și țelina tocate fin în 1 lingură ulei de măsline. 2. Adaugă 150g linte roșie spălată, 1L apă, sare, piper, boia. 3. Fierbe 25 min până lintea e moale. 4. Stoarce lămâie la final. 5. Servește cu pâine integrală și salată de spanac."},
                    {"meal": "Cină", "time": "18:30-19:30", "items": ["Piept de pui la grătar - 150g", "Orez brun cu legume - 200g", "Salată de sfeclă roșie - 100g"], "calories": "~480 kcal", "notes": "Sfecla roșie susține producția de hemoglobină; puiul oferă fier hem", "recipe": "1. Marinează pieptul de pui cu usturoi, lămâie, cimbru, 30 min. 2. Grătar 6-7 min pe fiecare parte. 3. Fierbe orezul brun 25 min, amestecă cu legume sotate. 4. Rade sfecla pe răzătoare, condimentează cu ulei și oțet."},
                ]},
                {"day": "Ziua 2 - Marți", "meals": [
                    {"meal": "Mic dejun", "time": "7:30-8:30", "items": ["2 ouă ochiuri pe pâine integrală", "Roșii cherry - 100g", "Suc de portocale proaspăt - 200ml"], "calories": "~400 kcal", "notes": "Vitamina C din portocale crește absorbția fierului din ouă", "recipe": "1. Încinge tigaia cu puțin ulei. 2. Sparge 2 ouă, gătește 3-4 min la foc mediu. 3. Prăjește pâinea. 4. Servește cu roșii și suc proaspăt."},
                    {"meal": "Prânz", "time": "12:30-13:30", "items": ["Mâncarică de mazăre cu pui - 350g", "Mămăligă - 150g", "Salată de varză cu morcov - 150g"], "calories": "~550 kcal", "notes": "Mazărea oferă fier și proteine vegetale; puiul completează cu fier hem", "recipe": "1. Călește ceapa tocată în ulei de măsline. 2. Adaugă 200g piept de pui tăiat cubulețe, sotează 5 min. 3. Adaugă 300g mazăre, 200ml apă, sare, piper, boia dulce, mărar. 4. Fierbe acoperit 20 min la foc mic. 5. Servește cu mămăligă."},
                    {"meal": "Cină", "time": "18:30-19:30", "items": ["Somon la cuptor cu lămâie - 150g", "Cartofi copți cu rozmarin - 200g", "Broccoli la aburi - 150g"], "calories": "~500 kcal", "notes": "Somonul oferă omega-3 benefice pentru ochi și inimă; broccoli susține sănătatea oculară", "recipe": "1. Asezonează somonul cu sare, piper, lămâie. 2. Coace la 200°C, 18 min. 3. Cartofii tăiați sferturi cu rozmarin și ulei, la cuptor 35 min. 4. Broccoli la aburi 5 min."},
                ]},
                {"day": "Ziua 3 - Miercuri", "meals": [
                    {"meal": "Mic dejun", "time": "7:30-8:30", "items": ["Smoothie cu spanac, banană și lapte de migdale - 350ml", "2 biscuiți integrali"], "calories": "~320 kcal", "notes": "Spanacul oferă fier și luteină pentru sănătatea ochilor", "recipe": "1. Blendează 50g spanac proaspăt, 1 banană, 250ml lapte de migdale. 2. Adaugă 1 linguriță miere. 3. Servește imediat cu biscuiții."},
                    {"meal": "Prânz", "time": "12:30-13:30", "items": ["Tocăniță de vită cu legume - 300g", "Paste integrale - 150g", "Salată verde cu castraveți - 100g"], "calories": "~580 kcal", "notes": "Carnea de vită este cea mai bună sursă de fier hem, ușor absorbabil", "recipe": "1. Rumeniți 200g carne de vită tăiată cuburi. 2. Adaugă ceapă, ardei, morcov, roșii. 3. Stingeți cu 100ml apă, boia, cimbru. 4. Înăbușiți 45 min acoperit. 5. Fierbeți pastele separat."},
                    {"meal": "Cină", "time": "18:30-19:30", "items": ["Supă cremă de dovleac - 300ml", "Pâine integrală prăjită cu brânză de vaci - 2 felii", "Salată de morcovi cu lămâie - 100g"], "calories": "~420 kcal", "notes": "Dovleacul și morcovii sunt bogați în beta-caroten, benefic pentru vedere", "recipe": "1. Sotează ceapa, adaugă 500g dovleac tăiat cuburi, 500ml supă. 2. Fierbe 20 min, blendează. 3. Condimentează cu nucșoară și smântână. 4. Întinde brânza pe pâinea prăjită."},
                ]},
                {"day": "Ziua 4 - Joi", "meals": [
                    {"meal": "Mic dejun", "time": "7:30-8:30", "items": ["Iaurt grecesc cu fructe de pădure și granola - 300g", "Ceai de măceșe - 200ml"], "calories": "~370 kcal", "notes": "Fructele de pădure conțin antioxidanți pentru sănătatea oculară", "recipe": "1. Pune 200g iaurt grecesc în bol. 2. Adaugă 80g mix de fructe de pădure. 3. Presară 40g granola deasupra."},
                    {"meal": "Prânz", "time": "12:30-13:30", "items": ["Ardei umpluți cu carne și orez - 2 buc", "Smântână 10% - 2 linguri", "Salată de roșii cu ceapă - 150g"], "calories": "~560 kcal", "notes": "Ardeii sunt bogați în vitamina C care crește absorbția fierului", "recipe": "1. Amestecă 250g carne tocată de vită cu 80g orez fiert, ceapă, mărar, condimente. 2. Umple 4 ardei grași. 3. Așază în oală cu sos de roșii. 4. Fierbe la foc mic 45 min acoperit."},
                    {"meal": "Cină", "time": "18:30-19:30", "items": ["Omletă cu spanac și telemea - 3 ouă", "Pâine integrală - 1 felie", "Salată de avocado - 100g"], "calories": "~450 kcal", "notes": "Spanacul cu ouă oferă combinație excelentă de fier și proteine", "recipe": "1. Bate 3 ouă cu sare și piper. 2. Sotează 50g spanac 2 min. 3. Toarnă ouăle, gătește 3 min. 4. Adaugă 40g telemea sfărâmată, pliază."},
                ]},
                {"day": "Ziua 5 - Vineri", "meals": [
                    {"meal": "Mic dejun", "time": "7:30-8:30", "items": ["Pâine integrală cu avocado și ou poșat", "Roșii - 100g", "Ceai verde - 200ml"], "calories": "~390 kcal", "notes": "Avocado oferă grăsimi sănătoase benefice cardiovascular", "recipe": "1. Prăjește pâinea. 2. Zdrobește avocado cu sare și lămâie. 3. Poșează oul 3 min în apă cu oțet. 4. Asamblează."},
                    {"meal": "Prânz", "time": "12:30-13:30", "items": ["Ciorbă de fasole cu afumătură - 350ml", "Pâine de casă - 1 felie", "Ceapă verde - 50g"], "calories": "~480 kcal", "notes": "Fasolea este bogată în fier vegetal și fibre care reduc colesterolul", "recipe": "1. Înmoaie 200g fasole peste noapte. 2. Fierbe cu morcov, țelină, ceapă 1 oră. 3. Adaugă 80g afumătură, roșii, boia. 4. Mai fierbe 20 min. 5. Adaugă oțet și leuștean."},
                    {"meal": "Cină", "time": "18:30-19:30", "items": ["Păstrăv la cuptor cu legume - 200g", "Spanac sotat cu usturoi - 150g", "Cartof copt - 1 buc"], "calories": "~470 kcal", "notes": "Peștele oferă omega-3 pentru sănătatea ochilor; spanacul completează fierul", "recipe": "1. Condimentează păstrăvul cu sare, lămâie, usturoi. 2. Așază pe pat de legume (ceapă, roșii, ardei). 3. Coace la 190°C, 25 min. 4. Sotează spanacul cu usturoi separat."},
                ]},
                {"day": "Ziua 6 - Sâmbătă", "meals": [
                    {"meal": "Mic dejun", "time": "8:30-9:30", "items": ["Clătite integrale cu brânză de vaci și dulceață - 3 buc", "Ceai de fructe - 200ml"], "calories": "~420 kcal", "notes": "Brânza de vaci oferă proteine și calciu", "recipe": "1. Amestecă 100g făină integrală, 1 ou, 200ml lapte. 2. Coace 3 clătite subțiri. 3. Umple cu 150g brânză de vaci și 2 linguri dulceață de fructe de pădure."},
                    {"meal": "Prânz", "time": "13:00-14:00", "items": ["Sarmale în foi de varză - 3 buc", "Mămăligă - 150g", "Smântână - 2 linguri", "Ardei iute - 1 buc"], "calories": "~620 kcal", "notes": "Sarmalele oferă proteine complete; mămăliga susține energia", "recipe": "1. Amestecă 300g carne tocată de porc+vită cu orez, ceapă, boia, cimbru. 2. Învelește în foi de varză murată. 3. Așază în oală cu straturi de varză. 4. Fierbe acoperit la foc mic 2-3 ore. 5. Servește cu mămăligă și smântână."},
                    {"meal": "Cină", "time": "19:00-20:00", "items": ["Supă de pui cu tăiței de casă - 350ml", "Pâine de casă - 1 felie"], "calories": "~380 kcal", "notes": "Supa de pui oferă proteine și minerale ușor asimilabile", "recipe": "1. Fierbe 1 pulpă de pui cu legume (morcov, țelină, păstârnac, ceapă) 1 oră. 2. Scoate puiul, desfă carnea. 3. Adaugă tăiței de casă, fierbe 10 min. 4. Adaugă verdeață: pătrunjel, leuștean."},
                ]},
                {"day": "Ziua 7 - Duminică", "meals": [
                    {"meal": "Mic dejun", "time": "9:00-10:00", "items": ["Brunch: ouă benedict cu spanac pe pâine integrală", "Suc de sfeclă și morcov - 200ml"], "calories": "~430 kcal", "notes": "Sucul de sfeclă stimulează producția de hemoglobină", "recipe": "1. Poșează 2 ouă. 2. Sotează spanac cu unt. 3. Prăjește pâinea. 4. Asamblează: pâine, spanac, ou poșat, sos hollandaise light."},
                    {"meal": "Prânz", "time": "13:00-14:00", "items": ["Ghiveci de legume la cuptor - 350g", "Piept de curcan la grătar - 150g", "Salată de vinete cu roșii - 100g"], "calories": "~520 kcal", "notes": "Ghiveciul oferă varietate mare de vitamine și minerale", "recipe": "1. Taie cuburi: dovlecei, vinete, ardei, cartofi, ceapă, roșii. 2. Amestecă cu ulei de măsline, usturoi, cimbru. 3. Coace la 200°C, 40 min. 4. Grătar curcanul separat."},
                    {"meal": "Cină", "time": "18:30-19:30", "items": ["Salată Caesar cu piept de pui - 300g", "Crutoane integrale - 30g", "Parmezan ras - 20g"], "calories": "~420 kcal", "notes": "Salata verde conține luteină benefică pentru sănătatea ochilor", "recipe": "1. Grătar pieptul de pui, taie felii. 2. Amestecă salata romană cu sos Caesar light. 3. Adaugă puiul, crutoane integrale, parmezan ras."},
                ]},
            ],
            "priority_foods": [
                {"category": "Alimente bogate în fier", "reason": "Combaterea anemiei feriprive", "foods": ["Carne roșie de vită", "Ficat de pui", "Linte", "Spanac", "Sfeclă roșie", "Năut"], "target": "15-20mg fier/zi"},
                {"category": "Surse de Omega-3", "reason": "Sănătatea ochilor și reducerea inflamației", "foods": ["Somon", "Păstrăv", "Sardine", "Nuci", "Semințe de in"], "target": "250-500mg EPA+DHA/zi"},
                {"category": "Alimente pentru vedere", "reason": "Susținerea sănătății oculare", "foods": ["Morcovi", "Spanac", "Dovleac", "Afine", "Ouă (luteină)"], "target": "6-10mg luteină/zi"},
            ],
            "foods_to_reduce": [
                {"category": "Grăsimi saturate", "reason": "Reducerea colesterolului LDL", "examples": ["Unt excesiv", "Carne grasă de porc", "Brânzeturi grase"], "alternatives": ["Ulei de măsline", "Carne slabă de pui/curcan", "Brânză de vaci"]},
                {"category": "Dulciuri procesate", "reason": "Control glicemie și greutate", "examples": ["Prăjituri", "Sucuri acidulate", "Ciocolată cu lapte"], "alternatives": ["Fructe proaspete", "Ciocolată neagră 70%+", "Miere cu moderație"]},
            ],
            "supplements_to_discuss": [
                {"supplement": "Fier (Tardyferon/Sideralia)", "reason": "Corecția anemiei feriprive — Feritina 12 ng/mL", "note": "A se lua pe stomacul gol cu vitamina C"},
                {"supplement": "Vitamina D3 2000 UI/zi", "reason": "Valori limită — 32 ng/mL", "note": "De luat cu masa, preferabil cu grăsimi"},
                {"supplement": "Omega-3 (ulei de pește)", "reason": "Susținerea sănătății oculare și cardiovasculare", "note": "1000mg/zi cu EPA+DHA"},
                {"supplement": "Luteină + Zeaxantină", "reason": "Protecția retinei — presiune intraoculară la limită", "note": "10mg luteină + 2mg zeaxantină/zi"},
            ],
            "shopping_list": [
                {"category": "Carne & Pește", "items": ["Piept de pui 1kg", "Carne de vită 500g", "Somon file 400g", "Păstrăv 2 buc", "Carne tocată vită+porc 500g"]},
                {"category": "Legume", "items": ["Spanac 500g", "Sfeclă roșie 4 buc", "Morcovi 1kg", "Dovleac 1 buc", "Broccoli 500g", "Roșii 1kg", "Ardei grași 6 buc", "Varză murată 1 borcan"]},
                {"category": "Fructe", "items": ["Portocale 2kg", "Banane 1kg", "Afine/fructe de pădure 300g", "Lămâi 5 buc", "Avocado 3 buc"]},
                {"category": "Cereale & Leguminoase", "items": ["Fulgi de ovăz 500g", "Orez brun 500g", "Linte roșie 500g", "Paste integrale 500g", "Pâine integrală", "Fasole uscată 500g"]},
                {"category": "Lactate", "items": ["Iaurt grecesc 500g", "Brânză de vaci 400g", "Telemea 200g", "Smântână 10% 200ml", "Lapte de migdale 1L"]},
            ],
            "warnings": [
                "Anemia feriprivă necesită monitorizare medicală — nu întrerupeți tratamentul cu fier fără consultarea medicului",
                "Presiunea intraoculară crescută la ochiul stâng necesită control oftalmologic regulat",
                "Consultați medicul înainte de a începe suplimentele recomandate",
            ],
        }),
        risk_level="attention",
        created_at=now - timedelta(days=13),
        biomarkers_analyzed=33,
    )
    db.add(nutrition_report)

    print(f"Created mother data: 4 documents, {10+15+4+8} biomarkers, 2 reports.")

# ============================================================
# DOCUMENTS & BIOMARKERS - SON
# ============================================================
def create_son_data(son):
    now = datetime.utcnow()

    # --- Document 1: Regina Maria - Analize pediatrice (5 months ago) ---
    doc1 = Document(
        user_id=son.id,
        filename="Analize_pediatrice_oct2025.pdf",
        provider="Regina Maria",
        upload_date=now - timedelta(days=150),
        document_date=now - timedelta(days=150),
        is_processed=True,
        patient_name="Andrei Popescu",
        file_hash=uuid.uuid4().hex[:32],
    )
    db.add(doc1)
    db.flush()

    biomarkers_doc1 = [
        ("Hemoglobina", "Hemoglobina", "11.5", 11.5, "g/dL", "11.5-15.5", "NORMAL", "Hematologie"),
        ("Hematocrit", "Hematocrit", "35.2", 35.2, "%", "35-45", "NORMAL", "Hematologie"),
        ("Fier seric", "Fier seric", "45", 45.0, "μg/dL", "50-120", "LOW", "Hematologie"),
        ("Feritina", "Feritina", "15", 15.0, "ng/mL", "20-200", "LOW", "Hematologie"),
        ("Leucocite (WBC)", "Leucocite", "8.2", 8.2, "x10³/μL", "4.5-13.5", "NORMAL", "Hematologie"),
        ("Eozinofile", "Eozinofile", "8.5", 8.5, "%", "1-5", "HIGH", "Hematologie"),
        ("IgE total", "IgE total", "385", 385.0, "UI/mL", "<100", "HIGH", "Imunologie"),
        ("Vitamina D (25-OH)", "Vitamina D", "18", 18.0, "ng/mL", "30-100", "LOW", "Vitamine"),
        ("Calciu total", "Calciu total", "9.0", 9.0, "mg/dL", "8.8-10.8", "NORMAL", "Minerale"),
        ("Fosfataza alcalina", "Fosfataza alcalina", "320", 320.0, "U/L", "100-390", "NORMAL", "Metabolism osos"),
        ("Glicemie", "Glicemie", "82", 82.0, "mg/dL", "70-100", "NORMAL", "Metabolism"),
        ("TSH", "TSH", "3.1", 3.1, "mUI/L", "0.7-5.7", "NORMAL", "Tiroidă"),
    ]

    for name, canonical, val, num, unit, ref, flag, cat in biomarkers_doc1:
        db.add(TestResult(document_id=doc1.id, test_name=name, canonical_name=canonical,
                          value=val, numeric_value=num, unit=unit, reference_range=ref, flags=flag, category=cat))

    # --- Document 2: Sanador - Panel alergologic (5 months ago) ---
    doc2 = Document(
        user_id=son.id,
        filename="Panel_alergii_oct2025.pdf",
        provider="Sanador",
        upload_date=now - timedelta(days=148),
        document_date=now - timedelta(days=148),
        is_processed=True,
        patient_name="Andrei Popescu",
        file_hash=uuid.uuid4().hex[:32],
    )
    db.add(doc2)
    db.flush()

    biomarkers_doc2 = [
        ("IgE specific Acarieni", "IgE Acarieni", "45.2", 45.2, "kU/L", "<0.35", "HIGH", "Alergologie"),
        ("IgE specific Ambrozie", "IgE Ambrozie", "28.7", 28.7, "kU/L", "<0.35", "HIGH", "Alergologie"),
        ("IgE specific Polen graminee", "IgE Polen graminee", "12.5", 12.5, "kU/L", "<0.35", "HIGH", "Alergologie"),
        ("IgE specific Lactoza", "IgE Lactoza", "8.3", 8.3, "kU/L", "<0.35", "HIGH", "Alergologie"),
        ("IgE specific Ou", "IgE Ou", "0.12", 0.12, "kU/L", "<0.35", "NORMAL", "Alergologie"),
        ("IgE specific Gluten", "IgE Gluten", "0.08", 0.08, "kU/L", "<0.35", "NORMAL", "Alergologie"),
    ]

    for name, canonical, val, num, unit, ref, flag, cat in biomarkers_doc2:
        db.add(TestResult(document_id=doc2.id, test_name=name, canonical_name=canonical,
                          value=val, numeric_value=num, unit=unit, reference_range=ref, flags=flag, category=cat))

    # --- Document 3: Regina Maria - Control + radiografie (2 months ago) ---
    doc3 = Document(
        user_id=son.id,
        filename="Evaluare_ortopedie_scolioza_ian2026.pdf",
        provider="Regina Maria",
        upload_date=now - timedelta(days=60),
        document_date=now - timedelta(days=60),
        is_processed=True,
        patient_name="Andrei Popescu",
        file_hash=uuid.uuid4().hex[:32],
    )
    db.add(doc3)
    db.flush()

    biomarkers_doc3 = [
        ("Unghi Cobb", "Unghi Cobb", "18", 18.0, "grade", "<10", "HIGH", "Ortopedic"),
        ("Rotație vertebrală", "Rotație vertebrală", "1", 1.0, "grad Nash-Moe", "0", "HIGH", "Ortopedic"),
    ]

    for name, canonical, val, num, unit, ref, flag, cat in biomarkers_doc3:
        db.add(TestResult(document_id=doc3.id, test_name=name, canonical_name=canonical,
                          value=val, numeric_value=num, unit=unit, reference_range=ref, flags=flag, category=cat))

    # --- Document 4: Sanador - Analize recente (1 week ago) ---
    doc4 = Document(
        user_id=son.id,
        filename="Hemoleucograma_control_mar2026.pdf",
        provider="Sanador",
        upload_date=now - timedelta(days=7),
        document_date=now - timedelta(days=7),
        is_processed=True,
        patient_name="Andrei Popescu",
        file_hash=uuid.uuid4().hex[:32],
    )
    db.add(doc4)
    db.flush()

    biomarkers_doc4 = [
        ("Hemoglobina", "Hemoglobina", "11.8", 11.8, "g/dL", "11.5-15.5", "NORMAL", "Hematologie"),
        ("Fier seric", "Fier seric", "52", 52.0, "μg/dL", "50-120", "NORMAL", "Hematologie"),
        ("Feritina", "Feritina", "18", 18.0, "ng/mL", "20-200", "LOW", "Hematologie"),
        ("Vitamina D (25-OH)", "Vitamina D", "22", 22.0, "ng/mL", "30-100", "LOW", "Vitamine"),
        ("Eozinofile", "Eozinofile", "7.2", 7.2, "%", "1-5", "HIGH", "Hematologie"),
        ("IgE total", "IgE total", "350", 350.0, "UI/mL", "<100", "HIGH", "Imunologie"),
        ("Leucocite (WBC)", "Leucocite", "7.8", 7.8, "x10³/μL", "4.5-13.5", "NORMAL", "Hematologie"),
        ("Calciu total", "Calciu total", "9.2", 9.2, "mg/dL", "8.8-10.8", "NORMAL", "Minerale"),
    ]

    for name, canonical, val, num, unit, ref, flag, cat in biomarkers_doc4:
        db.add(TestResult(document_id=doc4.id, test_name=name, canonical_name=canonical,
                          value=val, numeric_value=num, unit=unit, reference_range=ref, flags=flag, category=cat))

    # --- Health Report ---
    general_report = HealthReport(
        user_id=son.id,
        report_type="general",
        title="Evaluare Generala Sanatate",
        summary=json.dumps({
            "summary": "Pacientul pediatric prezintă deficit de vitamina D persistent, depozite de fier la limita inferioară, alergii multiple (acarieni, ambrozie, lactoza) și scolioză toracică moderată (unghi Cobb 18°) necesitând kinetoterapie activă.",
            "findings": [
                {"area": "Vitamina D", "status": "concern", "detail": "Deficit persistent de vitamina D — 22 ng/mL (anterior 18 ng/mL). Ameliorare ușoară sub suplimentare, dar încă sub valoarea optimă de 30 ng/mL. Critic pentru creșterea osoasă la această vârstă."},
                {"area": "Hematologie", "status": "attention", "detail": "Feritina 18 ng/mL (limita inferioară, sub 20). Fierul seric s-a normalizat la 52 μg/dL. Risc de anemie feriprivă dacă nu se menține aportul."},
                {"area": "Alergologie", "status": "attention", "detail": "Alergii multiple confirmate: acarieni (IgE 45.2), ambrozie (28.7), polen graminee (12.5), intoleranță lactoză (8.3). IgE total ridicat (350 UI/mL). Eozinofile crescute (7.2%)."},
                {"area": "Ortopedic", "status": "concern", "detail": "Scolioză toracică cu unghi Cobb 18° — formă moderată. Rotație vertebrală grad 1 Nash-Moe. Necesită kinetoterapie specifică și monitorizare la 6 luni. Nu necesită corset la acest grad."},
                {"area": "Metabolism", "status": "normal", "detail": "Glicemie normală (82 mg/dL), TSH normal (3.1 mUI/L), calciu normal. Creștere și dezvoltare în parametri normali."},
            ],
            "recommendations": [
                "Vitamina D3 suplimentar 2000 UI/zi — control la 3 luni pentru ajustare doză",
                "Kinetoterapie specifică scolioză 3x/săptămână — exerciții Schroth sau SEAS",
                "Dietă bogată în fier: carne roșie 2-3x/săptămână, leguminoase, spanac",
                "Evitare lactate din lapte de vacă — înlocuire cu alternative (lapte de migdale, soia)",
                "Aerius 5mg continuat în sezon alergic; consultare alergolog pentru imunoterapie",
                "Control ortopedic cu radiografie la 6 luni pentru monitorizare unghi Cobb",
                "Activitate fizică regulată: înot, exerciții de postură, evitare sporturi cu impact asimetric",
            ],
            "health_score": 62,
            "risk_areas": ["Deficit Vitamina D", "Scolioză moderată", "Alergii multiple", "Depozite fier scăzute"],
        }),
        risk_level="attention",
        created_at=now - timedelta(days=6),
        biomarkers_analyzed=28,
    )
    db.add(general_report)

    print(f"Created son data: 4 documents, {12+6+2+8} biomarkers, 1 report.")

# ============================================================
# FAMILY, SUBSCRIPTIONS, FOOD PREFS
# ============================================================
def create_family_and_extras(mother, son):
    now = datetime.utcnow()

    # Family group
    family = FamilyGroup(
        owner_id=mother.id,
        name="Familia Popescu",
        invite_code=uuid.uuid4().hex[:8],
        created_at=now - timedelta(days=60),
    )
    db.add(family)
    db.flush()

    member_mother = FamilyMember(family_id=family.id, user_id=mother.id, role="owner", joined_at=now - timedelta(days=60))
    member_son = FamilyMember(family_id=family.id, user_id=son.id, role="member", joined_at=now - timedelta(days=59))
    db.add(member_mother)
    db.add(member_son)

    # Subscriptions — Premium for mother, linked via family for son
    sub_mother = Subscription(user_id=mother.id, tier="family", status="active", billing_cycle="monthly",
                              current_period_start=now - timedelta(days=15), current_period_end=now + timedelta(days=15))
    sub_son = Subscription(user_id=son.id, tier="family", status="active", billing_cycle="monthly",
                           current_period_start=now - timedelta(days=15), current_period_end=now + timedelta(days=15))
    db.add(sub_mother)
    db.add(sub_son)

    # Usage trackers
    db.add(UsageTracker(user_id=mother.id, ai_analyses_this_month=2, month_start=now.replace(day=1),
                        total_ai_analyses=8, total_documents_uploaded=4))
    db.add(UsageTracker(user_id=son.id, ai_analyses_this_month=1, month_start=now.replace(day=1),
                        total_ai_analyses=4, total_documents_uploaded=4))

    # Notification preferences
    db.add(NotificationPreference(user_id=mother.id))
    db.add(NotificationPreference(user_id=son.id))

    # Food preferences for mother
    import hashlib
    def add_food_pref(user_id, name, pref):
        h = hashlib.sha256(name.lower().strip().encode()).hexdigest()
        db.add(FoodPreference(user_id=user_id, food_name_hash=h, food_name=name, preference=pref, source="meal_plan"))

    add_food_pref(mother.id, "Spanac", "liked")
    add_food_pref(mother.id, "Somon", "liked")
    add_food_pref(mother.id, "Linte", "liked")
    add_food_pref(mother.id, "Sfeclă roșie", "liked")
    add_food_pref(mother.id, "Broccoli", "liked")
    add_food_pref(mother.id, "Ficat", "disliked")
    add_food_pref(mother.id, "Sardine", "disliked")

    add_food_pref(son.id, "Piept de pui", "liked")
    add_food_pref(son.id, "Orez", "liked")
    add_food_pref(son.id, "Banane", "liked")
    add_food_pref(son.id, "Broccoli", "disliked")
    add_food_pref(son.id, "Spanac", "disliked")
    add_food_pref(son.id, "Pește", "disliked")

    # Medications
    db.add(Medication(user_id=mother.id, name="Tardyferon", dosage="80mg fier", frequency="daily",
                      time_of_day="morning", notes="Pe stomacul gol, cu suc de portocale", is_active=True))
    db.add(Medication(user_id=mother.id, name="Vitamina D3", dosage="2000 UI", frequency="daily",
                      time_of_day="morning", notes="Cu micul dejun", is_active=True))
    db.add(Medication(user_id=mother.id, name="Ocuvit Plus", dosage="1 comprimat", frequency="daily",
                      time_of_day="evening", notes="Luteină + Zeaxantină pentru ochi", is_active=True))
    db.add(Medication(user_id=mother.id, name="Ibuprofen", dosage="400mg", frequency="as_needed",
                      time_of_day=None, notes="La nevoie pentru dureri genunchi", is_active=True))

    db.add(Medication(user_id=son.id, name="Vitamina D3", dosage="2000 UI", frequency="daily",
                      time_of_day="morning", notes="Cu micul dejun", is_active=True))
    db.add(Medication(user_id=son.id, name="Aerius", dosage="5mg", frequency="daily",
                      time_of_day="evening", notes="Antialergic — sezon alergic", is_active=True))
    db.add(Medication(user_id=son.id, name="Calcium + Vitamina K2", dosage="500mg Ca", frequency="daily",
                      time_of_day="evening", notes="Pentru dezvoltare osoasă", is_active=True))

    print("Created family, subscriptions, food preferences, medications.")

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=== Seeding Demo Accounts ===")
    cleanup()
    mother, son = create_users()
    create_linked_accounts(mother, son)
    create_mother_data(mother)
    create_son_data(son)
    create_family_and_extras(mother, son)
    db.commit()
    print("\n=== DONE ===")
    print(f"Mother: {MOTHER_EMAIL} / {MOTHER_PASSWORD}")
    print(f"Son:    {SON_EMAIL} / {SON_PASSWORD}")
    print("Both have Family subscription, linked Regina Maria + Sanador accounts.")
    print("Login at https://analize.online to verify.")
