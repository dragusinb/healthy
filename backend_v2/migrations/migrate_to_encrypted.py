"""
Data migration to encrypt existing data with the vault.

This script reads all existing unencrypted data and encrypts it
using the vault. The vault must be initialized and unlocked before
running this migration.

Usage:
    python -m backend_v2.migrations.migrate_to_encrypted

Note: This is a one-way migration. Ensure you have backups before running.
"""

import sys
import os
import json
import getpass
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import SessionLocal
from models import LinkedAccount, TestResult, HealthReport, User, Document
from services.vault import vault, VaultLockedError
from cryptography.fernet import Fernet


def decrypt_legacy_password(encrypted_password: str) -> str:
    """Decrypt password encrypted with old Fernet method."""
    try:
        # Get the Fernet key from environment
        fernet_key = os.getenv("ENCRYPTION_KEY")
        if not fernet_key:
            # Try to read from .env file
            env_path = Path(__file__).parent.parent.parent / ".env"
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("ENCRYPTION_KEY="):
                            fernet_key = line.split("=", 1)[1].strip()
                            break

        if not fernet_key:
            print("  WARNING: ENCRYPTION_KEY not found, cannot decrypt legacy passwords")
            return None

        fernet = Fernet(fernet_key.encode() if isinstance(fernet_key, str) else fernet_key)
        return fernet.decrypt(encrypted_password.encode()).decode()
    except Exception as e:
        print(f"  WARNING: Failed to decrypt legacy password: {e}")
        return None


def migrate_linked_accounts(db):
    """Migrate linked accounts credentials."""
    print("\n[1/5] Migrating linked accounts...")

    accounts = db.query(LinkedAccount).filter(
        LinkedAccount.username_enc.is_(None)
    ).all()

    if not accounts:
        print("  No accounts to migrate")
        return

    migrated = 0
    for account in accounts:
        try:
            # Encrypt username
            if account.username:
                account.username_enc = vault.encrypt_credential(account.username)

            # Decrypt old password and re-encrypt with vault
            if account.encrypted_password:
                plain_password = decrypt_legacy_password(account.encrypted_password)
                if plain_password:
                    account.password_enc = vault.encrypt_credential(plain_password)

            migrated += 1
        except Exception as e:
            print(f"  ERROR migrating account {account.id}: {e}")

    db.commit()
    print(f"  Migrated {migrated} accounts")


def migrate_biomarkers(db):
    """Migrate biomarker values."""
    print("\n[2/5] Migrating biomarkers...")

    # Process in batches to avoid memory issues
    batch_size = 1000
    offset = 0
    total_migrated = 0

    while True:
        results = db.query(TestResult).filter(
            TestResult.value_enc.is_(None),
            TestResult.value.isnot(None)
        ).limit(batch_size).offset(offset).all()

        if not results:
            break

        for result in results:
            try:
                if result.value:
                    result.value_enc = vault.encrypt_data(result.value)
                if result.numeric_value is not None:
                    result.numeric_value_enc = vault.encrypt_number(result.numeric_value)
                total_migrated += 1
            except Exception as e:
                print(f"  ERROR migrating biomarker {result.id}: {e}")

        db.commit()
        offset += batch_size
        print(f"  Processed {offset} biomarkers...")

    print(f"  Migrated {total_migrated} biomarkers")


def migrate_health_reports(db):
    """Migrate health reports."""
    print("\n[3/5] Migrating health reports...")

    reports = db.query(HealthReport).filter(
        HealthReport.content_enc.is_(None)
    ).all()

    if not reports:
        print("  No reports to migrate")
        return

    migrated = 0
    for report in reports:
        try:
            # Combine summary, findings, recommendations into one encrypted blob
            content = {
                "summary": report.summary,
                "findings": report.findings,
                "recommendations": report.recommendations
            }
            report.content_enc = vault.encrypt_json(content)
            migrated += 1
        except Exception as e:
            print(f"  ERROR migrating report {report.id}: {e}")

    db.commit()
    print(f"  Migrated {migrated} reports")


