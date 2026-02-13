"""
GDPR compliance endpoints for data export and account deletion.
"""
import os
import json
import zipfile
import shutil
import tempfile
import logging
from datetime import datetime, timezone
from pathlib import Path
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

try:
    from backend_v2.database import get_db
    from backend_v2.routers.documents import get_current_user
    from backend_v2.models import (
        User, Document, TestResult, HealthReport, LinkedAccount,
        Subscription, UsageTracker, FamilyGroup, FamilyMember,
        AuditLog, UserSession, SyncJob, Notification, NotificationPreference,
        PushSubscription, AbuseFlag, UsageMetrics, OpenAIUsageLog
    )
    from backend_v2.services.user_vault import get_user_vault
except ImportError:
    from database import get_db
    from routers.documents import get_current_user
    from models import (
        User, Document, TestResult, HealthReport, LinkedAccount,
        Subscription, UsageTracker, FamilyGroup, FamilyMember,
        AuditLog, UserSession, SyncJob, Notification, NotificationPreference,
        PushSubscription, AbuseFlag, UsageMetrics, OpenAIUsageLog
    )
    from services.user_vault import get_user_vault

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


class DeleteAccountRequest(BaseModel):
    password: str
    confirm_text: str  # Must be "DELETE MY ACCOUNT"


def decrypt_if_possible(encrypted_data, user_vault, decrypt_func):
    """Try to decrypt data, return None if not possible."""
    if not encrypted_data:
        return None
    if not user_vault or not user_vault.is_unlocked:
        return "[encrypted - login required to export]"
    try:
        return decrypt_func(encrypted_data)
    except Exception:
        return "[decryption failed]"


