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
import shutil
from pathlib import Path
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
# PDF GENERATION — minimal valid PDFs with biomarker data
# ============================================================
def generate_minimal_pdf(title, patient_name, date_str, lines):
    """Generate a minimal valid PDF with text content (no external libs needed)."""
    # Build page content with simple text positioning
    text_objects = []
    # Title
    text_objects.append(f"BT /F1 16 Tf 50 780 Td ({_pdf_escape(title)}) Tj ET")
    text_objects.append(f"BT /F1 10 Tf 50 760 Td (Pacient: {_pdf_escape(patient_name)}) Tj ET")
    text_objects.append(f"BT /F1 10 Tf 50 745 Td (Data: {_pdf_escape(date_str)}) Tj ET")
    text_objects.append(f"BT /F1 10 Tf 50 725 Td (-----------------------------------------------------------) Tj ET")

    y = 710
    for line in lines:
        if y < 50:
            break
        text_objects.append(f"BT /F1 9 Tf 50 {y} Td ({_pdf_escape(line)}) Tj ET")
        y -= 14

    stream_content = "\n".join(text_objects)
    stream_bytes = stream_content.encode('latin-1', errors='replace')

    # Build PDF structure
    objects = []
    # Obj 1: Catalog
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    # Obj 2: Pages
    objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj")
    # Obj 3: Page
    objects.append(f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj")
    # Obj 4: Content stream
    objects.append(f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n{stream_content}\nendstream\nendobj")
    # Obj 5: Font
    objects.append("5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj")

    # Assemble PDF
    pdf_lines = ["%PDF-1.4"]
    offsets = []
    for obj in objects:
        offsets.append(len("\n".join(pdf_lines).encode('latin-1', errors='replace')) + 1)
        pdf_lines.append(obj)

    xref_offset = len("\n".join(pdf_lines).encode('latin-1', errors='replace')) + 1
    pdf_lines.append("xref")
    pdf_lines.append(f"0 {len(objects) + 1}")
    pdf_lines.append("0000000000 65535 f ")
    for off in offsets:
        pdf_lines.append(f"{off:010d} 00000 n ")

    pdf_lines.append("trailer")
    pdf_lines.append(f"<< /Size {len(objects) + 1} /Root 1 0 R >>")
    pdf_lines.append("startxref")
    pdf_lines.append(str(xref_offset))
    pdf_lines.append("%%EOF")

    return "\n".join(pdf_lines).encode('latin-1', errors='replace')


def _pdf_escape(text):
    """Escape special PDF characters and transliterate Romanian diacritics."""
    # Transliterate Romanian diacritics to ASCII for PDF compatibility
    diacritics = {'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
                  'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T',
                  'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
                  'ü': 'u', 'ö': 'o', 'ä': 'a', 'é': 'e', 'è': 'e',
                  '—': '-', '–': '-', '°': 'o', '³': '3', '⁶': '6',
                  'μ': 'u', '±': '+/-'}
    for k, v in diacritics.items():
        text = text.replace(k, v)
    return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def create_pdf_for_document(user_id, doc, biomarkers):
    """Create a PDF file on disk and set file_path on the document."""
    base_dir = Path(os.path.dirname(__file__)) / "data" / "raw" / str(user_id)
    base_dir.mkdir(parents=True, exist_ok=True)

    date_str = doc.document_date.strftime("%d.%m.%Y") if doc.document_date else "N/A"

    lines = []
    for name, canonical, val, num, unit, ref, flag, cat in biomarkers:
        flag_marker = " *" if flag != "NORMAL" else ""
        lines.append(f"{name}: {val} {unit}  (ref: {ref}) [{flag}]{flag_marker}")

    if not lines:
        lines = ["Document fara rezultate numerice.", "Consultati medicul pentru detalii."]

    pdf_bytes = generate_minimal_pdf(
        title=doc.filename.replace('.pdf', '').replace('_', ' '),
        patient_name=doc.patient_name or "N/A",
        date_str=date_str,
        lines=lines
    )

    file_path = base_dir / doc.filename
    file_path.write_bytes(pdf_bytes)
    doc.file_path = str(file_path)


# ============================================================
# CLEANUP - Remove existing demo accounts
# ============================================================
def cleanup():
    for email in [MOTHER_EMAIL, SON_EMAIL]:
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Delete family memberships - must delete ALL members of owned groups first
            owned_groups = db.query(FamilyGroup).filter(FamilyGroup.owner_id == user.id).all()
            for group in owned_groups:
                db.query(FamilyMember).filter(FamilyMember.family_id == group.id).delete()
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
            # Clean up file directories
            user_dir = Path(os.path.dirname(__file__)) / "data" / "raw" / str(user.id)
            if user_dir.exists():
                shutil.rmtree(user_dir)
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
        ("Fier seric", "Fier seric", "35", 35.0, "ug/dL", "60-170", "LOW", "Hematologie"),
        ("Feritina", "Feritina", "8.5", 8.5, "ng/mL", "13-150", "LOW", "Hematologie"),
        ("TIBC", "TIBC", "420", 420.0, "ug/dL", "250-370", "HIGH", "Hematologie"),
        ("Leucocite (WBC)", "Leucocite", "6.8", 6.8, "x10^3/uL", "4.0-10.0", "NORMAL", "Hematologie"),
        ("Trombocite", "Trombocite", "245", 245.0, "x10^3/uL", "150-400", "NORMAL", "Hematologie"),
        ("Eritrocite (RBC)", "Eritrocite", "4.1", 4.1, "x10^6/uL", "4.0-5.5", "NORMAL", "Hematologie"),
        ("VEM (MCV)", "VEM", "76.2", 76.2, "fL", "80-100", "LOW", "Hematologie"),
        ("HEM (MCH)", "HEM", "25.8", 25.8, "pg", "27-33", "LOW", "Hematologie"),
    ]

    for name, canonical, val, num, unit, ref, flag, cat in biomarkers_doc1:
        db.add(TestResult(document_id=doc1.id, test_name=name, canonical_name=canonical,
                          value=val, numeric_value=num, unit=unit, reference_range=ref, flags=flag, category=cat))
    create_pdf_for_document(mother.id, doc1, biomarkers_doc1)

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
        ("ALT (GPT)", "ALT", "22", 22.0, "U/L", "0-35", "NORMAL", "Functie Hepatica"),
        ("AST (GOT)", "AST", "19", 19.0, "U/L", "0-35", "NORMAL", "Functie Hepatica"),
        ("Creatinina", "Creatinina", "0.78", 0.78, "mg/dL", "0.6-1.1", "NORMAL", "Functie Renala"),
        ("Acid uric", "Acid uric", "4.2", 4.2, "mg/dL", "2.6-6.0", "NORMAL", "Metabolism"),
        ("Vitamina D (25-OH)", "Vitamina D", "28", 28.0, "ng/mL", "30-100", "LOW", "Vitamine"),
        ("Vitamina B12", "Vitamina B12", "310", 310.0, "pg/mL", "200-900", "NORMAL", "Vitamine"),
        ("Calciu total", "Calciu total", "9.2", 9.2, "mg/dL", "8.5-10.5", "NORMAL", "Minerale"),
        ("Magneziu", "Magneziu", "1.85", 1.85, "mg/dL", "1.7-2.2", "NORMAL", "Minerale"),
        ("TSH", "TSH", "2.8", 2.8, "mUI/L", "0.4-4.0", "NORMAL", "Tiroida"),
        ("Proteina C reactiva (CRP)", "CRP", "3.8", 3.8, "mg/L", "<3.0", "HIGH", "Inflamatie"),
    ]

    for name, canonical, val, num, unit, ref, flag, cat in biomarkers_doc2:
        db.add(TestResult(document_id=doc2.id, test_name=name, canonical_name=canonical,
                          value=val, numeric_value=num, unit=unit, reference_range=ref, flags=flag, category=cat))
    create_pdf_for_document(mother.id, doc2, biomarkers_doc2)

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
    create_pdf_for_document(mother.id, doc3, biomarkers_doc3)

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
        ("Fier seric", "Fier seric", "48", 48.0, "ug/dL", "60-170", "LOW", "Hematologie"),
        ("Feritina", "Feritina", "12.0", 12.0, "ng/mL", "13-150", "LOW", "Hematologie"),
        ("Vitamina D (25-OH)", "Vitamina D", "32", 32.0, "ng/mL", "30-100", "NORMAL", "Vitamine"),
        ("CRP", "CRP", "2.5", 2.5, "mg/L", "<3.0", "NORMAL", "Inflamatie"),
        ("VSH", "VSH", "18", 18.0, "mm/h", "0-20", "NORMAL", "Inflamatie"),
        ("Leucocite (WBC)", "Leucocite", "7.1", 7.1, "x10^3/uL", "4.0-10.0", "NORMAL", "Hematologie"),
    ]

    for name, canonical, val, num, unit, ref, flag, cat in biomarkers_doc4:
        db.add(TestResult(document_id=doc4.id, test_name=name, canonical_name=canonical,
                          value=val, numeric_value=num, unit=unit, reference_range=ref, flags=flag, category=cat))
    create_pdf_for_document(mother.id, doc4, biomarkers_doc4)

    # --- Health Reports ---
    # General health report
    mother_findings = [
        {"category": "Hematologie", "status": "attention", "explanation": "Anemie feripriva moderata - Hemoglobina 11.8 g/dL, Feritina 12 ng/mL. Usoara ameliorare fata de acum 6 luni (Hb 11.2), dar inca sub normal.", "markers": ["Hemoglobina", "Feritina", "Fier seric"]},
        {"category": "Oftalmologie", "status": "attention", "explanation": "Presiune intraoculara crescuta la ochiul stang (22 mmHg, limita superioara). Acuitate vizuala redusa bilateral (OD 0.7, OS 0.6). Se recomanda monitorizare glaucom.", "markers": ["Presiune intraoculara OS", "Acuitate vizuala OD", "Acuitate vizuala OS"]},
        {"category": "Profil Lipidic", "status": "attention", "explanation": "Colesterol total 215 mg/dL si LDL 138 mg/dL usor crescute. Risc cardiovascular moderat.", "markers": ["Colesterol total", "LDL Colesterol"]},
        {"category": "Ortopedic", "status": "attention", "explanation": "Gonartroza genunchi drept - necesita program de kinetoterapie pentru intarirea musculaturii si mentinerea mobilitatii articulare."},
        {"category": "Inflamatie", "status": "normal", "explanation": "CRP normalizat la 2.5 mg/L (anterior 3.8). VSH normal. Tendinta pozitiva.", "markers": ["CRP", "VSH"]},
        {"category": "Tiroida", "status": "normal", "explanation": "TSH normal (2.8 mUI/L). Functie tiroidiana normala.", "markers": ["TSH"]},
    ]
    mother_recommendations = [
        {"action": "Continuarea suplimentarii cu fier (Tardyferon sau similar)", "reason": "Corectia anemiei feriprive - Feritina 12 ng/mL, Hemoglobina 11.8 g/dL", "priority": "high"},
        {"action": "Control oftalmologic la 3 luni", "reason": "Monitorizarea presiunii intraoculare crescute la ochiul stang (22 mmHg)", "priority": "high"},
        {"action": "Kinetoterapie 2-3 sedinte/saptamana", "reason": "Program de recuperare pentru gonartroza genunchi drept - exercitii de intarire cvadriceps", "priority": "high"},
        {"action": "Dieta bogata in fier", "reason": "Carne rosie, spanac, linte, sfecla rosie - surse naturale de fier pentru combaterea anemiei", "priority": "medium"},
        {"action": "Reducere colesterol prin dieta", "reason": "Limitare grasimi saturate, crestere fibre - Colesterol total 215, LDL 138", "priority": "medium"},
        {"action": "Vitamina D3 suplimentar 2000 UI/zi", "reason": "Mentinerea nivelului optim de vitamina D in perioada iarna-primavara", "priority": "low"},
    ]
    general_report = HealthReport(
        user_id=mother.id,
        report_type="general",
        title="Evaluare Generala Sanatate",
        summary="Pacienta prezinta anemie feripriva persistenta cu tendinta usoara de ameliorare, valori limita ale presiunii intraoculare la ochiul stang necesitand monitorizare, si un profil lipidic usor crescut. Gonartroza genunchiului drept necesita program de kinetoterapie.",
        findings=json.dumps(mother_findings),
        recommendations=json.dumps(mother_recommendations),
        risk_level="attention",
        created_at=now - timedelta(days=13),
        biomarkers_analyzed=33,
    )
    db.add(general_report)

    # Nutrition report (stored as full JSON in summary — this is the expected format for lifestyle page)
    nutrition_report = HealthReport(
        user_id=mother.id,
        report_type="nutrition",
        title="Plan Alimentar Personalizat",
        summary=json.dumps({
            "summary": "Plan alimentar conceput pentru combaterea anemiei feriprive, reducerea colesterolului si sustinerea sanatatii oculare. Accent pe alimente bogate in fier, omega-3 si antioxidanti.",
            "daily_targets": {"calories": "1800-2000 kcal", "protein": "65-75g", "hydration": "2.0L", "meal_frequency": "3 mese + 2 gustari"},
            "meal_plan": [
                {"day": "Ziua 1 - Luni", "meals": [
                    {"meal": "Mic dejun", "time": "7:30-8:30", "items": ["Terci de ovaz cu miere si nuci - 250g", "1 portocala", "Ceai verde - 200ml"], "calories": "~380 kcal", "notes": "Ovazul ofera fibre solubile care reduc colesterolul", "recipe": "1. Fierbe 80g fulgi de ovaz in 250ml apa, 5 min. 2. Adauga 1 lingura miere si 30g nuci cernuti. 3. Serveste cu portocala feliata alaturi."},
                    {"meal": "Pranz", "time": "12:30-13:30", "items": ["Ciorba de linte cu legume - 350ml", "Paine integrala - 1 felie", "Salata de spanac cu seminte de dovleac - 150g"], "calories": "~520 kcal", "notes": "Lintea si spanacul sunt surse excelente de fier vegetal", "recipe": "1. Caleste ceapa, morcovul si telina tocate fin in 1 lingura ulei de masline. 2. Adauga 150g linte rosie spalata, 1L apa, sare, piper, boia. 3. Fierbe 25 min pana lintea e moale. 4. Stoarce lamaie la final. 5. Serveste cu paine integrala si salata de spanac."},
                    {"meal": "Cina", "time": "18:30-19:30", "items": ["Piept de pui la gratar - 150g", "Orez brun cu legume - 200g", "Salata de sfecla rosie - 100g"], "calories": "~480 kcal", "notes": "Sfecla rosie sustine productia de hemoglobina; puiul ofera fier hem", "recipe": "1. Marineaza pieptul de pui cu usturoi, lamaie, cimbru, 30 min. 2. Gratar 6-7 min pe fiecare parte. 3. Fierbe orezul brun 25 min, amesteca cu legume sotate. 4. Rade sfecla pe razatoare, condimenteaza cu ulei si otet."},
                ]},
                {"day": "Ziua 2 - Marti", "meals": [
                    {"meal": "Mic dejun", "time": "7:30-8:30", "items": ["2 oua ochiuri pe paine integrala", "Rosii cherry - 100g", "Suc de portocale proaspat - 200ml"], "calories": "~400 kcal", "notes": "Vitamina C din portocale creste absorbtia fierului din oua", "recipe": "1. Incinge tigaia cu putin ulei. 2. Sparge 2 oua, gateste 3-4 min la foc mediu. 3. Prajeste painea. 4. Serveste cu rosii si suc proaspat."},
                    {"meal": "Pranz", "time": "12:30-13:30", "items": ["Mancarica de mazare cu pui - 350g", "Mamaliga - 150g", "Salata de varza cu morcov - 150g"], "calories": "~550 kcal", "notes": "Mazarea ofera fier si proteine vegetale; puiul completeaza cu fier hem", "recipe": "1. Caleste ceapa tocata in ulei de masline. 2. Adauga 200g piept de pui taiat cubulere, soteaza 5 min. 3. Adauga 300g mazare, 200ml apa, sare, piper, boia dulce, marar. 4. Fierbe acoperit 20 min la foc mic. 5. Serveste cu mamaliga."},
                    {"meal": "Cina", "time": "18:30-19:30", "items": ["Somon la cuptor cu lamaie - 150g", "Cartofi copti cu rozmarin - 200g", "Broccoli la aburi - 150g"], "calories": "~500 kcal", "notes": "Somonul ofera omega-3 benefice pentru ochi si inima; broccoli sustine sanatatea oculara", "recipe": "1. Aseazoneaza somonul cu sare, piper, lamaie. 2. Coace la 200C, 18 min. 3. Cartofii taiati sferturi cu rozmarin si ulei, la cuptor 35 min. 4. Broccoli la aburi 5 min."},
                ]},
                {"day": "Ziua 3 - Miercuri", "meals": [
                    {"meal": "Mic dejun", "time": "7:30-8:30", "items": ["Smoothie cu spanac, banana si lapte de migdale - 350ml", "2 biscuiti integrali"], "calories": "~320 kcal", "notes": "Spanacul ofera fier si luteina pentru sanatatea ochilor", "recipe": "1. Blendeaza 50g spanac proaspat, 1 banana, 250ml lapte de migdale. 2. Adauga 1 lingurita miere. 3. Serveste imediat cu biscuitii."},
                    {"meal": "Pranz", "time": "12:30-13:30", "items": ["Tocanita de vita cu legume - 300g", "Paste integrale - 150g", "Salata verde cu castraveti - 100g"], "calories": "~580 kcal", "notes": "Carnea de vita este cea mai buna sursa de fier hem, usor absorbabil", "recipe": "1. Rumeniti 200g carne de vita taiata cuburi. 2. Adaugati ceapa, ardei, morcov, rosii. 3. Stingeti cu 100ml apa, boia, cimbru. 4. Inabusiti 45 min acoperit. 5. Fierbeti pastele separat."},
                    {"meal": "Cina", "time": "18:30-19:30", "items": ["Supa crema de dovleac - 300ml", "Paine integrala prajita cu branza de vaci - 2 felii", "Salata de morcovi cu lamaie - 100g"], "calories": "~420 kcal", "notes": "Dovleacul si morcovii sunt bogati in beta-caroten, benefic pentru vedere", "recipe": "1. Soteaza ceapa, adauga 500g dovleac taiat cuburi, 500ml supa. 2. Fierbe 20 min, blendeaza. 3. Condimenteaza cu nucsoara si smantana. 4. Intinde branza pe painea prajita."},
                ]},
                {"day": "Ziua 4 - Joi", "meals": [
                    {"meal": "Mic dejun", "time": "7:30-8:30", "items": ["Iaurt grecesc cu fructe de padure si granola - 300g", "Ceai de macese - 200ml"], "calories": "~370 kcal", "notes": "Fructele de padure contin antioxidanti pentru sanatatea oculara", "recipe": "1. Pune 200g iaurt grecesc in bol. 2. Adauga 80g mix de fructe de padure. 3. Presara 40g granola deasupra."},
                    {"meal": "Pranz", "time": "12:30-13:30", "items": ["Ardei umpluti cu carne si orez - 2 buc", "Smantana 10% - 2 linguri", "Salata de rosii cu ceapa - 150g"], "calories": "~560 kcal", "notes": "Ardeii sunt bogati in vitamina C care creste absorbtia fierului", "recipe": "1. Amesteca 250g carne tocata de vita cu 80g orez fiert, ceapa, marar, condimente. 2. Umple 4 ardei grasi. 3. Aseaza in oala cu sos de rosii. 4. Fierbe la foc mic 45 min acoperit."},
                    {"meal": "Cina", "time": "18:30-19:30", "items": ["Omleta cu spanac si telemea - 3 oua", "Paine integrala - 1 felie", "Salata de avocado - 100g"], "calories": "~450 kcal", "notes": "Spanacul cu oua ofera combinatie excelenta de fier si proteine", "recipe": "1. Bate 3 oua cu sare si piper. 2. Soteaza 50g spanac 2 min. 3. Toarna ouele, gateste 3 min. 4. Adauga 40g telemea sfaramata, pliaza."},
                ]},
                {"day": "Ziua 5 - Vineri", "meals": [
                    {"meal": "Mic dejun", "time": "7:30-8:30", "items": ["Paine integrala cu avocado si ou posat", "Rosii - 100g", "Ceai verde - 200ml"], "calories": "~390 kcal", "notes": "Avocado ofera grasimi sanatoase benefice cardiovascular", "recipe": "1. Prajeste painea. 2. Zdrobeste avocado cu sare si lamaie. 3. Poseaza oul 3 min in apa cu otet. 4. Asambleaza."},
                    {"meal": "Pranz", "time": "12:30-13:30", "items": ["Ciorba de fasole cu afumatura - 350ml", "Paine de casa - 1 felie", "Ceapa verde - 50g"], "calories": "~480 kcal", "notes": "Fasolea este bogata in fier vegetal si fibre care reduc colesterolul", "recipe": "1. Inmoaie 200g fasole peste noapte. 2. Fierbe cu morcov, telina, ceapa 1 ora. 3. Adauga 80g afumatura, rosii, boia. 4. Mai fierbe 20 min. 5. Adauga otet si leustean."},
                    {"meal": "Cina", "time": "18:30-19:30", "items": ["Pastrav la cuptor cu legume - 200g", "Spanac sotat cu usturoi - 150g", "Cartof copt - 1 buc"], "calories": "~470 kcal", "notes": "Pestele ofera omega-3 pentru sanatatea ochilor; spanacul completeaza fierul", "recipe": "1. Condimenteaza pastravul cu sare, lamaie, usturoi. 2. Aseaza pe pat de legume (ceapa, rosii, ardei). 3. Coace la 190C, 25 min. 4. Soteaza spanacul cu usturoi separat."},
                ]},
                {"day": "Ziua 6 - Sambata", "meals": [
                    {"meal": "Mic dejun", "time": "8:30-9:30", "items": ["Clatite integrale cu branza de vaci si dulceata - 3 buc", "Ceai de fructe - 200ml"], "calories": "~420 kcal", "notes": "Branza de vaci ofera proteine si calciu", "recipe": "1. Amesteca 100g faina integrala, 1 ou, 200ml lapte. 2. Coace 3 clatite subtiri. 3. Umple cu 150g branza de vaci si 2 linguri dulceata de fructe de padure."},
                    {"meal": "Pranz", "time": "13:00-14:00", "items": ["Sarmale in foi de varza - 3 buc", "Mamaliga - 150g", "Smantana - 2 linguri", "Ardei iute - 1 buc"], "calories": "~620 kcal", "notes": "Sarmalele ofera proteine complete; mamaliga sustine energia", "recipe": "1. Amesteca 300g carne tocata de porc+vita cu orez, ceapa, boia, cimbru. 2. Inveleste in foi de varza murata. 3. Aseaza in oala cu straturi de varza. 4. Fierbe acoperit la foc mic 2-3 ore. 5. Serveste cu mamaliga si smantana."},
                    {"meal": "Cina", "time": "19:00-20:00", "items": ["Supa de pui cu taitei de casa - 350ml", "Paine de casa - 1 felie"], "calories": "~380 kcal", "notes": "Supa de pui ofera proteine si minerale usor asimilabile", "recipe": "1. Fierbe 1 pulpa de pui cu legume (morcov, telina, pastarnac, ceapa) 1 ora. 2. Scoate puiul, desfa carnea. 3. Adauga taitei de casa, fierbe 10 min. 4. Adauga verdeata: patrunjel, leustean."},
                ]},
                {"day": "Ziua 7 - Duminica", "meals": [
                    {"meal": "Mic dejun", "time": "9:00-10:00", "items": ["Brunch: oua benedict cu spanac pe paine integrala", "Suc de sfecla si morcov - 200ml"], "calories": "~430 kcal", "notes": "Sucul de sfecla stimuleaza productia de hemoglobina", "recipe": "1. Poseaza 2 oua. 2. Soteaza spanac cu unt. 3. Prajeste painea. 4. Asambleaza: paine, spanac, ou posat, sos hollandaise light."},
                    {"meal": "Pranz", "time": "13:00-14:00", "items": ["Ghiveci de legume la cuptor - 350g", "Piept de curcan la gratar - 150g", "Salata de vinete cu rosii - 100g"], "calories": "~520 kcal", "notes": "Ghiveciul ofera varietate mare de vitamine si minerale", "recipe": "1. Taie cuburi: dovlecei, vinete, ardei, cartofi, ceapa, rosii. 2. Amesteca cu ulei de masline, usturoi, cimbru. 3. Coace la 200C, 40 min. 4. Gratar curcanul separat."},
                    {"meal": "Cina", "time": "18:30-19:30", "items": ["Salata Caesar cu piept de pui - 300g", "Crutoane integrale - 30g", "Parmezan ras - 20g"], "calories": "~420 kcal", "notes": "Salata verde contine luteina benefica pentru sanatatea ochilor", "recipe": "1. Gratar pieptul de pui, taie felii. 2. Amesteca salata romana cu sos Caesar light. 3. Adauga puiul, crutoane integrale, parmezan ras."},
                ]},
            ],
            "priority_foods": [
                {"category": "Alimente bogate in fier", "reason": "Combaterea anemiei feriprive", "foods": ["Carne rosie de vita", "Ficat de pui", "Linte", "Spanac", "Sfecla rosie", "Naut"], "target": "15-20mg fier/zi"},
                {"category": "Surse de Omega-3", "reason": "Sanatatea ochilor si reducerea inflamatiei", "foods": ["Somon", "Pastrav", "Sardine", "Nuci", "Seminte de in"], "target": "250-500mg EPA+DHA/zi"},
                {"category": "Alimente pentru vedere", "reason": "Sustinerea sanatatii oculare", "foods": ["Morcovi", "Spanac", "Dovleac", "Afine", "Oua (luteina)"], "target": "6-10mg luteina/zi"},
            ],
            "foods_to_reduce": [
                {"category": "Grasimi saturate", "reason": "Reducerea colesterolului LDL", "examples": ["Unt excesiv", "Carne grasa de porc", "Branzeturi grase"], "alternatives": ["Ulei de masline", "Carne slaba de pui/curcan", "Branza de vaci"]},
                {"category": "Dulciuri procesate", "reason": "Control glicemie si greutate", "examples": ["Prajituri", "Sucuri acidulate", "Ciocolata cu lapte"], "alternatives": ["Fructe proaspete", "Ciocolata neagra 70%+", "Miere cu moderatie"]},
            ],
            "supplements_to_discuss": [
                {"supplement": "Fier (Tardyferon/Sideralia)", "reason": "Corectia anemiei feriprive - Feritina 12 ng/mL", "note": "A se lua pe stomacul gol cu vitamina C"},
                {"supplement": "Vitamina D3 2000 UI/zi", "reason": "Valori limita - 32 ng/mL", "note": "De luat cu masa, preferabil cu grasimi"},
                {"supplement": "Omega-3 (ulei de peste)", "reason": "Sustinerea sanatatii oculare si cardiovasculare", "note": "1000mg/zi cu EPA+DHA"},
                {"supplement": "Luteina + Zeaxantina", "reason": "Protectia retinei - presiune intraoculara la limita", "note": "10mg luteina + 2mg zeaxantina/zi"},
            ],
            "shopping_list": [
                {"category": "Carne & Peste", "items": ["Piept de pui 1kg", "Carne de vita 500g", "Somon file 400g", "Pastrav 2 buc", "Carne tocata vita+porc 500g"]},
                {"category": "Legume", "items": ["Spanac 500g", "Sfecla rosie 4 buc", "Morcovi 1kg", "Dovleac 1 buc", "Broccoli 500g", "Rosii 1kg", "Ardei grasi 6 buc", "Varza murata 1 borcan"]},
                {"category": "Fructe", "items": ["Portocale 2kg", "Banane 1kg", "Afine/fructe de padure 300g", "Lamai 5 buc", "Avocado 3 buc"]},
                {"category": "Cereale & Leguminoase", "items": ["Fulgi de ovaz 500g", "Orez brun 500g", "Linte rosie 500g", "Paste integrale 500g", "Paine integrala", "Fasole uscata 500g"]},
                {"category": "Lactate", "items": ["Iaurt grecesc 500g", "Branza de vaci 400g", "Telemea 200g", "Smantana 10% 200ml", "Lapte de migdale 1L"]},
            ],
            "warnings": [
                "Anemia feripriva necesita monitorizare medicala - nu intrerupeti tratamentul cu fier fara consultarea medicului",
                "Presiunea intraoculara crescuta la ochiul stang necesita control oftalmologic regulat",
                "Consultati medicul inainte de a incepe suplimentele recomandate",
            ],
        }),
        risk_level="attention",
        created_at=now - timedelta(days=13),
        biomarkers_analyzed=33,
    )
    db.add(nutrition_report)

    # Exercise report (stored as full JSON in summary — expected format for lifestyle page)
    exercise_report = HealthReport(
        user_id=mother.id,
        report_type="exercise",
        title="Program de Exercitii Personalizat",
        summary=json.dumps({
            "summary": "Program de exercitii adaptat pentru gonartroza genunchi drept, imbunatatirea circulatiei (combaterea anemiei) si mentinerea sanatatii cardiovasculare. Accent pe kinetoterapie, exercitii de mobilitate si cardio moderat.",
            "current_assessment": {
                "activity_level": "Sedentara - activitate fizica usoara",
                "exercise_readiness": "Moderata - necesita adaptare pentru gonartroza",
                "key_health_factors": ["Gonartroza genunchi drept", "Anemie feripriva", "Colesterol usor crescut", "Presiune intraoculara la limita"]
            },
            "weekly_schedule": [
                {"day": "Luni", "focus": "Kinetoterapie genunchi + Cardio", "total_duration": "45 min", "warmup": {"duration": "10 min", "exercises": [
                    "Mers pe loc - 3 min, ritm moderat",
                    "Rotatii glezne si genunchi - 3 min, miscari lente",
                    "Stretching usor membre inferioare - 4 min"
                ]}, "main_workout": [
                    {"exercise": "Extensii de genunchi sezand", "sets_reps": "3x12", "rest": "60s", "duration": "", "biomarker_benefit": "Intarire cvadriceps - protectie gonartroza", "details": "Greutate mica sau fara greutate"},
                    {"exercise": "Ridicari de sold (bridge)", "sets_reps": "3x15", "rest": "45s", "duration": "", "biomarker_benefit": "Stabilitate genunchi si sold", "details": "Mentin 3 sec sus"},
                    {"exercise": "Mers pe bicicleta statica", "sets_reps": "", "rest": "", "duration": "15 min", "biomarker_benefit": "Cardio fara impact pe genunchi, circulatie", "details": "Rezistenta mica, ritm constant"},
                    {"exercise": "Flexii cu banda elastica", "sets_reps": "2x10", "rest": "45s", "duration": "", "biomarker_benefit": "Flexibilitate genunchi", "details": "Banda usoara"},
                ], "cooldown": {"duration": "5 min", "exercises": [
                    "Stretching cvadriceps - 2 min, tin 20s fiecare picior",
                    "Respiratii profunde - 3 min, relaxare completa"
                ]}},
                {"day": "Marti", "focus": "Cardio moderat + Tonifiere", "total_duration": "45 min", "warmup": {"duration": "8 min", "exercises": [
                    "Mers pe loc cu balansare brate - 3 min",
                    "Rotatii umeri si gat - 2 min",
                    "Flexii usoare trunchi - 3 min"
                ]}, "main_workout": [
                    {"exercise": "Plimbare in aer liber", "sets_reps": "", "rest": "", "duration": "30 min", "biomarker_benefit": "Cardio, circulatie, vitamina D", "details": "Pas alert dar confortabil"},
                    {"exercise": "Exercitii brate cu gantere mici", "sets_reps": "2x12", "rest": "45s", "duration": "", "biomarker_benefit": "Tonifiere generala", "details": "1-2 kg gantere"},
                ], "cooldown": {"duration": "5 min", "exercises": [
                    "Stretching general - 5 min, tot corpul"
                ]}},
                {"day": "Miercuri", "focus": "Kinetoterapie + Inot", "total_duration": "50 min", "warmup": {"duration": "10 min", "exercises": [
                    "Mers pe loc - 3 min",
                    "Mobilizare articulara - 4 min, accent pe genunchi",
                    "Balans pe un picior - 3 min, cu sprijin pe scaun"
                ]}, "main_workout": [
                    {"exercise": "Extensii izometrice genunchi", "sets_reps": "3x10", "rest": "60s", "duration": "", "biomarker_benefit": "Intarire musculatura periarticulara", "details": "Tin 5s contractia"},
                    {"exercise": "Step lateral cu banda elastica", "sets_reps": "3x12", "rest": "45s", "duration": "", "biomarker_benefit": "Stabilitate laterala genunchi", "details": "Pasi mici, controlati"},
                    {"exercise": "Inot sau aquagym", "sets_reps": "", "rest": "", "duration": "20 min", "biomarker_benefit": "Cardio fara impact, mobilitate articulara", "details": "Ideal pentru gonartroza"},
                ], "cooldown": {"duration": "5 min", "exercises": [
                    "Stretching in apa sau pe saltea - 5 min"
                ]}},
                {"day": "Joi", "focus": "Recuperare activa - Yoga", "total_duration": "35 min", "warmup": {"duration": "5 min", "exercises": [
                    "Respiratii si stretching usor - 5 min"
                ]}, "main_workout": [
                    {"exercise": "Yoga adaptata / stretching", "sets_reps": "", "rest": "", "duration": "25 min", "biomarker_benefit": "Flexibilitate, reducere stres, tensiune arteriala", "details": "Pozitii adaptate, evita presiune pe genunchi"},
                ], "cooldown": {"duration": "5 min", "exercises": [
                    "Meditatie si respiratie - 5 min, relaxare profunda"
                ]}},
                {"day": "Vineri", "focus": "Forta + Cardio interval", "total_duration": "45 min", "warmup": {"duration": "10 min", "exercises": [
                    "Mers pe loc - 3 min",
                    "Mobilizare completa articulatii - 4 min",
                    "Rotatii trunchi - 3 min"
                ]}, "main_workout": [
                    {"exercise": "Genuflexiuni partiale la perete", "sets_reps": "3x10", "rest": "60s", "duration": "", "biomarker_benefit": "Intarire cvadriceps si fesieri", "details": "Nu cobori sub 90 grade"},
                    {"exercise": "Ridicari pe varfuri", "sets_reps": "3x15", "rest": "30s", "duration": "", "biomarker_benefit": "Circulatie periferica, echilibru", "details": "Cu sprijin pe scaun"},
                    {"exercise": "Bicicleta statica", "sets_reps": "", "rest": "", "duration": "15 min", "biomarker_benefit": "Cardio, reducere colesterol", "details": "Interval: 2 min moderat, 1 min rapid"},
                ], "cooldown": {"duration": "5 min", "exercises": [
                    "Stretching complet - 5 min, accent pe membre inferioare"
                ]}},
                {"day": "Sambata", "focus": "Plimbare lunga in natura", "total_duration": "55 min", "warmup": {"duration": "5 min", "exercises": [
                    "Stretching usor - 5 min"
                ]}, "main_workout": [
                    {"exercise": "Plimbare lunga in natura", "sets_reps": "", "rest": "", "duration": "45 min", "biomarker_benefit": "Cardio, vitamina D, bunastare mentala", "details": "Teren plat, evita pantele abrupte"},
                ], "cooldown": {"duration": "5 min", "exercises": [
                    "Stretching si hidratare - 5 min"
                ]}},
                {"day": "Duminica", "focus": "Odihna si recuperare", "total_duration": "15-20 min", "warmup": {"duration": "0 min", "exercises": []}, "main_workout": [
                    {"exercise": "Zi de odihna activa", "sets_reps": "", "rest": "", "duration": "15-20 min", "biomarker_benefit": "Recuperare musculara si articulara", "details": "Plimbare usoara daca se simte bine, altfel odihna completa"},
                ], "cooldown": {"duration": "0 min", "exercises": []}},
            ],
        }),
        risk_level="normal",
        created_at=now - timedelta(days=13),
        biomarkers_analyzed=33,
    )
    db.add(exercise_report)

    # Gap analysis / screening recommendations
    mother_gap_tests = [
        {"test_name": "Hemoleucograma completa + Feritina", "category": "Hematologie", "priority": "high", "reason": "Monitorizare anemie feripriva in tratament - Hb 11.8, Feritina 12", "frequency": "La 3 luni", "recommended_interval_months": 3, "is_overdue": False, "last_done_date": (now - timedelta(days=14)).isoformat(), "months_since_last": 0},
        {"test_name": "Examen oftalmologic complet (tonometrie + fund de ochi)", "category": "Oftalmologie", "priority": "high", "reason": "Presiune intraoculara crescuta OS (22 mmHg) - risc glaucom", "frequency": "La 3 luni", "recommended_interval_months": 3, "is_overdue": True, "last_done_date": (now - timedelta(days=90)).isoformat(), "months_since_last": 3},
        {"test_name": "Profil lipidic complet", "category": "Cardiovascular", "priority": "medium", "reason": "Colesterol total 215, LDL 138 - monitorizare dupa modificari dieta", "frequency": "La 6 luni", "recommended_interval_months": 6, "is_overdue": False, "last_done_date": (now - timedelta(days=178)).isoformat(), "months_since_last": 6},
        {"test_name": "Mamografie bilaterala", "category": "Cancer", "priority": "medium", "reason": "Screening cancer san - femeie 40 ani, recomandare ghid national", "frequency": "Anual", "recommended_interval_months": 12, "is_overdue": True, "last_done_date": None, "months_since_last": None},
        {"test_name": "Test Babes-Papanicolau", "category": "Cancer", "priority": "medium", "reason": "Screening cancer col uterin - recomandare ghid national", "frequency": "La 3 ani", "recommended_interval_months": 36, "is_overdue": True, "last_done_date": None, "months_since_last": None},
        {"test_name": "Ecografie abdominala", "category": "General", "priority": "low", "reason": "Screening general organe abdominale", "frequency": "Anual", "recommended_interval_months": 12, "is_overdue": True, "last_done_date": None, "months_since_last": None},
        {"test_name": "EKG (electrocardiograma)", "category": "Cardiovascular", "priority": "low", "reason": "Screening cardiovascular de baza - profil lipidic usor crescut", "frequency": "Anual", "recommended_interval_months": 12, "is_overdue": True, "last_done_date": None, "months_since_last": None},
        {"test_name": "Densitometrie osoasa (DEXA)", "category": "General", "priority": "low", "reason": "Evaluare densitate osoasa - femeie cu gonartroza", "frequency": "La 2 ani", "recommended_interval_months": 24, "is_overdue": True, "last_done_date": None, "months_since_last": None},
    ]
    gap_report = HealthReport(
        user_id=mother.id,
        report_type="gap_analysis",
        title="Screeninguri Recomandate",
        summary="Bazat pe profilul dvs. medical si rezultatele analizelor, va recomandam urmatoarele investigatii pentru monitorizarea completa a sanatatii.",
        findings=json.dumps(mother_gap_tests),
        recommendations=json.dumps([]),
        risk_level="attention",
        created_at=now - timedelta(days=13),
        biomarkers_analyzed=33,
    )
    db.add(gap_report)

    print(f"Created mother data: 4 documents, {10+15+4+8} biomarkers, 4 reports.")

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
        ("Fier seric", "Fier seric", "45", 45.0, "ug/dL", "50-120", "LOW", "Hematologie"),
        ("Feritina", "Feritina", "15", 15.0, "ng/mL", "20-200", "LOW", "Hematologie"),
        ("Leucocite (WBC)", "Leucocite", "8.2", 8.2, "x10^3/uL", "4.5-13.5", "NORMAL", "Hematologie"),
        ("Eozinofile", "Eozinofile", "8.5", 8.5, "%", "1-5", "HIGH", "Hematologie"),
        ("IgE total", "IgE total", "385", 385.0, "UI/mL", "<100", "HIGH", "Imunologie"),
        ("Vitamina D (25-OH)", "Vitamina D", "18", 18.0, "ng/mL", "30-100", "LOW", "Vitamine"),
        ("Calciu total", "Calciu total", "9.0", 9.0, "mg/dL", "8.8-10.8", "NORMAL", "Minerale"),
        ("Fosfataza alcalina", "Fosfataza alcalina", "320", 320.0, "U/L", "100-390", "NORMAL", "Metabolism osos"),
        ("Glicemie", "Glicemie", "82", 82.0, "mg/dL", "70-100", "NORMAL", "Metabolism"),
        ("TSH", "TSH", "3.1", 3.1, "mUI/L", "0.7-5.7", "NORMAL", "Tiroida"),
    ]

    for name, canonical, val, num, unit, ref, flag, cat in biomarkers_doc1:
        db.add(TestResult(document_id=doc1.id, test_name=name, canonical_name=canonical,
                          value=val, numeric_value=num, unit=unit, reference_range=ref, flags=flag, category=cat))
    create_pdf_for_document(son.id, doc1, biomarkers_doc1)

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
    create_pdf_for_document(son.id, doc2, biomarkers_doc2)

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
        ("Rotatie vertebrala", "Rotatie vertebrala", "1", 1.0, "grad Nash-Moe", "0", "HIGH", "Ortopedic"),
    ]

    for name, canonical, val, num, unit, ref, flag, cat in biomarkers_doc3:
        db.add(TestResult(document_id=doc3.id, test_name=name, canonical_name=canonical,
                          value=val, numeric_value=num, unit=unit, reference_range=ref, flags=flag, category=cat))
    create_pdf_for_document(son.id, doc3, biomarkers_doc3)

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
        ("Fier seric", "Fier seric", "52", 52.0, "ug/dL", "50-120", "NORMAL", "Hematologie"),
        ("Feritina", "Feritina", "18", 18.0, "ng/mL", "20-200", "LOW", "Hematologie"),
        ("Vitamina D (25-OH)", "Vitamina D", "22", 22.0, "ng/mL", "30-100", "LOW", "Vitamine"),
        ("Eozinofile", "Eozinofile", "7.2", 7.2, "%", "1-5", "HIGH", "Hematologie"),
        ("IgE total", "IgE total", "350", 350.0, "UI/mL", "<100", "HIGH", "Imunologie"),
        ("Leucocite (WBC)", "Leucocite", "7.8", 7.8, "x10^3/uL", "4.5-13.5", "NORMAL", "Hematologie"),
        ("Calciu total", "Calciu total", "9.2", 9.2, "mg/dL", "8.8-10.8", "NORMAL", "Minerale"),
    ]

    for name, canonical, val, num, unit, ref, flag, cat in biomarkers_doc4:
        db.add(TestResult(document_id=doc4.id, test_name=name, canonical_name=canonical,
                          value=val, numeric_value=num, unit=unit, reference_range=ref, flags=flag, category=cat))
    create_pdf_for_document(son.id, doc4, biomarkers_doc4)

    # --- Health Reports ---
    son_findings = [
        {"category": "Vitamina D", "status": "concern", "explanation": "Deficit persistent de vitamina D - 22 ng/mL (anterior 18 ng/mL). Ameliorare usoara sub suplimentare, dar inca sub valoarea optima de 30 ng/mL. Critic pentru cresterea osoasa la aceasta varsta.", "markers": ["Vitamina D"]},
        {"category": "Hematologie", "status": "attention", "explanation": "Feritina 18 ng/mL (limita inferioara, sub 20). Fierul seric s-a normalizat la 52 ug/dL. Risc de anemie feripriva daca nu se mentine aportul.", "markers": ["Feritina", "Fier seric"]},
        {"category": "Alergologie", "status": "attention", "explanation": "Alergii multiple confirmate: acarieni (IgE 45.2), ambrozie (28.7), polen graminee (12.5), intoleranta lactoza (8.3). IgE total ridicat (350 UI/mL). Eozinofile crescute (7.2%).", "markers": ["IgE total", "Eozinofile", "IgE Acarieni", "IgE Ambrozie"]},
        {"category": "Ortopedic", "status": "concern", "explanation": "Scolioza toracica cu unghi Cobb 18 grade - forma moderata. Rotatie vertebrala grad 1 Nash-Moe. Necesita kinetoterapie specifica si monitorizare la 6 luni. Nu necesita corset la acest grad.", "markers": ["Unghi Cobb", "Rotatie vertebrala"]},
        {"category": "Metabolism", "status": "normal", "explanation": "Glicemie normala (82 mg/dL), TSH normal (3.1 mUI/L), calciu normal. Crestere si dezvoltare in parametri normali.", "markers": ["Glicemie", "TSH", "Calciu total"]},
    ]
    son_recommendations = [
        {"action": "Vitamina D3 suplimentar 2000 UI/zi", "reason": "Deficit persistent (22 ng/mL) - critic pentru cresterea osoasa. Control la 3 luni pentru ajustare doza", "priority": "high"},
        {"action": "Kinetoterapie specifica scolioza 3x/saptamana", "reason": "Exercitii Schroth sau SEAS pentru corectia scoliozei toracice (Cobb 18 grade)", "priority": "high"},
        {"action": "Dieta bogata in fier", "reason": "Carne rosie 2-3x/saptamana, leguminoase, spanac - Feritina la limita inferioara (18 ng/mL)", "priority": "medium"},
        {"action": "Evitare lactate din lapte de vaca", "reason": "Intoleranta lactoza confirmata (IgE 8.3) - inlocuire cu alternative (lapte de migdale, soia)", "priority": "medium"},
        {"action": "Aerius 5mg continuat in sezon alergic", "reason": "Alergii multiple confirmate. Consultare alergolog pentru evaluare imunoterapie specifica", "priority": "medium"},
        {"action": "Control ortopedic cu radiografie la 6 luni", "reason": "Monitorizare unghi Cobb in perioada de crestere rapida - risc de progresie", "priority": "high"},
        {"action": "Activitate fizica regulata: inot, exercitii de postura", "reason": "Intarire musculatura spatelui, evitare sporturi cu impact asimetric", "priority": "low"},
    ]
    general_report = HealthReport(
        user_id=son.id,
        report_type="general",
        title="Evaluare Generala Sanatate",
        summary="Pacientul pediatric prezinta deficit de vitamina D persistent, depozite de fier la limita inferioara, alergii multiple (acarieni, ambrozie, lactoza) si scolioza toracica moderata (unghi Cobb 18 grade) necesitand kinetoterapie activa.",
        findings=json.dumps(son_findings),
        recommendations=json.dumps(son_recommendations),
        risk_level="attention",
        created_at=now - timedelta(days=6),
        biomarkers_analyzed=28,
    )
    db.add(general_report)

    # Son exercise report
    son_exercise_report = HealthReport(
        user_id=son.id,
        report_type="exercise",
        title="Program de Exercitii - Scolioza si Dezvoltare",
        summary=json.dumps({
            "summary": "Program de exercitii adaptat pentru scolioza toracica (Cobb 18 grade), dezvoltare osoasa sanatoasa si gestionarea alergiilor. Accent pe exercitii Schroth pentru scolioza, activitati de intarire musculatura spatelui si inot.",
            "current_assessment": {
                "activity_level": "Moderata - copil activ dar necesita exercitii specifice",
                "exercise_readiness": "Buna - fara contraindicatii majore",
                "key_health_factors": ["Scolioza toracica moderata (Cobb 18)", "Deficit vitamina D", "Alergii respiratorii", "Depozite fier scazute"]
            },
            "weekly_schedule": [
                {"day": "Luni", "focus": "Schroth + Inot", "total_duration": "55 min", "warmup": {"duration": "10 min", "exercises": [
                    "Mers pe loc cu balansare brate - 3 min",
                    "Rotatii trunchi si umeri - 3 min, miscari lente",
                    "Cat-Cow stretch - 4 min, mobilizare coloana"
                ]}, "main_workout": [
                    {"exercise": "Exercitii Schroth - autoelongare", "sets_reps": "3x10", "rest": "60s", "duration": "", "biomarker_benefit": "Corectie posturala activa scolioza", "details": "Concentrare pe respiratie 3D"},
                    {"exercise": "Plank lateral (partea concava)", "sets_reps": "3x20s", "rest": "45s", "duration": "", "biomarker_benefit": "Intarire musculatura asimetrica", "details": "Doar pe partea recomandata de kinetoterapeut"},
                    {"exercise": "Inot - stil craul", "sets_reps": "", "rest": "", "duration": "30 min", "biomarker_benefit": "Intarire simetrica spate, fara compresie vertebrala", "details": "Cel mai benefic sport pentru scolioza"},
                ], "cooldown": {"duration": "5 min", "exercises": [
                    "Stretching spate si umeri - 5 min, pozitia copilului"
                ]}},
                {"day": "Marti", "focus": "Cardio + Core", "total_duration": "40 min", "warmup": {"duration": "8 min", "exercises": [
                    "Sarituri usoare pe loc - 3 min, impact redus",
                    "Rotatii articulare - 2 min",
                    "Stretching dinamic - 3 min"
                ]}, "main_workout": [
                    {"exercise": "Alergare usoara in aer liber", "sets_reps": "", "rest": "", "duration": "20 min", "biomarker_benefit": "Cardio, vitamina D din soare, circulatie", "details": "Evitare in sezon de polen ridicat - alternativa: sala"},
                    {"exercise": "Exercitii abdominale adaptate", "sets_reps": "3x12", "rest": "45s", "duration": "", "biomarker_benefit": "Stabilitate core pentru coloana", "details": "Bird-dog si dead bug, evita sit-ups clasice"},
                ], "cooldown": {"duration": "5 min", "exercises": [
                    "Stretching general - 5 min"
                ]}},
                {"day": "Miercuri", "focus": "Schroth + Inot spate", "total_duration": "55 min", "warmup": {"duration": "10 min", "exercises": [
                    "Mers pe loc - 3 min",
                    "Cat-Cow stretch - 3 min",
                    "Respiratie diafragmatica - 4 min, pregatire Schroth"
                ]}, "main_workout": [
                    {"exercise": "Exercitii Schroth - corectie rotatie", "sets_reps": "3x8", "rest": "60s", "duration": "", "biomarker_benefit": "Reducere rotatie vertebrala", "details": "Sub indrumarea kinetoterapeutului"},
                    {"exercise": "Ridicari laterale cu banda elastica", "sets_reps": "2x10", "rest": "45s", "duration": "", "biomarker_benefit": "Intarire musculatura paravertebrala", "details": "Banda usoara"},
                    {"exercise": "Inot - stil spate", "sets_reps": "", "rest": "", "duration": "25 min", "biomarker_benefit": "Extensie coloana, intarire spate", "details": "Alterneza cu crawl"},
                ], "cooldown": {"duration": "5 min", "exercises": [
                    "Stretching in apa - 5 min"
                ]}},
                {"day": "Joi", "focus": "Cardio usor + Echilibru", "total_duration": "40 min", "warmup": {"duration": "5 min", "exercises": [
                    "Stretching usor - 5 min"
                ]}, "main_workout": [
                    {"exercise": "Bicicleta (statica sau in aer liber)", "sets_reps": "", "rest": "", "duration": "25 min", "biomarker_benefit": "Cardio fara impact pe coloana", "details": "Postura corecta pe bicicleta"},
                    {"exercise": "Exercitii echilibru pe placa instabila", "sets_reps": "3x2min", "rest": "30s", "duration": "", "biomarker_benefit": "Proprioceptie, stabilitate core", "details": "Cu supraveghere"},
                ], "cooldown": {"duration": "5 min", "exercises": [
                    "Stretching si relaxare - 5 min"
                ]}},
                {"day": "Vineri", "focus": "Schroth complet + Plank", "total_duration": "40 min", "warmup": {"duration": "10 min", "exercises": [
                    "Mers pe loc - 3 min",
                    "Mobilizare articulara completa - 4 min",
                    "Respiratie Schroth 3D - 3 min"
                ]}, "main_workout": [
                    {"exercise": "Exercitii Schroth - program complet", "sets_reps": "3x10", "rest": "60s", "duration": "", "biomarker_benefit": "Sesiune completa corectie scolioza", "details": "Autoelongare + corectie rotatie + respiratie"},
                    {"exercise": "Plank frontal", "sets_reps": "3x30s", "rest": "45s", "duration": "", "biomarker_benefit": "Stabilitate core globala", "details": "Pozitie corecta, fara arcuire lombara"},
                ], "cooldown": {"duration": "5 min", "exercises": [
                    "Stretching complet - 5 min, accent pe spate si umeri"
                ]}},
                {"day": "Sambata", "focus": "Sport recreativ", "total_duration": "55 min", "warmup": {"duration": "5 min", "exercises": [
                    "Stretching dinamic - 5 min"
                ]}, "main_workout": [
                    {"exercise": "Sport recreativ (badminton, tenis de masa)", "sets_reps": "", "rest": "", "duration": "45 min", "biomarker_benefit": "Coordonare, socializare, distractie", "details": "Sporturi cu impact simetric, evitare tenis clasic"},
                ], "cooldown": {"duration": "5 min", "exercises": [
                    "Stretching si hidratare - 5 min"
                ]}},
                {"day": "Duminica", "focus": "Odihna si recuperare", "total_duration": "20-30 min", "warmup": {"duration": "0 min", "exercises": []}, "main_workout": [
                    {"exercise": "Zi de odihna activa", "sets_reps": "", "rest": "", "duration": "20-30 min", "biomarker_benefit": "Recuperare musculara", "details": "Plimbare 20-30 min cu familia, jocuri in aer liber"},
                ], "cooldown": {"duration": "0 min", "exercises": []}},
            ],
        }),
        risk_level="normal",
        created_at=now - timedelta(days=6),
        biomarkers_analyzed=28,
    )
    db.add(son_exercise_report)

    # Son gap analysis
    son_gap_tests = [
        {"test_name": "Vitamina D (25-OH) + Calciu + Fosfataza alcalina", "category": "Metabolism osos", "priority": "high", "reason": "Deficit vitamina D persistent (22 ng/mL) - critic pentru dezvoltare osoasa", "frequency": "La 3 luni", "recommended_interval_months": 3, "is_overdue": False, "last_done_date": (now - timedelta(days=7)).isoformat(), "months_since_last": 0},
        {"test_name": "Radiografie coloana + evaluare ortopedica", "category": "Ortopedic", "priority": "high", "reason": "Monitorizare scolioza toracica (Cobb 18) in perioada de crestere rapida", "frequency": "La 6 luni", "recommended_interval_months": 6, "is_overdue": False, "last_done_date": (now - timedelta(days=60)).isoformat(), "months_since_last": 2},
        {"test_name": "Hemoleucograma + Feritina + Fier seric", "category": "Hematologie", "priority": "medium", "reason": "Feritina la limita inferioara (18 ng/mL) - monitorizare depozite fier", "frequency": "La 3 luni", "recommended_interval_months": 3, "is_overdue": False, "last_done_date": (now - timedelta(days=7)).isoformat(), "months_since_last": 0},
        {"test_name": "Teste cutanate prick alergologice", "category": "Alergologie", "priority": "medium", "reason": "Alergii multiple - evaluare anuala si discutie imunoterapie", "frequency": "Anual", "recommended_interval_months": 12, "is_overdue": False, "last_done_date": (now - timedelta(days=148)).isoformat(), "months_since_last": 5},
        {"test_name": "Consult alergologie - imunoterapie specifica", "category": "Alergologie", "priority": "medium", "reason": "IgE total 350, alergii multiple - candidat pentru imunoterapie sublinguala", "frequency": "Anual", "recommended_interval_months": 12, "is_overdue": True, "last_done_date": None, "months_since_last": None},
        {"test_name": "Spirometrie", "category": "Pneumologie", "priority": "low", "reason": "Screening functie pulmonara - rinita alergica, risc astm", "frequency": "Anual", "recommended_interval_months": 12, "is_overdue": True, "last_done_date": None, "months_since_last": None},
        {"test_name": "Control oftalmologic", "category": "Oftalmologie", "priority": "low", "reason": "Screening vedere - varsta scolara", "frequency": "Anual", "recommended_interval_months": 12, "is_overdue": True, "last_done_date": None, "months_since_last": None},
    ]
    son_gap_report = HealthReport(
        user_id=son.id,
        report_type="gap_analysis",
        title="Screeninguri Recomandate",
        summary="Bazat pe profilul medical al copilului si rezultatele analizelor, se recomanda urmatoarele investigatii pentru monitorizarea completa a sanatatii si dezvoltarii.",
        findings=json.dumps(son_gap_tests),
        recommendations=json.dumps([]),
        risk_level="attention",
        created_at=now - timedelta(days=6),
        biomarkers_analyzed=28,
    )
    db.add(son_gap_report)

    print(f"Created son data: 4 documents, {12+6+2+8} biomarkers, 3 reports.")

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

    # Subscriptions
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

    # Food preferences
    import hashlib
    def add_food_pref(user_id, name, pref):
        h = hashlib.sha256(name.lower().strip().encode()).hexdigest()
        db.add(FoodPreference(user_id=user_id, food_name_hash=h, food_name=name, preference=pref, source="meal_plan"))

    add_food_pref(mother.id, "Spanac", "liked")
    add_food_pref(mother.id, "Somon", "liked")
    add_food_pref(mother.id, "Linte", "liked")
    add_food_pref(mother.id, "Sfecla rosie", "liked")
    add_food_pref(mother.id, "Broccoli", "liked")
    add_food_pref(mother.id, "Ficat", "disliked")
    add_food_pref(mother.id, "Sardine", "disliked")

    add_food_pref(son.id, "Piept de pui", "liked")
    add_food_pref(son.id, "Orez", "liked")
    add_food_pref(son.id, "Banane", "liked")
    add_food_pref(son.id, "Broccoli", "disliked")
    add_food_pref(son.id, "Spanac", "disliked")
    add_food_pref(son.id, "Peste", "disliked")

    # Medications
    db.add(Medication(user_id=mother.id, name="Tardyferon", dosage="80mg fier", frequency="daily",
                      time_of_day="morning", notes="Pe stomacul gol, cu suc de portocale", is_active=True))
    db.add(Medication(user_id=mother.id, name="Vitamina D3", dosage="2000 UI", frequency="daily",
                      time_of_day="morning", notes="Cu micul dejun", is_active=True))
    db.add(Medication(user_id=mother.id, name="Ocuvit Plus", dosage="1 comprimat", frequency="daily",
                      time_of_day="evening", notes="Luteina + Zeaxantina pentru ochi", is_active=True))
    db.add(Medication(user_id=mother.id, name="Ibuprofen", dosage="400mg", frequency="as_needed",
                      time_of_day=None, notes="La nevoie pentru dureri genunchi", is_active=True))

    db.add(Medication(user_id=son.id, name="Vitamina D3", dosage="2000 UI", frequency="daily",
                      time_of_day="morning", notes="Cu micul dejun", is_active=True))
    db.add(Medication(user_id=son.id, name="Aerius", dosage="5mg", frequency="daily",
                      time_of_day="evening", notes="Antialergic - sezon alergic", is_active=True))
    db.add(Medication(user_id=son.id, name="Calcium + Vitamina K2", dosage="500mg Ca", frequency="daily",
                      time_of_day="evening", notes="Pentru dezvoltare osoasa", is_active=True))

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
