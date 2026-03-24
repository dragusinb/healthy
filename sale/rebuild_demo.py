#!/usr/bin/env python3
"""
Rebuild demo accounts from scratch with proper per-user vault encryption.

Run on server:
  cd /opt/healthy && source backend_v2/venv/bin/activate && \
  set -a && source backend_v2/.env && set +a && \
  PYTHONPATH=/opt/healthy python3 sale/rebuild_demo.py
"""
import sys
import os

# Ensure backend_v2 is importable
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend_v2'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
import uuid
import shutil
import hashlib
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend_v2', '.env')
load_dotenv(env_path)

# Import models
from backend_v2.models import (
    User, LinkedAccount, Document, TestResult, HealthReport,
    FamilyGroup, FamilyMember, Subscription, UsageTracker,
    NotificationPreference, FoodPreference, Medication, MedicationLog,
    Notification, SyncJob, AuditLog, UserSession, AbuseFlag,
    UsageMetrics, OpenAIUsageLog, PushSubscription, SharedReport,
    SupportTicket, SupportTicketReply, SupportTicketAttachment,
    PaymentHistory, RateLimitCounter
)
from backend_v2.services.user_vault import UserVault, set_user_vault_session
from backend_v2.auth.security import get_password_hash

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://healthy_user:healthy_pass_2024@localhost/healthy_db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

# Config
MOTHER_EMAIL = "elena.popescu@demo.analize.online"
SON_EMAIL = "andrei.popescu@demo.analize.online"
PASSWORD = "DemoPass123!"


def utc_now():
    return datetime.now(timezone.utc)