@router.get("/export")
async def export_user_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export all user data in GDPR-compliant format.

    Returns a ZIP file containing:
    - profile.json: User profile and settings
    - documents.json: Document metadata
    - biomarkers.json: All biomarker data
    - health_reports.json: AI-generated health reports
    - linked_accounts.json: Connected provider accounts (without passwords)
    - subscription.json: Subscription information
    """
    user_vault = get_user_vault(current_user.id)

    # Collect all user data
    export_data = {}

    # 1. Profile data
    profile = {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "email_verified": current_user.email_verified,
        "language": current_user.language,
        "full_name": current_user.full_name,
        "date_of_birth": current_user.date_of_birth.isoformat() if current_user.date_of_birth else None,
        "gender": current_user.gender,
        "height_cm": current_user.height_cm,
        "weight_kg": current_user.weight_kg,
        "blood_type": current_user.blood_type,
        "smoking_status": current_user.smoking_status,
        "alcohol_consumption": current_user.alcohol_consumption,
        "physical_activity": current_user.physical_activity,
        "allergies": current_user.allergies,
        "chronic_conditions": current_user.chronic_conditions,
        "current_medications": current_user.current_medications,
        "terms_accepted_at": current_user.terms_accepted_at.isoformat() if current_user.terms_accepted_at else None,
        "privacy_accepted_at": current_user.privacy_accepted_at.isoformat() if current_user.privacy_accepted_at else None,
    }

    # Decrypt encrypted profile fields if vault is available
    if user_vault and user_vault.is_unlocked:
        if current_user.full_name_enc and not current_user.full_name:
            profile["full_name"] = decrypt_if_possible(
                current_user.full_name_enc, user_vault, user_vault.decrypt_data
            )
        if current_user.date_of_birth_enc and not current_user.date_of_birth:
            dob = decrypt_if_possible(current_user.date_of_birth_enc, user_vault, user_vault.decrypt_data)
            profile["date_of_birth"] = dob
        if current_user.gender_enc and not current_user.gender:
            profile["gender"] = decrypt_if_possible(
                current_user.gender_enc, user_vault, user_vault.decrypt_data
            )
        if current_user.blood_type_enc and not current_user.blood_type:
            profile["blood_type"] = decrypt_if_possible(
                current_user.blood_type_enc, user_vault, user_vault.decrypt_data
            )
        if current_user.profile_data_enc:
            profile_data = decrypt_if_possible(
                current_user.profile_data_enc, user_vault, user_vault.decrypt_json
            )
            if isinstance(profile_data, dict):
                profile.update(profile_data)
        if current_user.health_context_enc:
            health_context = decrypt_if_possible(
                current_user.health_context_enc, user_vault, user_vault.decrypt_json
            )
            if isinstance(health_context, dict):
                profile["allergies"] = health_context.get("allergies", profile.get("allergies"))
                profile["chronic_conditions"] = health_context.get("chronic_conditions", profile.get("chronic_conditions"))
                profile["current_medications"] = health_context.get("current_medications", profile.get("current_medications"))

    export_data["profile"] = profile

    # 2. Documents
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    export_data["documents"] = []
    for doc in documents:
        doc_data = {
            "id": doc.id,
            "filename": doc.filename,
            "provider": doc.provider,
            "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
            "document_date": doc.document_date.isoformat() if doc.document_date else None,
            "is_processed": doc.is_processed,
            "patient_name": doc.patient_name,
        }
        if doc.patient_name_enc and not doc.patient_name and user_vault and user_vault.is_unlocked:
            doc_data["patient_name"] = decrypt_if_possible(
                doc.patient_name_enc, user_vault, user_vault.decrypt_data
            )
        export_data["documents"].append(doc_data)

    # 3. Biomarkers
    doc_ids = [d.id for d in documents]
    biomarkers = []
    if doc_ids:
        results = db.query(TestResult).filter(TestResult.document_id.in_(doc_ids)).all()
        for result in results:
            bio_data = {
                "id": result.id,
                "document_id": result.document_id,
                "test_name": result.test_name,
                "canonical_name": result.canonical_name,
                "value": result.value,
                "numeric_value": result.numeric_value,
                "unit": result.unit,
                "reference_range": result.reference_range,
                "flags": result.flags,
                "category": result.category,
            }
            # Decrypt values if available
            if user_vault and user_vault.is_unlocked:
                if result.value_enc and not result.value:
                    bio_data["value"] = decrypt_if_possible(
                        result.value_enc, user_vault, user_vault.decrypt_data
                    )
                if result.numeric_value_enc and result.numeric_value is None:
                    bio_data["numeric_value"] = decrypt_if_possible(
                        result.numeric_value_enc, user_vault, user_vault.decrypt_number
                    )
            biomarkers.append(bio_data)
    export_data["biomarkers"] = biomarkers

    # 4. Health Reports
    reports = db.query(HealthReport).filter(HealthReport.user_id == current_user.id).all()
    export_data["health_reports"] = []
    for report in reports:
        report_data = {
            "id": report.id,
            "report_type": report.report_type,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "summary": report.summary,
            "findings": report.findings,
            "recommendations": report.recommendations,
        }
        # Decrypt if needed
        if report.content_enc and not report.summary and user_vault and user_vault.is_unlocked:
            content = decrypt_if_possible(report.content_enc, user_vault, user_vault.decrypt_json)
            if isinstance(content, dict):
                report_data["summary"] = content.get("summary")
                report_data["findings"] = content.get("findings")
                report_data["recommendations"] = content.get("recommendations")
        export_data["health_reports"].append(report_data)

    # 5. Linked Accounts (without passwords)
    accounts = db.query(LinkedAccount).filter(LinkedAccount.user_id == current_user.id).all()
    export_data["linked_accounts"] = []
    for account in accounts:
        acc_data = {
            "id": account.id,
            "provider_name": account.provider_name,
            "username": account.username,
            "last_sync": account.last_sync.isoformat() if account.last_sync else None,
            "sync_frequency": account.sync_frequency,
            "sync_enabled": account.sync_enabled,
            "status": account.status,
        }
        if account.username_enc and not account.username and user_vault and user_vault.is_unlocked:
            acc_data["username"] = decrypt_if_possible(
                account.username_enc, user_vault, user_vault.decrypt_data
            )
        export_data["linked_accounts"].append(acc_data)

    # 6. Subscription
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if subscription:
        export_data["subscription"] = {
            "tier": subscription.tier,
            "status": subscription.status,
            "billing_cycle": subscription.billing_cycle,
            "current_period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            "cancel_at_period_end": subscription.cancel_at_period_end,
        }

    # 7. Family membership
    family_member = db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).first()
    if family_member:
        export_data["family_membership"] = {
            "family_id": family_member.family_id,
            "role": family_member.role,
            "joined_at": family_member.joined_at.isoformat() if family_member.joined_at else None,
        }

    # Create ZIP file in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add each section as a separate JSON file
        for section, data in export_data.items():
            json_content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
            zip_file.writestr(f"{section}.json", json_content)

        # Add a README
        readme = """# Your Data Export from Analize.online

This ZIP file contains all your personal data stored in Analize.online.

## Contents:
- profile.json - Your profile information and settings
- documents.json - Metadata about your uploaded documents
- biomarkers.json - All extracted biomarker data from your lab results
- health_reports.json - AI-generated health analysis reports
- linked_accounts.json - Your connected medical provider accounts
- subscription.json - Your subscription information
- family_membership.json - Family group membership (if applicable)

## Notes:
- Some data may show as "[encrypted - login required to export]" if your
  encryption vault was not unlocked during export. Log in and export again
  to get the decrypted data.
- Document files (PDFs) are not included in this export for size reasons.
  Contact support if you need the original files.

## Data Portability:
This export is provided in JSON format for easy import into other systems.