def migrate_user_profiles(db):
    """Migrate user profile data."""
    print("\n[4/5] Migrating user profiles...")

    users = db.query(User).filter(
        User.full_name_enc.is_(None),
        User.full_name.isnot(None)
    ).all()

    if not users:
        print("  No profiles to migrate")
        return

    migrated = 0
    for user in users:
        try:
            # Encrypt individual fields
            if user.full_name:
                user.full_name_enc = vault.encrypt_data(user.full_name)
            if user.date_of_birth:
                user.date_of_birth_enc = vault.encrypt_data(user.date_of_birth.isoformat())
            if user.gender:
                user.gender_enc = vault.encrypt_data(user.gender)
            if user.blood_type:
                user.blood_type_enc = vault.encrypt_data(user.blood_type)

            # Combine height, weight into profile_data
            profile_data = {}
            if user.height_cm:
                profile_data["height_cm"] = user.height_cm
            if user.weight_kg:
                profile_data["weight_kg"] = user.weight_kg
            if profile_data:
                user.profile_data_enc = vault.encrypt_json(profile_data)

            # Combine health context
            health_context = {}
            if user.allergies:
                health_context["allergies"] = user.allergies
            if user.chronic_conditions:
                health_context["chronic_conditions"] = user.chronic_conditions
            if user.current_medications:
                health_context["current_medications"] = user.current_medications
            if health_context:
                user.health_context_enc = vault.encrypt_json(health_context)

            migrated += 1
        except Exception as e:
            print(f"  ERROR migrating user {user.id}: {e}")

    db.commit()
    print(f"  Migrated {migrated} user profiles")


def migrate_documents(db):
    """Migrate document files to encrypted storage."""
    print("\n[5/5] Migrating document files...")

    documents = db.query(Document).filter(
        Document.is_encrypted == False,
        Document.file_path.isnot(None)
    ).all()

    if not documents:
        print("  No documents to migrate")
        return

    # Create encrypted storage directory
    encrypted_dir = Path(__file__).parent.parent.parent / "data" / "encrypted"
    encrypted_dir.mkdir(parents=True, exist_ok=True)

    migrated = 0
    errors = 0

    for doc in documents:
        try:
            # Read original file
            original_path = Path(doc.file_path)
            if not original_path.exists():
                print(f"  WARNING: File not found: {original_path}")
                continue

            with open(original_path, 'rb') as f:
                content = f.read()

            # Encrypt content
            encrypted_content = vault.encrypt_document(content)

            # Save to encrypted directory
            user_dir = encrypted_dir / str(doc.user_id)
            user_dir.mkdir(exist_ok=True)
            encrypted_path = user_dir / f"{doc.id}.enc"

            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_content)

            # Update document record
            doc.encrypted_path = str(encrypted_path)
            doc.is_encrypted = True

            # Encrypt patient info
            if doc.patient_name:
                doc.patient_name_enc = vault.encrypt_data(doc.patient_name)
            if doc.patient_cnp_prefix:
                doc.patient_cnp_enc = vault.encrypt_data(doc.patient_cnp_prefix)

            migrated += 1

            if migrated % 100 == 0:
                print(f"  Processed {migrated} documents...")
                db.commit()

        except Exception as e:
            print(f"  ERROR migrating document {doc.id}: {e}")
            errors += 1

    db.commit()
    print(f"  Migrated {migrated} documents ({errors} errors)")


def run_migration():
    """Run the full data migration."""

    # Check vault status
    if not vault.is_configured:
        print("ERROR: Vault not initialized.")
        print("Please run: POST /admin/vault/initialize first")
        return False

    if not vault.is_unlocked:
        print("Vault is locked. Please enter master password to unlock.")
        password = getpass.getpass("Master password: ")

        if not vault.unlock(password):
            print("ERROR: Invalid master password")
            return False

        print("Vault unlocked successfully")

    db = SessionLocal()
    try:
        migrate_linked_accounts(db)
        migrate_biomarkers(db)
        migrate_health_reports(db)
        migrate_user_profiles(db)
        migrate_documents(db)

        print("\n" + "=" * 50)
        print("Migration completed!")
        print("=" * 50)
        print("\nIMPORTANT: After verifying the migration:")
        print("1. Backup the encrypted data")
        print("2. Remove legacy unencrypted columns (optional)")
        print("3. Delete unencrypted PDF files (optional)")

        return True

    except VaultLockedError:
        print("ERROR: Vault was locked during migration")
        return False
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Vault Encryption - Data Migration")
    print("=" * 50)
    print()
    print("This will encrypt all existing data with the vault.")
    print("Make sure you have a backup before proceeding.")
    print()

    confirm = input("Type 'yes' to continue: ")
    if confirm.lower() != 'yes':
        print("Migration cancelled")
        sys.exit(0)

    success = run_migration()
    sys.exit(0 if success else 1)