# ============================================================
# PDF generation (minimal valid PDFs, no external libs)
# ============================================================
def _pdf_escape(text):
    diacritics = {
        'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
        'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T',
        'ü': 'u', 'ö': 'o', 'ä': 'a', 'é': 'e', 'è': 'e',
        '—': '-', '–': '-', '°': 'o', '³': '3', '⁶': '6',
        'μ': 'u', '±': '+/-'
    }
    for k, v in diacritics.items():
        text = text.replace(k, v)
    return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def generate_minimal_pdf(title, patient_name, date_str, lines):
    text_objects = []
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

    objects = []
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj")
    objects.append(f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj")
    objects.append(f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n{stream_content}\nendstream\nendobj")
    objects.append("5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj")

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


def create_pdf_on_disk(user_id, doc, biomarkers):
    """Create a PDF file on disk and set file_path on the document."""
    base_dir = Path(os.path.dirname(os.path.abspath(__file__))) / '..' / 'backend_v2' / 'data' / 'raw' / str(user_id)
    # On server, use /opt/healthy/backend_v2/data/raw/
    if os.path.exists('/opt/healthy'):
        base_dir = Path('/opt/healthy/backend_v2/data/raw') / str(user_id)
    base_dir.mkdir(parents=True, exist_ok=True)

    date_str = doc.document_date.strftime("%d.%m.%Y") if doc.document_date else "N/A"
    lines = []
    for name, canonical, val, num, unit, ref, flag, cat in biomarkers:
        flag_marker = " *" if flag != "NORMAL" else ""
        lines.append(f"{name}: {val} {unit}  (ref: {ref}) [{flag}]{flag_marker}")
    if not lines:
        lines = ["Document fara rezultate numerice."]

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
# THOROUGH CLEANUP
# ============================================================
def cleanup():
    """Delete ALL data for demo accounts across ALL tables."""
    print("--- Cleanup: deleting all demo data ---")
    for email in [MOTHER_EMAIL, SON_EMAIL]:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"  User {email} not found, skipping.")
            continue

        uid = user.id
        print(f"  Deleting data for {email} (ID: {uid})...")

        # MedicationLog (FK to medications AND users)
        db.query(MedicationLog).filter(MedicationLog.user_id == uid).delete()

        # Medications
        db.query(Medication).filter(Medication.user_id == uid).delete()

        # Food preferences
        db.query(FoodPreference).filter(FoodPreference.user_id == uid).delete()

        # Family: delete all members from owned groups, then own membership, then groups
        owned_groups = db.query(FamilyGroup).filter(FamilyGroup.owner_id == uid).all()
        for grp in owned_groups:
            db.query(FamilyMember).filter(FamilyMember.family_id == grp.id).delete()
        db.query(FamilyMember).filter(FamilyMember.user_id == uid).delete()
        db.query(FamilyGroup).filter(FamilyGroup.owner_id == uid).delete()

        # Notifications
        db.query(Notification).filter(Notification.user_id == uid).delete()
        db.query(NotificationPreference).filter(NotificationPreference.user_id == uid).delete()

        # Push subscriptions
        db.query(PushSubscription).filter(PushSubscription.user_id == uid).delete()

        # Subscriptions & payment
        db.query(Subscription).filter(Subscription.user_id == uid).delete()
        db.query(PaymentHistory).filter(PaymentHistory.user_id == uid).delete()

        # Usage
        db.query(UsageTracker).filter(UsageTracker.user_id == uid).delete()
        db.query(UsageMetrics).filter(UsageMetrics.user_id == uid).delete()

        # Audit & security
        db.query(AuditLog).filter(AuditLog.user_id == uid).delete()
        db.query(UserSession).filter(UserSession.user_id == uid).delete()
        db.query(AbuseFlag).filter(AbuseFlag.user_id == uid).delete()

        # OpenAI usage
        db.query(OpenAIUsageLog).filter(OpenAIUsageLog.user_id == uid).delete()

        # Support tickets: attachments -> replies -> tickets
        tickets = db.query(SupportTicket).filter(SupportTicket.reporter_id == uid).all()
        for t in tickets:
            db.query(SupportTicketAttachment).filter(SupportTicketAttachment.ticket_id == t.id).delete()
            db.query(SupportTicketReply).filter(SupportTicketReply.ticket_id == t.id).delete()
        db.query(SupportTicket).filter(SupportTicket.reporter_id == uid).delete()

        # Shared reports
        db.query(SharedReport).filter(SharedReport.user_id == uid).delete()

        # Health reports
        db.query(HealthReport).filter(HealthReport.user_id == uid).delete()

        # Sync jobs
        db.query(SyncJob).filter(SyncJob.user_id == uid).delete()

        # Test results via documents, then documents
        docs = db.query(Document).filter(Document.user_id == uid).all()
        for doc in docs:
            db.query(TestResult).filter(TestResult.document_id == doc.id).delete()
        db.query(Document).filter(Document.user_id == uid).delete()

        # Linked accounts
        db.query(LinkedAccount).filter(LinkedAccount.user_id == uid).delete()

        # Clean up file directories
        for subdir in ['data/raw', 'data/uploads', 'data/encrypted']:
            user_dir = Path('/opt/healthy/backend_v2') / subdir / str(uid)
            if user_dir.exists():
                shutil.rmtree(user_dir)
                print(f"    Removed {user_dir}")

        # Finally delete the user
        db.delete(user)

    db.commit()
    print("--- Cleanup complete ---\n")


# ============================================================
# CREATE USERS WITH VAULTS
# ============================================================
def create_users():
    now = utc_now()
    hashed_pw = get_password_hash(PASSWORD)

    mother = User(
        email=MOTHER_EMAIL,
        hashed_password=hashed_pw,
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
        date_of_birth=datetime(1985, 3, 15, tzinfo=timezone.utc),
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
        hashed_password=hashed_pw,
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
        date_of_birth=datetime(2012, 7, 22, tzinfo=timezone.utc),
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

    # Set up per-user vaults
    for user_obj in [mother, son]:
        vault = UserVault(user_obj.id)
        vault_result = vault.setup_vault(PASSWORD)
        user_obj.vault_data = json.dumps(vault_result['vault_data'])
        user_obj.vault_setup_at = utc_now()
        # Store the unlocked vault in session so encryption works
        set_user_vault_session(user_obj.id, vault)

        # Encrypt profile fields
        user_obj.full_name_enc = vault.encrypt_data(user_obj.full_name)
        dob_str = user_obj.date_of_birth.isoformat() if user_obj.date_of_birth else ""
        user_obj.date_of_birth_enc = vault.encrypt_data(dob_str)
        user_obj.gender_enc = vault.encrypt_data(user_obj.gender or "")
        user_obj.blood_type_enc = vault.encrypt_data(user_obj.blood_type or "")
        user_obj.profile_data_enc = vault.encrypt_json({
            "height_cm": user_obj.height_cm,
            "weight_kg": user_obj.weight_kg,
        })
        user_obj.health_context_enc = vault.encrypt_json({
            "allergies": json.loads(user_obj.allergies) if user_obj.allergies else [],
            "chronic_conditions": json.loads(user_obj.chronic_conditions) if user_obj.chronic_conditions else [],
            "current_medications": json.loads(user_obj.current_medications) if user_obj.current_medications else [],
        })

        print(f"  Created {user_obj.email} (ID: {user_obj.id}) with vault")
        print(f"    Recovery key: {vault_result['recovery_key']}")

    db.flush()
    return mother, son


# ============================================================
# HELPER: add biomarkers with vault encryption
# ============================================================
def add_biomarkers(doc, biomarkers, vault):
    """Add test results with both legacy and encrypted fields."""
    for name, canonical, val, num, unit, ref, flag, cat in biomarkers:
        tr = TestResult(
            document_id=doc.id,
            test_name=name,
            canonical_name=canonical,
            value=val,
            numeric_value=num,
            unit=unit,
            reference_range=ref,
            flags=flag,
            category=cat,
        )
        # Encrypt values
        tr.value_enc = vault.encrypt_data(val)
        tr.numeric_value_enc = vault.encrypt_number(num)
        db.add(tr)


# ============================================================
# HELPER: create health report with encryption
# ============================================================
def add_report(user_id, vault, report_type, title, summary, findings, recommendations, risk_level, created_at, biomarkers_analyzed):
    """Create a health report with both legacy and encrypted content."""
    report = HealthReport(
        user_id=user_id,
        report_type=report_type,
        title=title,
        summary=summary,
        findings=findings,
        recommendations=recommendations,
        risk_level=risk_level,
        created_at=created_at,
        biomarkers_analyzed=biomarkers_analyzed,
    )
    # Encrypt content
    content = {
        "summary": summary,
        "findings": findings,
        "recommendations": recommendations,
    }
    report.content_enc = vault.encrypt_json(content)
    db.add(report)
    return report


# ============================================================
# LINKED ACCOUNTS
# ============================================================
def create_linked_accounts(mother, son, mother_vault, son_vault):
    now = utc_now()
    accounts = []
    for user, vault in [(mother, mother_vault), (son, son_vault)]:
        for provider in ["Regina Maria", "Sanador"]:
            uname = user.email.split("@")[0]
            acc = LinkedAccount(
                user_id=user.id,
                provider_name=provider,
                username=uname,
                username_enc=vault.encrypt_data(uname),
                password_enc=vault.encrypt_data("demo_pass_placeholder"),
                last_sync=now - timedelta(days=2),
                status="ACTIVE",
                sync_enabled=True,
                sync_frequency="weekly",
                consecutive_failures=0,
            )
            db.add(acc)
            accounts.append(acc)
    db.flush()
    print(f"  Created {len(accounts)} linked accounts.")
    return accounts


# ============================================================
# MOTHER DATA
# ============================================================
def create_mother_data(mother, vault):
    now = utc_now()
    print("  Creating mother documents & biomarkers...")

    # Document 1: Hemoleucograma (6 months ago)
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
    doc1.patient_name_enc = vault.encrypt_data("Elena Popescu")
    db.add(doc1)
    db.flush()

    bio1 = [
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
    add_biomarkers(doc1, bio1, vault)
    create_pdf_on_disk(mother.id, doc1, bio1)

    # Document 2: Profil biochimic (6 months ago)
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
    doc2.patient_name_enc = vault.encrypt_data("Elena Popescu")
    db.add(doc2)
    db.flush()

    bio2 = [
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
    add_biomarkers(doc2, bio2, vault)
    create_pdf_on_disk(mother.id, doc2, bio2)

    # Document 3: Examen oftalmologic (3 months ago)
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
    doc3.patient_name_enc = vault.encrypt_data("Elena Popescu")
    db.add(doc3)
    db.flush()

    bio3 = [
        ("Presiune intraoculara OD", "Presiune intraoculara OD", "19", 19.0, "mmHg", "10-21", "NORMAL", "Oftalmologie"),
        ("Presiune intraoculara OS", "Presiune intraoculara OS", "22", 22.0, "mmHg", "10-21", "HIGH", "Oftalmologie"),
        ("Acuitate vizuala OD", "Acuitate vizuala OD", "0.7", 0.7, "", "1.0", "LOW", "Oftalmologie"),
        ("Acuitate vizuala OS", "Acuitate vizuala OS", "0.6", 0.6, "", "1.0", "LOW", "Oftalmologie"),
    ]
    add_biomarkers(doc3, bio3, vault)
    create_pdf_on_disk(mother.id, doc3, bio3)

    # Document 4: Control recent (2 weeks ago)
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
    doc4.patient_name_enc = vault.encrypt_data("Elena Popescu")
    db.add(doc4)
    db.flush()

    bio4 = [
        ("Hemoglobina", "Hemoglobina", "11.8", 11.8, "g/dL", "12.0-16.0", "LOW", "Hematologie"),
        ("Hematocrit", "Hematocrit", "35.8", 35.8, "%", "36.0-46.0", "LOW", "Hematologie"),
        ("Fier seric", "Fier seric", "48", 48.0, "ug/dL", "60-170", "LOW", "Hematologie"),
        ("Feritina", "Feritina", "12.0", 12.0, "ng/mL", "13-150", "LOW", "Hematologie"),
        ("Vitamina D (25-OH)", "Vitamina D", "32", 32.0, "ng/mL", "30-100", "NORMAL", "Vitamine"),
        ("CRP", "CRP", "2.5", 2.5, "mg/L", "<3.0", "NORMAL", "Inflamatie"),
        ("VSH", "VSH", "18", 18.0, "mm/h", "0-20", "NORMAL", "Inflamatie"),
        ("Leucocite (WBC)", "Leucocite", "7.1", 7.1, "x10^3/uL", "4.0-10.0", "NORMAL", "Hematologie"),
    ]
    add_biomarkers(doc4, bio4, vault)
    create_pdf_on_disk(mother.id, doc4, bio4)

    # --- HEALTH REPORTS ---
    # General report
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
        {"action": "Kinetoterapie 2-3 sedinte/saptamana", "reason": "Program de recuperare pentru gonartroza genunchi drept", "priority": "high"},
        {"action": "Dieta bogata in fier", "reason": "Carne rosie, spanac, linte, sfecla rosie", "priority": "medium"},
        {"action": "Reducere colesterol prin dieta", "reason": "Limitare grasimi saturate, crestere fibre - Colesterol total 215, LDL 138", "priority": "medium"},
        {"action": "Vitamina D3 suplimentar 2000 UI/zi", "reason": "Mentinerea nivelului optim de vitamina D", "priority": "low"},
    ]
    add_report(
        mother.id, vault, "general", "Evaluare Generala Sanatate",
        "Pacienta prezinta anemie feripriva persistenta cu tendinta usoara de ameliorare, valori limita ale presiunii intraoculare la ochiul stang necesitand monitorizare, si un profil lipidic usor crescut.",
        json.dumps(mother_findings), json.dumps(mother_recommendations),
        "attention", now - timedelta(days=13), 33
    )

    # Nutrition report
    nutrition_data = {
        "summary": "Plan alimentar conceput pentru combaterea anemiei feriprive, reducerea colesterolului si sustinerea sanatatii oculare.",
        "daily_targets": {"calories": "1800-2000 kcal", "protein": "65-75g", "hydration": "2.0L", "meal_frequency": "3 mese + 2 gustari"},
        "meal_plan": [
            {"day": "Ziua 1 - Luni", "meals": [
                {"meal": "Mic dejun", "time": "7:30-8:30", "items": ["Terci de ovaz cu miere si nuci - 250g", "1 portocala", "Ceai verde - 200ml"], "calories": "~380 kcal", "notes": "Ovazul ofera fibre solubile care reduc colesterolul", "recipe": "1. Fierbe 80g fulgi de ovaz in 250ml apa, 5 min. 2. Adauga 1 lingura miere si 30g nuci."},
                {"meal": "Pranz", "time": "12:30-13:30", "items": ["Ciorba de linte cu legume - 350ml", "Paine integrala - 1 felie", "Salata de spanac cu seminte de dovleac - 150g"], "calories": "~520 kcal", "notes": "Lintea si spanacul sunt surse excelente de fier vegetal"},
                {"meal": "Cina", "time": "18:30-19:30", "items": ["Piept de pui la gratar - 150g", "Orez brun cu legume - 200g", "Salata de sfecla rosie - 100g"], "calories": "~480 kcal", "notes": "Sfecla rosie sustine productia de hemoglobina"},
            ]},
            {"day": "Ziua 2 - Marti", "meals": [
                {"meal": "Mic dejun", "time": "7:30-8:30", "items": ["2 oua ochiuri pe paine integrala", "Rosii cherry - 100g", "Suc de portocale proaspat"], "calories": "~400 kcal", "notes": "Vitamina C din portocale creste absorbtia fierului"},
                {"meal": "Pranz", "time": "12:30-13:30", "items": ["Mancarica de mazare cu pui - 350g", "Mamaliga - 150g", "Salata de varza cu morcov"], "calories": "~550 kcal", "notes": "Mazarea ofera fier si proteine vegetale"},
                {"meal": "Cina", "time": "18:30-19:30", "items": ["Somon la cuptor cu lamaie - 150g", "Cartofi copti cu rozmarin - 200g", "Broccoli la aburi"], "calories": "~500 kcal", "notes": "Somonul ofera omega-3 benefice pentru ochi si inima"},
            ]},
            {"day": "Ziua 3 - Miercuri", "meals": [
                {"meal": "Mic dejun", "time": "7:30-8:30", "items": ["Smoothie cu spanac, banana si lapte de migdale - 350ml", "2 biscuiti integrali"], "calories": "~320 kcal", "notes": "Spanacul ofera fier si luteina"},
                {"meal": "Pranz", "time": "12:30-13:30", "items": ["Tocanita de vita cu legume - 300g", "Paste integrale - 150g"], "calories": "~580 kcal", "notes": "Carnea de vita este cea mai buna sursa de fier hem"},
                {"meal": "Cina", "time": "18:30-19:30", "items": ["Supa crema de dovleac - 300ml", "Paine integrala cu branza de vaci"], "calories": "~420 kcal", "notes": "Dovleacul si morcovii sunt bogati in beta-caroten"},
            ]},
        ],
        "priority_foods": [
            {"category": "Alimente bogate in fier", "reason": "Combaterea anemiei feriprive", "foods": ["Carne rosie de vita", "Ficat de pui", "Linte", "Spanac", "Sfecla rosie", "Naut"], "target": "15-20mg fier/zi"},
            {"category": "Surse de Omega-3", "reason": "Sanatatea ochilor si reducerea inflamatiei", "foods": ["Somon", "Pastrav", "Sardine", "Nuci", "Seminte de in"], "target": "250-500mg EPA+DHA/zi"},
        ],
        "foods_to_reduce": [
            {"category": "Grasimi saturate", "reason": "Reducerea colesterolului LDL", "examples": ["Unt excesiv", "Carne grasa de porc"], "alternatives": ["Ulei de masline", "Carne slaba de pui/curcan"]},
        ],
        "supplements_to_discuss": [
            {"supplement": "Fier (Tardyferon/Sideralia)", "reason": "Corectia anemiei feriprive - Feritina 12 ng/mL", "note": "A se lua pe stomacul gol cu vitamina C"},
            {"supplement": "Vitamina D3 2000 UI/zi", "reason": "Valori limita - 32 ng/mL", "note": "De luat cu masa"},
            {"supplement": "Omega-3 (ulei de peste)", "reason": "Sustinerea sanatatii oculare si cardiovasculare", "note": "1000mg/zi cu EPA+DHA"},
        ],
        "shopping_list": [
            {"category": "Carne & Peste", "items": ["Piept de pui 1kg", "Carne de vita 500g", "Somon file 400g"]},
            {"category": "Legume", "items": ["Spanac 500g", "Sfecla rosie 4 buc", "Morcovi 1kg", "Broccoli 500g"]},
            {"category": "Fructe", "items": ["Portocale 2kg", "Banane 1kg", "Afine 300g"]},
        ],
        "warnings": [
            "Anemia feripriva necesita monitorizare medicala",
            "Presiunea intraoculara crescuta la ochiul stang necesita control oftalmologic regulat",
        ],
    }
    add_report(
        mother.id, vault, "nutrition", "Plan Alimentar Personalizat",
        json.dumps(nutrition_data), None, None,
        "attention", now - timedelta(days=13), 33
    )

    # Exercise report
    exercise_data = {
        "summary": "Program de exercitii adaptat pentru gonartroza genunchi drept, imbunatatirea circulatiei si mentinerea sanatatii cardiovasculare.",
        "current_assessment": {
            "activity_level": "Sedentara - activitate fizica usoara",
            "exercise_readiness": "Moderata - necesita adaptare pentru gonartroza",
            "key_health_factors": ["Gonartroza genunchi drept", "Anemie feripriva", "Colesterol usor crescut"]
        },
        "weekly_schedule": [
            {"day": "Luni", "focus": "Kinetoterapie genunchi + Cardio", "total_duration": "45 min", "warmup": {"duration": "10 min", "exercises": ["Mers pe loc - 3 min", "Rotatii glezne si genunchi - 3 min", "Stretching usor - 4 min"]}, "main_workout": [
                {"exercise": "Extensii de genunchi sezand", "sets_reps": "3x12", "rest": "60s", "duration": "", "biomarker_benefit": "Intarire cvadriceps - protectie gonartroza"},
                {"exercise": "Ridicari de sold (bridge)", "sets_reps": "3x15", "rest": "45s", "duration": "", "biomarker_benefit": "Stabilitate genunchi si sold"},
                {"exercise": "Mers pe bicicleta statica", "sets_reps": "", "rest": "", "duration": "15 min", "biomarker_benefit": "Cardio fara impact pe genunchi"},
            ], "cooldown": {"duration": "5 min", "exercises": ["Stretching cvadriceps - 2 min", "Respiratii profunde - 3 min"]}},
            {"day": "Marti", "focus": "Cardio moderat + Tonifiere", "total_duration": "45 min", "warmup": {"duration": "8 min", "exercises": ["Mers pe loc cu balansare brate - 3 min", "Rotatii umeri - 2 min", "Flexii trunchi - 3 min"]}, "main_workout": [
                {"exercise": "Plimbare in aer liber", "sets_reps": "", "rest": "", "duration": "30 min", "biomarker_benefit": "Cardio, circulatie, vitamina D"},
                {"exercise": "Exercitii brate cu gantere mici", "sets_reps": "2x12", "rest": "45s", "duration": "", "biomarker_benefit": "Tonifiere generala"},
            ], "cooldown": {"duration": "5 min", "exercises": ["Stretching general - 5 min"]}},
            {"day": "Miercuri", "focus": "Kinetoterapie + Inot", "total_duration": "50 min", "warmup": {"duration": "10 min", "exercises": ["Mers pe loc - 3 min", "Mobilizare articulara - 4 min", "Balans pe un picior - 3 min"]}, "main_workout": [
                {"exercise": "Extensii izometrice genunchi", "sets_reps": "3x10", "rest": "60s", "duration": "", "biomarker_benefit": "Intarire musculatura periarticulara"},
                {"exercise": "Inot sau aquagym", "sets_reps": "", "rest": "", "duration": "20 min", "biomarker_benefit": "Cardio fara impact, mobilitate articulara"},
            ], "cooldown": {"duration": "5 min", "exercises": ["Stretching in apa - 5 min"]}},
        ],
    }
    add_report(
        mother.id, vault, "exercise", "Program de Exercitii Personalizat",
        json.dumps(exercise_data), None, None,
        "normal", now - timedelta(days=13), 33
    )

    # Gap analysis
    mother_gap_tests = [
        {"test_name": "Hemoleucograma completa + Feritina", "category": "Hematologie", "priority": "high", "reason": "Monitorizare anemie feripriva in tratament", "frequency": "La 3 luni", "recommended_interval_months": 3, "is_overdue": False, "last_done_date": (now - timedelta(days=14)).isoformat(), "months_since_last": 0},
        {"test_name": "Examen oftalmologic complet", "category": "Oftalmologie", "priority": "high", "reason": "Presiune intraoculara crescuta OS (22 mmHg)", "frequency": "La 3 luni", "recommended_interval_months": 3, "is_overdue": True, "last_done_date": (now - timedelta(days=90)).isoformat(), "months_since_last": 3},
        {"test_name": "Profil lipidic complet", "category": "Cardiovascular", "priority": "medium", "reason": "Colesterol total 215, LDL 138", "frequency": "La 6 luni", "recommended_interval_months": 6, "is_overdue": False, "last_done_date": (now - timedelta(days=178)).isoformat(), "months_since_last": 6},
        {"test_name": "Mamografie bilaterala", "category": "Cancer", "priority": "medium", "reason": "Screening cancer san - femeie 40 ani", "frequency": "Anual", "recommended_interval_months": 12, "is_overdue": True, "last_done_date": None, "months_since_last": None},
    ]
    add_report(
        mother.id, vault, "gap_analysis", "Screeninguri Recomandate",
        "Bazat pe profilul dvs. medical si rezultatele analizelor, va recomandam urmatoarele investigatii.",
        json.dumps(mother_gap_tests), json.dumps([]),
        "attention", now - timedelta(days=13), 33
    )

    print(f"    Mother: 4 docs, {10+15+4+8} biomarkers, 4 reports")


# ============================================================
# SON DATA
# ============================================================
def create_son_data(son, vault):
    now = utc_now()
    print("  Creating son documents & biomarkers...")

    # Document 1: Analize pediatrice (5 months ago)
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
    doc1.patient_name_enc = vault.encrypt_data("Andrei Popescu")
    db.add(doc1)
    db.flush()

    bio1 = [
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
    add_biomarkers(doc1, bio1, vault)
    create_pdf_on_disk(son.id, doc1, bio1)

    # Document 2: Panel alergologic (5 months ago)
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
    doc2.patient_name_enc = vault.encrypt_data("Andrei Popescu")
    db.add(doc2)
    db.flush()

    bio2 = [
        ("IgE specific Acarieni", "IgE Acarieni", "45.2", 45.2, "kU/L", "<0.35", "HIGH", "Alergologie"),
        ("IgE specific Ambrozie", "IgE Ambrozie", "28.7", 28.7, "kU/L", "<0.35", "HIGH", "Alergologie"),
        ("IgE specific Polen graminee", "IgE Polen graminee", "12.5", 12.5, "kU/L", "<0.35", "HIGH", "Alergologie"),
        ("IgE specific Lactoza", "IgE Lactoza", "8.3", 8.3, "kU/L", "<0.35", "HIGH", "Alergologie"),
        ("IgE specific Ou", "IgE Ou", "0.12", 0.12, "kU/L", "<0.35", "NORMAL", "Alergologie"),
        ("IgE specific Gluten", "IgE Gluten", "0.08", 0.08, "kU/L", "<0.35", "NORMAL", "Alergologie"),
    ]
    add_biomarkers(doc2, bio2, vault)
    create_pdf_on_disk(son.id, doc2, bio2)

    # Document 3: Evaluare ortopedie (2 months ago)
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
    doc3.patient_name_enc = vault.encrypt_data("Andrei Popescu")
    db.add(doc3)
    db.flush()

    bio3 = [
        ("Unghi Cobb", "Unghi Cobb", "18", 18.0, "grade", "<10", "HIGH", "Ortopedic"),
        ("Rotatie vertebrala", "Rotatie vertebrala", "1", 1.0, "grad Nash-Moe", "0", "HIGH", "Ortopedic"),
    ]
    add_biomarkers(doc3, bio3, vault)
    create_pdf_on_disk(son.id, doc3, bio3)

    # Document 4: Control recent (1 week ago)
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
    doc4.patient_name_enc = vault.encrypt_data("Andrei Popescu")
    db.add(doc4)
    db.flush()

    bio4 = [
        ("Hemoglobina", "Hemoglobina", "11.8", 11.8, "g/dL", "11.5-15.5", "NORMAL", "Hematologie"),
        ("Fier seric", "Fier seric", "52", 52.0, "ug/dL", "50-120", "NORMAL", "Hematologie"),
        ("Feritina", "Feritina", "18", 18.0, "ng/mL", "20-200", "LOW", "Hematologie"),
        ("Vitamina D (25-OH)", "Vitamina D", "22", 22.0, "ng/mL", "30-100", "LOW", "Vitamine"),
        ("Eozinofile", "Eozinofile", "7.2", 7.2, "%", "1-5", "HIGH", "Hematologie"),
        ("IgE total", "IgE total", "350", 350.0, "UI/mL", "<100", "HIGH", "Imunologie"),
        ("Leucocite (WBC)", "Leucocite", "7.8", 7.8, "x10^3/uL", "4.5-13.5", "NORMAL", "Hematologie"),
        ("Calciu total", "Calciu total", "9.2", 9.2, "mg/dL", "8.8-10.8", "NORMAL", "Minerale"),
    ]
    add_biomarkers(doc4, bio4, vault)
    create_pdf_on_disk(son.id, doc4, bio4)

    # --- HEALTH REPORTS ---
    son_findings = [
        {"category": "Vitamina D", "status": "concern", "explanation": "Deficit persistent de vitamina D - 22 ng/mL. Critic pentru cresterea osoasa.", "markers": ["Vitamina D"]},
        {"category": "Hematologie", "status": "attention", "explanation": "Feritina 18 ng/mL (limita inferioara). Fier seric normalizat la 52 ug/dL.", "markers": ["Feritina", "Fier seric"]},
        {"category": "Alergologie", "status": "attention", "explanation": "Alergii multiple: acarieni (IgE 45.2), ambrozie (28.7), polen graminee (12.5), lactoza (8.3). IgE total ridicat (350).", "markers": ["IgE total", "Eozinofile"]},
        {"category": "Ortopedic", "status": "concern", "explanation": "Scolioza toracica cu unghi Cobb 18 grade - forma moderata. Necesita kinetoterapie.", "markers": ["Unghi Cobb", "Rotatie vertebrala"]},
        {"category": "Metabolism", "status": "normal", "explanation": "Glicemie normala (82 mg/dL), TSH normal (3.1 mUI/L).", "markers": ["Glicemie", "TSH"]},
    ]
    son_recommendations = [
        {"action": "Vitamina D3 suplimentar 2000 UI/zi", "reason": "Deficit persistent (22 ng/mL) - critic pentru cresterea osoasa", "priority": "high"},
        {"action": "Kinetoterapie specifica scolioza 3x/saptamana", "reason": "Exercitii Schroth pentru corectia scoliozei toracice (Cobb 18 grade)", "priority": "high"},
        {"action": "Dieta bogata in fier", "reason": "Feritina la limita inferioara (18 ng/mL)", "priority": "medium"},
        {"action": "Evitare lactate din lapte de vaca", "reason": "Intoleranta lactoza confirmata (IgE 8.3)", "priority": "medium"},
        {"action": "Control ortopedic cu radiografie la 6 luni", "reason": "Monitorizare unghi Cobb in perioada de crestere rapida", "priority": "high"},
    ]
    add_report(
        son.id, vault, "general", "Evaluare Generala Sanatate",
        "Pacientul pediatric prezinta deficit de vitamina D persistent, depozite de fier la limita inferioara, alergii multiple si scolioza toracica moderata.",
        json.dumps(son_findings), json.dumps(son_recommendations),
        "attention", now - timedelta(days=6), 28
    )

    # Son exercise report
    son_exercise_data = {
        "summary": "Program de exercitii adaptat pentru scolioza toracica (Cobb 18 grade) si dezvoltare osoasa sanatoasa.",
        "current_assessment": {
            "activity_level": "Moderata - copil activ",
            "exercise_readiness": "Buna",
            "key_health_factors": ["Scolioza toracica moderata", "Deficit vitamina D", "Alergii respiratorii"]
        },
        "weekly_schedule": [
            {"day": "Luni", "focus": "Schroth + Inot", "total_duration": "55 min", "warmup": {"duration": "10 min", "exercises": ["Mers pe loc - 3 min", "Rotatii trunchi - 3 min", "Cat-Cow stretch - 4 min"]}, "main_workout": [
                {"exercise": "Exercitii Schroth - autoelongare", "sets_reps": "3x10", "rest": "60s", "duration": "", "biomarker_benefit": "Corectie posturala activa scolioza"},
                {"exercise": "Inot - stil craul", "sets_reps": "", "rest": "", "duration": "30 min", "biomarker_benefit": "Intarire simetrica spate"},
            ], "cooldown": {"duration": "5 min", "exercises": ["Stretching spate - 5 min"]}},
            {"day": "Marti", "focus": "Cardio + Core", "total_duration": "40 min", "warmup": {"duration": "8 min", "exercises": ["Sarituri usoare - 3 min", "Stretching dinamic - 5 min"]}, "main_workout": [
                {"exercise": "Alergare usoara", "sets_reps": "", "rest": "", "duration": "20 min", "biomarker_benefit": "Cardio, vitamina D"},
                {"exercise": "Exercitii abdominale adaptate", "sets_reps": "3x12", "rest": "45s", "duration": "", "biomarker_benefit": "Stabilitate core"},
            ], "cooldown": {"duration": "5 min", "exercises": ["Stretching general - 5 min"]}},
        ],
    }
    add_report(
        son.id, vault, "exercise", "Program de Exercitii - Scolioza si Dezvoltare",
        json.dumps(son_exercise_data), None, None,
        "normal", now - timedelta(days=6), 28
    )

    # Son gap analysis
    son_gap_tests = [
        {"test_name": "Vitamina D (25-OH) + Calciu", "category": "Metabolism osos", "priority": "high", "reason": "Deficit vitamina D persistent (22 ng/mL)", "frequency": "La 3 luni", "recommended_interval_months": 3, "is_overdue": False, "last_done_date": (now - timedelta(days=7)).isoformat(), "months_since_last": 0},
        {"test_name": "Radiografie coloana + evaluare ortopedica", "category": "Ortopedic", "priority": "high", "reason": "Monitorizare scolioza toracica", "frequency": "La 6 luni", "recommended_interval_months": 6, "is_overdue": False, "last_done_date": (now - timedelta(days=60)).isoformat(), "months_since_last": 2},
        {"test_name": "Hemoleucograma + Feritina", "category": "Hematologie", "priority": "medium", "reason": "Feritina la limita inferioara (18 ng/mL)", "frequency": "La 3 luni", "recommended_interval_months": 3, "is_overdue": False, "last_done_date": (now - timedelta(days=7)).isoformat(), "months_since_last": 0},
    ]
    add_report(
        son.id, vault, "gap_analysis", "Screeninguri Recomandate",
        "Bazat pe profilul medical al copilului, se recomanda urmatoarele investigatii.",
        json.dumps(son_gap_tests), json.dumps([]),
        "attention", now - timedelta(days=6), 28
    )

    print(f"    Son: 4 docs, {12+6+2+8} biomarkers, 3 reports")


# ============================================================
# FAMILY, SUBSCRIPTIONS, EXTRAS
# ============================================================
def create_extras(mother, son, mother_vault, son_vault):
    now = utc_now()
    print("  Creating family, subscriptions, medications...")

    # Family group
    family = FamilyGroup(
        owner_id=mother.id,
        name="Familia Popescu",
        invite_code=uuid.uuid4().hex[:8],
        created_at=now - timedelta(days=60),
    )
    db.add(family)
    db.flush()

    db.add(FamilyMember(family_id=family.id, user_id=mother.id, role="owner", joined_at=now - timedelta(days=60)))
    db.add(FamilyMember(family_id=family.id, user_id=son.id, role="member", joined_at=now - timedelta(days=59)))

    # Subscriptions
    db.add(Subscription(user_id=mother.id, tier="family", status="active", billing_cycle="monthly",
                         current_period_start=now - timedelta(days=15), current_period_end=now + timedelta(days=15)))
    db.add(Subscription(user_id=son.id, tier="family", status="active", billing_cycle="monthly",
                         current_period_start=now - timedelta(days=15), current_period_end=now + timedelta(days=15)))

    # Usage trackers
    db.add(UsageTracker(user_id=mother.id, ai_analyses_this_month=2, month_start=now.replace(day=1),
                         total_ai_analyses=8, total_documents_uploaded=4))
    db.add(UsageTracker(user_id=son.id, ai_analyses_this_month=1, month_start=now.replace(day=1),
                         total_ai_analyses=4, total_documents_uploaded=4))

    # Notification preferences
    db.add(NotificationPreference(user_id=mother.id))
    db.add(NotificationPreference(user_id=son.id))

    # Food preferences
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

    print("    Family, subscriptions, food prefs, medications created.")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("REBUILD DEMO ACCOUNTS")
    print("=" * 60)

    cleanup()

    print("\n--- Creating users with vaults ---")
    mother, son = create_users()

    # Get vaults for encryption
    from backend_v2.services.user_vault import get_user_vault
    mother_vault = get_user_vault(mother.id)
    son_vault = get_user_vault(son.id)

    create_linked_accounts(mother, son, mother_vault, son_vault)
    create_mother_data(mother, mother_vault)
    create_son_data(son, son_vault)
    create_extras(mother, son, mother_vault, son_vault)

    db.commit()

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    print(f"  Mother: {MOTHER_EMAIL} / {PASSWORD}  (ID: {mother.id})")
    print(f"  Son:    {SON_EMAIL} / {PASSWORD}  (ID: {son.id})")
    print("  Both have Family subscription, linked accounts, vault encryption.")
    print("  Login at https://analize.online to verify.")
    print("=" * 60)