Export date: {date}
""".format(date=datetime.now(timezone.utc).isoformat())
        zip_file.writestr("README.txt", readme)

    zip_buffer.seek(0)

    filename = f"analize_online_export_{current_user.id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/delete-account")
async def delete_user_account(
    request: DeleteAccountRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permanently delete user account and all associated data.

    This action is irreversible. All data will be permanently deleted:
    - Profile and settings
    - All documents (files and metadata)
    - All biomarker data
    - All health reports
    - All linked accounts
    - Subscription (will be cancelled)
    - Family membership (will leave any family groups)
    """
    # Verify confirmation text
    if request.confirm_text != "DELETE MY ACCOUNT":
        raise HTTPException(
            status_code=400,
            detail="Please type 'DELETE MY ACCOUNT' to confirm deletion"
        )

    # Verify password
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    if not current_user.hashed_password:
        # Google OAuth user - they can't verify with password
        # For OAuth users, the confirmation text is enough
        pass
    elif not pwd_context.verify(request.password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    user_id = current_user.id

    logger.info(f"Starting account deletion for user {user_id}")

    try:
        # 1. Delete health reports
        db.query(HealthReport).filter(HealthReport.user_id == user_id).delete()

        # 2. Get document IDs and delete biomarkers
        documents = db.query(Document).filter(Document.user_id == user_id).all()
        doc_ids = [d.id for d in documents]

        if doc_ids:
            db.query(TestResult).filter(TestResult.document_id.in_(doc_ids)).delete(synchronize_session=False)

        # 3. Delete document files
        for doc in documents:
            # Delete unencrypted file
            if doc.file_path and os.path.exists(doc.file_path):
                try:
                    os.remove(doc.file_path)
                except Exception as e:
                    logger.warning(f"Could not delete file {doc.file_path}: {e}")

            # Delete encrypted file
            if doc.encrypted_path and os.path.exists(doc.encrypted_path):
                try:
                    os.remove(doc.encrypted_path)
                except Exception as e:
                    logger.warning(f"Could not delete file {doc.encrypted_path}: {e}")

        # 4. Delete documents from database
        db.query(Document).filter(Document.user_id == user_id).delete()

        # 5. Delete linked accounts
        db.query(LinkedAccount).filter(LinkedAccount.user_id == user_id).delete()

        # 6. Delete usage tracker
        db.query(UsageTracker).filter(UsageTracker.user_id == user_id).delete()

        # 7. Delete subscription
        db.query(Subscription).filter(Subscription.user_id == user_id).delete()

        # 8. Handle family membership
        family_member = db.query(FamilyMember).filter(FamilyMember.user_id == user_id).first()
        if family_member:
            if family_member.role == "owner":
                # Delete entire family group and all memberships
                family_id = family_member.family_id
                db.query(FamilyMember).filter(FamilyMember.family_id == family_id).delete()
                db.query(FamilyGroup).filter(FamilyGroup.id == family_id).delete()
            else:
                # Just remove from family
                db.delete(family_member)

        # 9. Delete user's encrypted file directory
        encrypted_dir = Path(f"data/encrypted/{user_id}")
        if encrypted_dir.exists():
            try:
                shutil.rmtree(encrypted_dir)
            except Exception as e:
                logger.warning(f"Could not delete encrypted directory: {e}")

        # 10. Delete audit logs, sessions, and other user-related records
        db.query(AuditLog).filter(AuditLog.user_id == user_id).delete()
        db.query(UserSession).filter(UserSession.user_id == user_id).delete()
        db.query(SyncJob).filter(SyncJob.user_id == user_id).delete()
        db.query(Notification).filter(Notification.user_id == user_id).delete()
        db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).delete()
        db.query(PushSubscription).filter(PushSubscription.user_id == user_id).delete()
        db.query(AbuseFlag).filter(AbuseFlag.user_id == user_id).delete()
        db.query(UsageMetrics).filter(UsageMetrics.user_id == user_id).delete()
        db.query(OpenAIUsageLog).filter(OpenAIUsageLog.user_id == user_id).delete()

        # 11. Finally, delete the user
        db.query(User).filter(User.id == user_id).delete()

        db.commit()

        logger.info(f"Account deletion completed for user {user_id}")

        return {
            "status": "success",
            "message": "Your account and all associated data have been permanently deleted."
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Account deletion failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Account deletion failed. Please contact support. Error: {str(e)}"
        )


@router.get("/data-summary")
async def get_data_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a summary of all data stored for the user.
    Useful before export or deletion.
    """
    # Count documents
    doc_count = db.query(Document).filter(Document.user_id == current_user.id).count()

    # Count biomarkers
    doc_ids = [d.id for d in db.query(Document.id).filter(Document.user_id == current_user.id).all()]
    biomarker_count = 0
    if doc_ids:
        biomarker_count = db.query(TestResult).filter(TestResult.document_id.in_(doc_ids)).count()

    # Count health reports
    report_count = db.query(HealthReport).filter(HealthReport.user_id == current_user.id).count()

    # Count linked accounts
    account_count = db.query(LinkedAccount).filter(LinkedAccount.user_id == current_user.id).count()

    # Check family membership
    family_member = db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).first()
    family_info = None
    if family_member:
        family_info = {
            "role": family_member.role,
            "family_id": family_member.family_id,
            "is_owner": family_member.role == "owner"
        }
        if family_member.role == "owner":
            member_count = db.query(FamilyMember).filter(
                FamilyMember.family_id == family_member.family_id
            ).count()
            family_info["member_count"] = member_count

    return {
        "documents": doc_count,
        "biomarkers": biomarker_count,
        "health_reports": report_count,
        "linked_accounts": account_count,
        "family": family_info,
        "account_created": current_user.created_at.isoformat() if current_user.created_at else None,
    }
