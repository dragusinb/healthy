"""
Re-encryption Service

Re-encrypts user data from plaintext sources using their per-user vault.
Use this when:
1. A user has a vault but their data is encrypted with the wrong key (global vault)
2. Plaintext data exists and needs to be properly encrypted

This service will:
- Re-encrypt documents from unencrypted files
- Re-encrypt biomarkers from plaintext value columns
- Re-encrypt profile data from plaintext columns
- Delete plaintext data after successful re-encryption
"""

import logging
import os
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

try:
    from backend_v2.models import User, LinkedAccount, Document, TestResult, HealthReport
    from backend_v2.services.user_vault import UserVault, get_user_vault
except ImportError:
    from models import User, LinkedAccount, Document, TestResult, HealthReport
    from services.user_vault import UserVault, get_user_vault

logger = logging.getLogger(__name__)


def get_encrypted_storage_path() -> Path:
    """Get path to encrypted file storage."""
    path = Path("data/encrypted")
    path.mkdir(parents=True, exist_ok=True)
    return path


def reencrypt_user_documents(
    db: Session,
    user: User,
    user_vault: UserVault,
    delete_plaintext: bool = True
) -> dict:
    """
    Re-encrypt all documents for a user from their unencrypted sources.

    Args:
        db: Database session
        user: User whose documents to re-encrypt
        user_vault: User's unlocked vault
        delete_plaintext: Whether to delete unencrypted files after re-encryption

    Returns:
        Dict with statistics
    """
    stats = {"documents_reencrypted": 0, "errors": [], "skipped": 0}

    if not user_vault.is_unlocked:
        stats["errors"].append("User vault is not unlocked")
        return stats

    documents = db.query(Document).filter(Document.user_id == user.id).all()

    for doc in documents:
        try:
            # Check if unencrypted file exists
            if not doc.file_path or not os.path.exists(doc.file_path):
                stats["skipped"] += 1
                continue

            # Read unencrypted content
            plaintext_content = Path(doc.file_path).read_bytes()

            # Encrypt with user vault
            encrypted_content = user_vault.encrypt_bytes(plaintext_content)

            # Determine encrypted path
            user_dir = get_encrypted_storage_path() / str(user.id)
            user_dir.mkdir(parents=True, exist_ok=True)
            encrypted_path = user_dir / f"{doc.id}.enc"

            # Save encrypted content
            encrypted_path.write_bytes(encrypted_content)

            # Update document record
            doc.encrypted_path = str(encrypted_path)
            doc.is_encrypted = True

            # Delete unencrypted file if requested
            if delete_plaintext:
                try:
                    os.remove(doc.file_path)
                    doc.file_path = None
                except Exception as e:
                    logger.warning(f"Could not delete unencrypted file {doc.file_path}: {e}")

            stats["documents_reencrypted"] += 1

        except Exception as e:
            stats["errors"].append(f"Document {doc.id}: {str(e)}")
            logger.error(f"Error re-encrypting document {doc.id}: {e}")

    db.commit()
    return stats


def reencrypt_user_biomarkers(
    db: Session,
    user: User,
    user_vault: UserVault,
    clear_plaintext: bool = True
) -> dict:
    """
    Re-encrypt all biomarkers for a user from plaintext values.

    Args:
        db: Database session
        user: User whose biomarkers to re-encrypt
        user_vault: User's unlocked vault
        clear_plaintext: Whether to clear plaintext columns after encryption

    Returns:
        Dict with statistics
    """
    stats = {"biomarkers_reencrypted": 0, "errors": [], "skipped": 0}

    if not user_vault.is_unlocked:
        stats["errors"].append("User vault is not unlocked")
        return stats

    # Get all documents for this user
    doc_ids = [d.id for d in db.query(Document.id).filter(Document.user_id == user.id).all()]

    if not doc_ids:
        return stats

    # Get all test results with plaintext values
    results = db.query(TestResult).filter(
        TestResult.document_id.in_(doc_ids),
        TestResult.value.isnot(None)
    ).all()

    batch_size = 100
    batch_count = 0

    for result in results:
        try:
            # Encrypt value if plaintext exists
            if result.value:
                result.value_enc = user_vault.encrypt_data(result.value)
                if clear_plaintext:
                    result.value = None

            # Encrypt numeric value if it exists
            if result.numeric_value is not None:
                result.numeric_value_enc = user_vault.encrypt_number(result.numeric_value)
                if clear_plaintext:
                    result.numeric_value = None

            stats["biomarkers_reencrypted"] += 1
            batch_count += 1

            # Commit in batches
            if batch_count >= batch_size:
                db.commit()
                batch_count = 0

        except Exception as e:
            stats["errors"].append(f"TestResult {result.id}: {str(e)}")
            logger.error(f"Error re-encrypting test result {result.id}: {e}")

    db.commit()
    return stats


