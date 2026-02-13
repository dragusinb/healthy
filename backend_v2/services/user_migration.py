"""
User Data Migration Service

Migrates legacy user data from global vault encryption to per-user vault encryption.
This runs automatically when a legacy user (without vault) logs in.
"""

import logging
from pathlib import Path
from sqlalchemy.orm import Session

try:
    from backend_v2.models import User, LinkedAccount, Document, TestResult, HealthReport
    from backend_v2.services.user_vault import UserVault
    from backend_v2.services.vault import vault as global_vault
except ImportError:
    from models import User, LinkedAccount, Document, TestResult, HealthReport
    from services.user_vault import UserVault
    from services.vault import vault as global_vault

logger = logging.getLogger(__name__)


def migrate_user_to_per_user_vault(
    db: Session,
    user: User,
    user_vault: UserVault
) -> dict:
    """
    Migrate all of a user's data from global vault to per-user vault.

    This function:
    1. Decrypts data using global vault
    2. Re-encrypts using the user's personal vault
    3. Updates database records

    Args:
        db: Database session
        user: User to migrate
        user_vault: User's unlocked vault

    Returns:
        Dict with migration statistics
    """
    stats = {
        "linked_accounts": 0,
        "documents": 0,
        "biomarkers": 0,
        "health_reports": 0,
        "profile_fields": 0,
        "errors": []
    }

    # Check if global vault is unlocked (needed to decrypt legacy data)
    if not global_vault.is_unlocked:
        logger.warning("Global vault is locked - skipping legacy data migration")
        return stats

    if not user_vault.is_unlocked:
        logger.error("User vault is not unlocked - cannot migrate")
        return stats

    logger.info(f"Starting migration for user {user.id}")

    # 1. Migrate linked account credentials
    try:
        for account in db.query(LinkedAccount).filter(
            LinkedAccount.user_id == user.id,
            LinkedAccount.username_enc.is_(None)
        ).all():
            try:
                # Decrypt from legacy Fernet or global vault
                if account.username and not account.username_enc:
                    account.username_enc = user_vault.encrypt_data(account.username)
                    account.username = None  # Clear plaintext
                    stats["linked_accounts"] += 1

                if account.encrypted_password and not account.password_enc:
                    # Try to decrypt legacy Fernet password
                    try:
                        from cryptography.fernet import Fernet
                        import os
                        fernet_key = os.getenv("ENCRYPTION_KEY")
                        if fernet_key:
                            fernet = Fernet(fernet_key.encode())
                            plain_password = fernet.decrypt(account.encrypted_password.encode()).decode()
                            account.password_enc = user_vault.encrypt_data(plain_password)
                            account.encrypted_password = None  # Clear legacy
                    except Exception as e:
                        logger.warning(f"Could not migrate legacy password for account {account.id}: {e}")

            except Exception as e:
                stats["errors"].append(f"LinkedAccount {account.id}: {str(e)}")
                logger.error(f"Error migrating account {account.id}: {e}")

        db.commit()
    except Exception as e:
        logger.error(f"Error migrating linked accounts: {e}")
        db.rollback()

    # 2. Migrate user profile fields
    try:
        profile_updated = False

        if user.full_name and not user.full_name_enc:
            user.full_name_enc = user_vault.encrypt_data(user.full_name)
            user.full_name = None
            stats["profile_fields"] += 1
            profile_updated = True

        if user.date_of_birth and not user.date_of_birth_enc:
            user.date_of_birth_enc = user_vault.encrypt_data(user.date_of_birth.isoformat())
            user.date_of_birth = None
            stats["profile_fields"] += 1
            profile_updated = True

        if user.gender and not user.gender_enc:
            user.gender_enc = user_vault.encrypt_data(user.gender)
            user.gender = None
            stats["profile_fields"] += 1
            profile_updated = True

        if user.blood_type and not user.blood_type_enc:
            user.blood_type_enc = user_vault.encrypt_data(user.blood_type)
            user.blood_type = None
            stats["profile_fields"] += 1
            profile_updated = True

        # Combine height/weight into profile_data_enc
        if (user.height_cm or user.weight_kg) and not user.profile_data_enc:
            profile_data = {}
            if user.height_cm:
                profile_data["height_cm"] = user.height_cm
                user.height_cm = None
            if user.weight_kg:
                profile_data["weight_kg"] = user.weight_kg
                user.weight_kg = None
            if profile_data:
                user.profile_data_enc = user_vault.encrypt_json(profile_data)
                stats["profile_fields"] += 1
                profile_updated = True

        # Combine health context
        if (user.allergies or user.chronic_conditions or user.current_medications) and not user.health_context_enc:
            health_context = {}
            if user.allergies:
                health_context["allergies"] = user.allergies
                user.allergies = None
            if user.chronic_conditions:
                health_context["chronic_conditions"] = user.chronic_conditions
                user.chronic_conditions = None
            if user.current_medications:
                health_context["current_medications"] = user.current_medications
                user.current_medications = None
            if health_context:
                user.health_context_enc = user_vault.encrypt_json(health_context)
                stats["profile_fields"] += 1
                profile_updated = True

        if profile_updated:
            db.commit()

    except Exception as e:
        logger.error(f"Error migrating user profile: {e}")
        stats["errors"].append(f"User profile: {str(e)}")
        db.rollback()

    # 3. Migrate biomarker values (batch process)
    try:
        batch_size = 100
        migrated = 0

        documents = db.query(Document).filter(Document.user_id == user.id).all()
        doc_ids = [d.id for d in documents]

        if doc_ids:
            results = db.query(TestResult).filter(
                TestResult.document_id.in_(doc_ids),
                TestResult.value_enc.is_(None),
                TestResult.value.isnot(None)
            ).all()

            for result in results:
                try:
                    if result.value:
                        result.value_enc = user_vault.encrypt_data(result.value)
                        result.value = None
                    if result.numeric_value is not None:
                        result.numeric_value_enc = user_vault.encrypt_number(result.numeric_value)
                        result.numeric_value = None
                    migrated += 1

                    if migrated % batch_size == 0:
                        db.commit()

                except Exception as e:
                    stats["errors"].append(f"TestResult {result.id}: {str(e)}")

            db.commit()
            stats["biomarkers"] = migrated

    except Exception as e:
        logger.error(f"Error migrating biomarkers: {e}")
        db.rollback()

    # 4. Migrate health reports
    try:
        reports = db.query(HealthReport).filter(
            HealthReport.user_id == user.id,
            HealthReport.content_enc.is_(None)
        ).all()

        for report in reports:
            try:
                content = {
                    "summary": report.summary,
                    "findings": report.findings,
                    "recommendations": report.recommendations
                }
                report.content_enc = user_vault.encrypt_json(content)
                report.summary = None
                report.findings = None
                report.recommendations = None
                stats["health_reports"] += 1
            except Exception as e:
                stats["errors"].append(f"HealthReport {report.id}: {str(e)}")

        db.commit()

    except Exception as e:
        logger.error(f"Error migrating health reports: {e}")
        db.rollback()

    # 5. Migrate document files (re-encrypt with user vault)
    try:
        documents = db.query(Document).filter(
            Document.user_id == user.id,
            Document.is_encrypted == True,
            Document.encrypted_path.isnot(None)
        ).all()

        for doc in documents:
            try:
                enc_path = Path(doc.encrypted_path)
                if enc_path.exists():
                    # Read file encrypted with global vault
                    encrypted_content = enc_path.read_bytes()

                    # Decrypt with global vault
                    decrypted = global_vault.decrypt_document(encrypted_content)

                    # Re-encrypt with user vault
                    re_encrypted = user_vault.encrypt_bytes(decrypted)

                    # Write back
                    enc_path.write_bytes(re_encrypted)
                    stats["documents"] += 1

                # Migrate patient info
                if doc.patient_name and not doc.patient_name_enc:
                    doc.patient_name_enc = user_vault.encrypt_data(doc.patient_name)
                    doc.patient_name = None

                if doc.patient_cnp_prefix and not doc.patient_cnp_enc:
                    doc.patient_cnp_enc = user_vault.encrypt_data(doc.patient_cnp_prefix)
                    doc.patient_cnp_prefix = None

            except Exception as e:
                stats["errors"].append(f"Document {doc.id}: {str(e)}")
                logger.error(f"Error migrating document {doc.id}: {e}")

        db.commit()

    except Exception as e:
        logger.error(f"Error migrating documents: {e}")
        db.rollback()

    logger.info(f"Migration completed for user {user.id}: {stats}")
    return stats


def setup_vault_for_legacy_user(
    db: Session,
    user: User,
    password: str
) -> tuple[UserVault, str, dict]:
    """
    Set up a vault for a legacy user who doesn't have one yet.

    Args:
        db: Database session
        user: User without vault
        password: User's password (for vault creation)

    Returns:
        Tuple of (vault, recovery_key, migration_stats)
    """
    from datetime import datetime, timezone
    import json

    # Create vault
    vault = UserVault(user.id)
    vault_result = vault.setup_vault(password)

    # Store vault configuration
    user.vault_data = json.dumps(vault_result['vault_data'])
    user.vault_setup_at = datetime.now(timezone.utc)
    db.commit()

    # Migrate existing data
    migration_stats = migrate_user_to_per_user_vault(db, user, vault)

    return vault, vault_result['recovery_key'], migration_stats