def reencrypt_user_profile(
    db: Session,
    user: User,
    user_vault: UserVault,
    clear_plaintext: bool = True
) -> dict:
    """
    Re-encrypt user profile data from plaintext columns.

    Returns:
        Dict with statistics
    """
    stats = {"fields_reencrypted": 0, "errors": []}

    if not user_vault.is_unlocked:
        stats["errors"].append("User vault is not unlocked")
        return stats

    try:
        # Full name
        if user.full_name:
            user.full_name_enc = user_vault.encrypt_data(user.full_name)
            if clear_plaintext:
                user.full_name = None
            stats["fields_reencrypted"] += 1

        # Date of birth
        if user.date_of_birth:
            user.date_of_birth_enc = user_vault.encrypt_data(user.date_of_birth.isoformat())
            if clear_plaintext:
                user.date_of_birth = None
            stats["fields_reencrypted"] += 1

        # Gender
        if user.gender:
            user.gender_enc = user_vault.encrypt_data(user.gender)
            if clear_plaintext:
                user.gender = None
            stats["fields_reencrypted"] += 1

        # Blood type
        if user.blood_type:
            user.blood_type_enc = user_vault.encrypt_data(user.blood_type)
            if clear_plaintext:
                user.blood_type = None
            stats["fields_reencrypted"] += 1

        # Height and weight -> profile_data_enc
        if user.height_cm or user.weight_kg:
            profile_data = {}
            if user.height_cm:
                profile_data["height_cm"] = user.height_cm
            if user.weight_kg:
                profile_data["weight_kg"] = user.weight_kg

            user.profile_data_enc = user_vault.encrypt_json(profile_data)
            if clear_plaintext:
                user.height_cm = None
                user.weight_kg = None
            stats["fields_reencrypted"] += 1

        # Health context
        if user.allergies or user.chronic_conditions or user.current_medications:
            health_context = {}
            if user.allergies:
                health_context["allergies"] = user.allergies
            if user.chronic_conditions:
                health_context["chronic_conditions"] = user.chronic_conditions
            if user.current_medications:
                health_context["current_medications"] = user.current_medications

            user.health_context_enc = user_vault.encrypt_json(health_context)
            if clear_plaintext:
                user.allergies = None
                user.chronic_conditions = None
                user.current_medications = None
            stats["fields_reencrypted"] += 1

        db.commit()

    except Exception as e:
        stats["errors"].append(f"Profile: {str(e)}")
        logger.error(f"Error re-encrypting user profile: {e}")
        db.rollback()

    return stats


def reencrypt_user_health_reports(
    db: Session,
    user: User,
    user_vault: UserVault,
    clear_plaintext: bool = True
) -> dict:
    """
    Re-encrypt health reports from plaintext columns.
    """
    stats = {"reports_reencrypted": 0, "errors": []}

    if not user_vault.is_unlocked:
        stats["errors"].append("User vault is not unlocked")
        return stats

    reports = db.query(HealthReport).filter(
        HealthReport.user_id == user.id,
        HealthReport.summary.isnot(None)  # Has plaintext content
    ).all()

    for report in reports:
        try:
            content = {
                "summary": report.summary,
                "findings": report.findings,
                "recommendations": report.recommendations
            }
            report.content_enc = user_vault.encrypt_json(content)

            if clear_plaintext:
                report.summary = None
                report.findings = None
                report.recommendations = None

            stats["reports_reencrypted"] += 1

        except Exception as e:
            stats["errors"].append(f"HealthReport {report.id}: {str(e)}")
            logger.error(f"Error re-encrypting health report {report.id}: {e}")

    db.commit()
    return stats


def reencrypt_user_linked_accounts(
    db: Session,
    user: User,
    user_vault: UserVault,
    clear_plaintext: bool = True
) -> dict:
    """
    Re-encrypt linked account credentials.
    """
    stats = {"accounts_reencrypted": 0, "errors": []}

    if not user_vault.is_unlocked:
        stats["errors"].append("User vault is not unlocked")
        return stats

    accounts = db.query(LinkedAccount).filter(
        LinkedAccount.user_id == user.id
    ).all()

    for account in accounts:
        try:
            updated = False

            # Encrypt username if plaintext exists
            if account.username:
                account.username_enc = user_vault.encrypt_data(account.username)
                if clear_plaintext:
                    account.username = None
                updated = True

            # Try to decrypt legacy Fernet password and re-encrypt
            if account.encrypted_password:
                try:
                    from cryptography.fernet import Fernet
                    fernet_key = os.getenv("ENCRYPTION_KEY")
                    if fernet_key:
                        fernet = Fernet(fernet_key.encode())
                        plain_password = fernet.decrypt(account.encrypted_password.encode()).decode()
                        account.password_enc = user_vault.encrypt_data(plain_password)
                        if clear_plaintext:
                            account.encrypted_password = None
                        updated = True
                except Exception as e:
                    logger.warning(f"Could not decrypt legacy password for account {account.id}: {e}")

            if updated:
                stats["accounts_reencrypted"] += 1

        except Exception as e:
            stats["errors"].append(f"LinkedAccount {account.id}: {str(e)}")
            logger.error(f"Error re-encrypting linked account {account.id}: {e}")

    db.commit()
    return stats


def reencrypt_all_user_data(
    db: Session,
    user: User,
    user_vault: UserVault,
    delete_plaintext: bool = True
) -> dict:
    """
    Re-encrypt all user data from plaintext sources.

    Args:
        db: Database session
        user: User whose data to re-encrypt
        user_vault: User's unlocked vault
        delete_plaintext: Whether to delete/clear plaintext after encryption

    Returns:
        Combined statistics
    """
    logger.info(f"Starting full re-encryption for user {user.id}")

    all_stats = {
        "documents": reencrypt_user_documents(db, user, user_vault, delete_plaintext),
        "biomarkers": reencrypt_user_biomarkers(db, user, user_vault, delete_plaintext),
        "profile": reencrypt_user_profile(db, user, user_vault, delete_plaintext),
        "health_reports": reencrypt_user_health_reports(db, user, user_vault, delete_plaintext),
        "linked_accounts": reencrypt_user_linked_accounts(db, user, user_vault, delete_plaintext),
    }

    # Summary
    total_errors = []
    for key, stats in all_stats.items():
        if "errors" in stats:
            total_errors.extend(stats["errors"])

    all_stats["total_errors"] = total_errors
    all_stats["success"] = len(total_errors) == 0

    logger.info(f"Re-encryption completed for user {user.id}: {all_stats}")
    return all_stats
