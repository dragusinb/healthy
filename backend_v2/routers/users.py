from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import datetime
import json
import hashlib
import os


def calculate_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of a file for duplicate detection."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return None

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, LinkedAccount
    from backend_v2.routers.documents import get_current_user
    from backend_v2.services import sync_status
    from backend_v2.auth.crypto import encrypt_password, decrypt_password
    from backend_v2.services.vault import vault, VaultLockedError
    from backend_v2.services.subscription_service import SubscriptionService
    from backend_v2.auth.rate_limiter import check_profile_scan_rate_limit
except ImportError:
    from database import get_db
    from models import User, LinkedAccount
    from routers.documents import get_current_user
    from services import sync_status
    from auth.crypto import encrypt_password, decrypt_password
    from services.vault import vault, VaultLockedError
    from services.subscription_service import SubscriptionService
    from auth.rate_limiter import check_profile_scan_rate_limit


def get_account_username(account: LinkedAccount) -> str:
    """Get username from account, preferring vault-encrypted if available."""
    if account.username_enc and vault.is_unlocked:
        try:
            return vault.decrypt_credential(account.username_enc)
        except Exception:
            pass
    return account.username


def get_account_password(account: LinkedAccount) -> str:
    """Get decrypted password from account, preferring vault-encrypted if available."""
    if account.password_enc and vault.is_unlocked:
        try:
            return vault.decrypt_credential(account.password_enc)
        except Exception:
            pass
    # Fall back to legacy Fernet encryption
    if account.encrypted_password:
        return decrypt_password(account.encrypted_password)
    return None


router = APIRouter(prefix="/users", tags=["users"])

class LinkedAccountCreate(BaseModel):
    provider_name: str
    username: str
    password: str


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None  # YYYY-MM-DD format
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_type: Optional[str] = None
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    smoking_status: Optional[str] = None
    alcohol_consumption: Optional[str] = None
    physical_activity: Optional[str] = None

@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    # Include linked account errors for popup notification
    linked_accounts_data = []
    for acc in current_user.linked_accounts:
        # Get username from vault if available
        username = get_account_username(acc) if vault.is_unlocked else "[encrypted]"

        acc_data = {
            "id": acc.id,
            "provider_name": acc.provider_name,
            "username": username,
            "status": acc.status,
            "last_sync": acc.last_sync.isoformat() if acc.last_sync else None,
            "last_sync_error": acc.last_sync_error,
            "error_type": acc.error_type if hasattr(acc, 'error_type') else None,
            "error_acknowledged": acc.error_acknowledged if hasattr(acc, 'error_acknowledged') else True,
            "consecutive_failures": acc.consecutive_failures
        }
        linked_accounts_data.append(acc_data)

    return {
        "email": current_user.email,
        "id": current_user.id,
        "is_admin": current_user.is_admin,
        "is_active": current_user.is_active,
        "email_verified": current_user.email_verified,
        "language": current_user.language,
        "linked_accounts": linked_accounts_data,
        "profile": get_profile_data(current_user),
        "vault_unlocked": vault.is_unlocked
    }


def get_profile_data(user: User) -> dict:
    """Extract profile data from user model, preferring vault-encrypted fields."""
    # Try vault-encrypted fields first
    full_name = None
    date_of_birth = None
    gender = None
    blood_type = None
    height_cm = None
    weight_kg = None
    allergies = []
    chronic_conditions = []
    current_medications = []

    if vault.is_unlocked:
        try:
            if user.full_name_enc:
                full_name = vault.decrypt_data(user.full_name_enc)
            if user.date_of_birth_enc:
                date_of_birth = vault.decrypt_data(user.date_of_birth_enc)
            if user.gender_enc:
                gender = vault.decrypt_data(user.gender_enc)
            if user.blood_type_enc:
                blood_type = vault.decrypt_data(user.blood_type_enc)
            if user.profile_data_enc:
                profile_data = vault.decrypt_json(user.profile_data_enc)
                height_cm = profile_data.get("height_cm")
                weight_kg = profile_data.get("weight_kg")
            if user.health_context_enc:
                health_context = vault.decrypt_json(user.health_context_enc)
                allergies = json.loads(health_context.get("allergies", "[]")) if isinstance(health_context.get("allergies"), str) else health_context.get("allergies", [])
                chronic_conditions = json.loads(health_context.get("chronic_conditions", "[]")) if isinstance(health_context.get("chronic_conditions"), str) else health_context.get("chronic_conditions", [])
                current_medications = json.loads(health_context.get("current_medications", "[]")) if isinstance(health_context.get("current_medications"), str) else health_context.get("current_medications", [])
        except Exception:
            pass  # Fall back to legacy fields

    # Fall back to legacy unencrypted fields
    if full_name is None:
        full_name = user.full_name
    if date_of_birth is None and user.date_of_birth:
        date_of_birth = user.date_of_birth.strftime("%Y-%m-%d")
    if gender is None:
        gender = user.gender
    if blood_type is None:
        blood_type = user.blood_type
    if height_cm is None:
        height_cm = user.height_cm
    if weight_kg is None:
        weight_kg = user.weight_kg
    if not allergies:
        allergies = json.loads(user.allergies) if user.allergies else []
    if not chronic_conditions:
        chronic_conditions = json.loads(user.chronic_conditions) if user.chronic_conditions else []
    if not current_medications:
        current_medications = json.loads(user.current_medications) if user.current_medications else []

    # Parse date_of_birth for age calculation
    dob_datetime = None
    if isinstance(date_of_birth, str):
        try:
            dob_datetime = datetime.datetime.strptime(date_of_birth, "%Y-%m-%d")
        except (ValueError, TypeError):
            pass
    elif isinstance(date_of_birth, datetime.datetime):
        dob_datetime = date_of_birth
        date_of_birth = date_of_birth.strftime("%Y-%m-%d")

    return {
        "full_name": full_name,
        "date_of_birth": date_of_birth,
        "age": calculate_age(dob_datetime) if dob_datetime else None,
        "gender": gender,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "bmi": calculate_bmi(height_cm, weight_kg) if height_cm and weight_kg else None,
        "blood_type": blood_type,
        "allergies": allergies,
        "chronic_conditions": chronic_conditions,
        "current_medications": current_medications,
        "smoking_status": user.smoking_status,
        "alcohol_consumption": user.alcohol_consumption,
        "physical_activity": user.physical_activity
    }


def calculate_age(dob: datetime.datetime) -> int:
    """Calculate age from date of birth."""
    today = datetime.date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    """Calculate BMI from height and weight."""
    if height_cm <= 0:
        return None
    height_m = height_cm / 100
    return round(weight_kg / (height_m * height_m), 1)


@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    """Get user's profile data."""
    return get_profile_data(current_user)


@router.put("/profile")
def update_profile(
    profile: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user's profile data."""
    # Check vault status for encrypted storage
    use_vault = vault.is_unlocked

    if profile.full_name is not None:
        if use_vault:
            current_user.full_name_enc = vault.encrypt_data(profile.full_name) if profile.full_name else None
            current_user.full_name = None  # Clear legacy
        else:
            current_user.full_name = profile.full_name

    if profile.date_of_birth is not None:
        if profile.date_of_birth == "" or profile.date_of_birth is None:
            if use_vault:
                current_user.date_of_birth_enc = None
            current_user.date_of_birth = None
        else:
            try:
                dob = datetime.datetime.strptime(profile.date_of_birth, "%Y-%m-%d")
                if use_vault:
                    current_user.date_of_birth_enc = vault.encrypt_data(profile.date_of_birth)
                    current_user.date_of_birth = None  # Clear legacy
                else:
                    current_user.date_of_birth = dob
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    if profile.gender is not None:
        if profile.gender not in ["male", "female", "other", ""]:
            raise HTTPException(status_code=400, detail="Invalid gender value")
        gender_val = profile.gender if profile.gender else None
        if use_vault:
            current_user.gender_enc = vault.encrypt_data(gender_val) if gender_val else None
            current_user.gender = None  # Clear legacy
        else:
            current_user.gender = gender_val

    if profile.blood_type is not None:
        valid_blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", ""]
        if profile.blood_type not in valid_blood_types:
            raise HTTPException(status_code=400, detail="Invalid blood type")
        blood_type_val = profile.blood_type if profile.blood_type else None
        if use_vault:
            current_user.blood_type_enc = vault.encrypt_data(blood_type_val) if blood_type_val else None
            current_user.blood_type = None  # Clear legacy
        else:
            current_user.blood_type = blood_type_val

    # Handle height/weight - store in profile_data_enc if vault is unlocked
    if profile.height_cm is not None or profile.weight_kg is not None:
        if profile.height_cm is not None:
            if profile.height_cm < 0 or profile.height_cm > 300:
                raise HTTPException(status_code=400, detail="Height must be between 0 and 300 cm")
        if profile.weight_kg is not None:
            if profile.weight_kg < 0 or profile.weight_kg > 500:
                raise HTTPException(status_code=400, detail="Weight must be between 0 and 500 kg")

        if use_vault:
            # Get existing profile data or create new
            profile_data = {}
            if current_user.profile_data_enc:
                try:
                    profile_data = vault.decrypt_json(current_user.profile_data_enc)
                except Exception:
                    pass
            if profile.height_cm is not None:
                profile_data["height_cm"] = profile.height_cm if profile.height_cm > 0 else None
            if profile.weight_kg is not None:
                profile_data["weight_kg"] = profile.weight_kg if profile.weight_kg > 0 else None
            current_user.profile_data_enc = vault.encrypt_json(profile_data)
            current_user.height_cm = None  # Clear legacy
            current_user.weight_kg = None
        else:
            if profile.height_cm is not None:
                current_user.height_cm = profile.height_cm if profile.height_cm > 0 else None
            if profile.weight_kg is not None:
                current_user.weight_kg = profile.weight_kg if profile.weight_kg > 0 else None

    # Handle health context (allergies, conditions, medications)
    if profile.allergies is not None or profile.chronic_conditions is not None or profile.current_medications is not None:
        if use_vault:
            health_context = {}
            if current_user.health_context_enc:
                try:
                    health_context = vault.decrypt_json(current_user.health_context_enc)
                except Exception:
                    pass
            if profile.allergies is not None:
                health_context["allergies"] = json.dumps(profile.allergies)
            if profile.chronic_conditions is not None:
                health_context["chronic_conditions"] = json.dumps(profile.chronic_conditions)
            if profile.current_medications is not None:
                health_context["current_medications"] = json.dumps(profile.current_medications)
            current_user.health_context_enc = vault.encrypt_json(health_context)
            # Clear legacy
            current_user.allergies = None
            current_user.chronic_conditions = None
            current_user.current_medications = None
        else:
            if profile.allergies is not None:
                current_user.allergies = json.dumps(profile.allergies)
            if profile.chronic_conditions is not None:
                current_user.chronic_conditions = json.dumps(profile.chronic_conditions)
            if profile.current_medications is not None:
                current_user.current_medications = json.dumps(profile.current_medications)

    # Non-sensitive lifestyle fields (not encrypted)
    if profile.smoking_status is not None:
        valid_smoking = ["never", "former", "current", ""]
        if profile.smoking_status not in valid_smoking:
            raise HTTPException(status_code=400, detail="Invalid smoking status")
        current_user.smoking_status = profile.smoking_status if profile.smoking_status else None

    if profile.alcohol_consumption is not None:
        valid_alcohol = ["none", "occasional", "moderate", "heavy", ""]
        if profile.alcohol_consumption not in valid_alcohol:
            raise HTTPException(status_code=400, detail="Invalid alcohol consumption value")
        current_user.alcohol_consumption = profile.alcohol_consumption if profile.alcohol_consumption else None

    if profile.physical_activity is not None:
        valid_activity = ["sedentary", "light", "moderate", "active", "very_active", ""]
        if profile.physical_activity not in valid_activity:
            raise HTTPException(status_code=400, detail="Invalid physical activity value")
        current_user.physical_activity = profile.physical_activity if profile.physical_activity else None

    db.commit()

    return {"message": "Profile updated", "profile": get_profile_data(current_user)}

@router.post("/accounts/{account_id}/acknowledge-error")
def acknowledge_account_error(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an account error as acknowledged (user has seen it)."""
    account = db.query(LinkedAccount).filter(
        LinkedAccount.id == account_id,
        LinkedAccount.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.error_acknowledged = True
    db.commit()

    return {"message": "Error acknowledged"}


@router.post("/scan-profile")
def scan_profile_from_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Scan user's documents to extract profile information using AI.
    OPTIMIZED: Uses batch extraction (1 API call for multiple documents).
    RATE LIMITED: Max 3 scans per day per user to prevent excessive API usage.
    """
    import os

    try:
        from backend_v2.models import Document
        from backend_v2.services.ai_parser import AIParser
    except ImportError:
        from models import Document
        from services.ai_parser import AIParser

    # Apply rate limiting (max 3 scans per day)
    check_profile_scan_rate_limit(current_user.id)

    # Check if profile is already complete - skip expensive AI call
    current_profile = get_profile_data(current_user)
    if all([
        current_profile.get("full_name"),
        current_profile.get("date_of_birth"),
        current_profile.get("gender")
    ]):
        # Profile is mostly complete, check if we're just missing blood type
        if current_profile.get("blood_type"):
            return {
                "status": "already_complete",
                "message": "Profile is already complete",
                "profile": current_profile
            }

    # Get user's processed documents (most recent first)
    # OPTIMIZED: Limit to 10 documents (was 50)
    documents = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.is_processed == True
    ).order_by(Document.document_date.desc()).limit(10).all()

    if not documents:
        return {"status": "no_documents", "message": "No processed documents found", "profile": {}}

    def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                # Focus on first 2 pages where patient info usually is
                for i, page in enumerate(pdf.pages[:2]):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return ""

    # Collect document texts for batch processing
    doc_texts = []
    for doc in documents:
        if not doc.file_path or not os.path.exists(doc.file_path):
            continue
        text = extract_text_from_pdf(doc.file_path)
        if text:
            doc_texts.append({
                "id": doc.id,
                "filename": doc.filename,
                "text": text,
                "date": doc.document_date
            })
        if len(doc_texts) >= 5:  # Max 5 documents for batch
            break

    if not doc_texts:
        return {
            "status": "no_readable_documents",
            "message": "Could not read any documents",
            "profile": {}
        }

    # OPTIMIZED: Single API call for all documents (was 1 call per document)
    parser = AIParser()
    result = parser.extract_profiles_batch(doc_texts, max_docs=5)

    if result.get("error"):
        return {
            "status": "error",
            "message": result["error"],
            "profile": {}
        }

    merged_profile = result.get("profile", {})
    scanned_count = result.get("documents_scanned", 0)

    if not merged_profile or not any(merged_profile.values()):
        return {
            "status": "no_profile_found",
            "message": f"Scanned {scanned_count} documents but could not extract profile information",
            "profile": {}
        }

    # Track age document date for birth year calculation
    age_document_date = doc_texts[0].get("date") if doc_texts else None

    # Apply to user profile (only fill empty fields)
    # Use vault encryption when available
    use_vault = vault.is_unlocked
    updates_made = []

    # Check current profile data (prefer encrypted, fall back to legacy)
    current_full_name = None
    current_dob = None
    current_gender = None
    current_blood_type = None

    if use_vault:
        try:
            if current_user.full_name_enc:
                current_full_name = vault.decrypt_data(current_user.full_name_enc)
            if current_user.date_of_birth_enc:
                current_dob = vault.decrypt_data(current_user.date_of_birth_enc)
            if current_user.gender_enc:
                current_gender = vault.decrypt_data(current_user.gender_enc)
            if current_user.blood_type_enc:
                current_blood_type = vault.decrypt_data(current_user.blood_type_enc)
        except Exception:
            pass

    # Fall back to legacy fields
    if current_full_name is None:
        current_full_name = current_user.full_name
    if current_dob is None and current_user.date_of_birth:
        current_dob = current_user.date_of_birth.strftime("%Y-%m-%d")
    if current_gender is None:
        current_gender = current_user.gender
    if current_blood_type is None:
        current_blood_type = current_user.blood_type

    if merged_profile.get("full_name") and not current_full_name:
        if use_vault:
            current_user.full_name_enc = vault.encrypt_data(merged_profile["full_name"])
            current_user.full_name = None  # Clear legacy
        else:
            current_user.full_name = merged_profile["full_name"]
        updates_made.append("full_name")

    if not current_dob:
        dob_str = None
        # Try direct date_of_birth first
        if merged_profile.get("date_of_birth"):
            try:
                dob = datetime.datetime.strptime(merged_profile["date_of_birth"], "%Y-%m-%d")
                dob_str = merged_profile["date_of_birth"]
                updates_made.append("date_of_birth")
            except (ValueError, TypeError):
                pass  # Invalid date format - will try age fallback
        # Fallback: calculate from age_years if no birth date found
        elif merged_profile.get("age_years"):
            try:
                age = int(merged_profile["age_years"])
                # Use document date for accurate calculation, fallback to today
                reference_date = age_document_date if age_document_date else datetime.date.today()
                if hasattr(reference_date, 'year'):
                    birth_year = reference_date.year - age
                else:
                    birth_year = datetime.date.today().year - age
                # Approximate birth date (use January 1st of birth year)
                dob_str = f"{birth_year}-01-01"
                updates_made.append("date_of_birth (estimated from age)")
            except (ValueError, TypeError):
                pass

        if dob_str:
            if use_vault:
                current_user.date_of_birth_enc = vault.encrypt_data(dob_str)
                current_user.date_of_birth = None  # Clear legacy
            else:
                current_user.date_of_birth = datetime.datetime.strptime(dob_str, "%Y-%m-%d")

    if merged_profile.get("gender") and not current_gender:
        if merged_profile["gender"] in ["male", "female"]:
            if use_vault:
                current_user.gender_enc = vault.encrypt_data(merged_profile["gender"])
                current_user.gender = None  # Clear legacy
            else:
                current_user.gender = merged_profile["gender"]
            updates_made.append("gender")

    # Extract blood type (e.g., "A+", "B-", "AB+", "O-")
    if merged_profile.get("blood_type") and not current_blood_type:
        valid_blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        blood_type = merged_profile["blood_type"].upper().strip()
        if blood_type in valid_blood_types:
            if use_vault:
                current_user.blood_type_enc = vault.encrypt_data(blood_type)
                current_user.blood_type = None  # Clear legacy
            else:
                current_user.blood_type = blood_type
            updates_made.append("blood_type")

    if updates_made:
        db.commit()

    # Multi-patient detection using CNP prefix as unique identifier
    # Query all documents with CNP prefix
    all_docs_patient_info = db.query(Document.patient_name, Document.patient_cnp_prefix).filter(
        Document.user_id == current_user.id,
        Document.patient_cnp_prefix.isnot(None)
    ).all()

    # Group patients by CNP prefix only - pick first name found for each CNP
    patient_groups = {}  # key: cnp_prefix, value: display_name
    for name, cnp_prefix in all_docs_patient_info:
        if cnp_prefix and cnp_prefix not in patient_groups:
            patient_groups[cnp_prefix] = name or "Unknown"

    # Also add from extracted profiles
    for profile in extracted_profiles:
        cnp = profile.get("cnp_prefix")
        name = profile.get("full_name")
        if cnp and cnp not in patient_groups:
            patient_groups[cnp] = name or "Unknown"

    distinct_patients = list(patient_groups.values())

    # Build response
    response = {
        "status": "success" if updates_made else "no_new_data",
        "message": f"Updated {len(updates_made)} fields" if updates_made else "No new profile data to update (fields already filled or no data found)",
        "updates": updates_made,
        "extracted": merged_profile,
        "documents_scanned": scanned_count,
        "profile": get_profile_data(current_user)
    }

    # Add multi-patient warning if multiple distinct patients detected
    if len(distinct_patients) > 1:
        response["multi_patient_warning"] = True
        response["patients_found"] = distinct_patients
        response["warning_message"] = f"Found documents for {len(distinct_patients)} different patients: {', '.join(distinct_patients)}. Your profile may contain data from multiple people."

    return response


@router.post("/link-account")
def link_account(
    account: LinkedAccountCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check vault status
    if not vault.is_unlocked:
        raise HTTPException(
            status_code=503,
            detail="Vault is locked. Please contact administrator to unlock the system."
        )

    # Check if this is a new account (not updating existing)
    existing = db.query(LinkedAccount).filter(
        LinkedAccount.user_id == current_user.id,
        LinkedAccount.provider_name == account.provider_name
    ).first()

    # Only check quota for NEW accounts
    if not existing:
        subscription_service = SubscriptionService(db)
        can_add, message = subscription_service.check_can_add_provider(current_user.id)
        if not can_add:
            raise HTTPException(status_code=403, detail=message)

    # Encrypt credentials with vault
    username_enc = vault.encrypt_credential(account.username)
    password_enc = vault.encrypt_credential(account.password)

    if existing:
        was_in_error = existing.status == 'ERROR'
        # Store vault-encrypted credentials
        existing.username_enc = username_enc
        existing.password_enc = password_enc
        # Clear legacy fields
        existing.username = None
        existing.encrypted_password = None
        # Reset error state when credentials are updated
        existing.status = 'ACTIVE'
        existing.error_type = None
        existing.error_acknowledged = False
        existing.consecutive_failures = 0
        existing.last_sync_error = None
        db.commit()

        # Auto-trigger sync if credentials were updated after an error
        if was_in_error:
            background_tasks.add_task(
                run_sync_task,
                current_user.id,
                account.provider_name,
                existing.id
            )
            return {"message": "Account updated", "sync_triggered": True}

        return {"message": "Account updated", "sync_triggered": False}

    new_link = LinkedAccount(
        user_id=current_user.id,
        provider_name=account.provider_name,
        username_enc=username_enc,
        password_enc=password_enc
    )
    db.add(new_link)
    db.commit()
    return {"message": "Account linked", "sync_triggered": False}

@router.get("/sync-status/{provider_name}")
def get_sync_status(provider_name: str, current_user: User = Depends(get_current_user)):
    """Get current sync status for a provider."""
    status = sync_status.get_status(current_user.id, provider_name)
    if status:
        return status
    return {"stage": "idle", "message": "No sync in progress"}


@router.post("/sync/{provider_name}")
async def sync_provider(
    provider_name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check vault status
    if not vault.is_unlocked:
        raise HTTPException(
            status_code=503,
            detail="Vault is locked. Please contact administrator to unlock the system."
        )

    link = db.query(LinkedAccount).filter(
        LinkedAccount.user_id == current_user.id,
        LinkedAccount.provider_name == provider_name
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Provider not linked")

    # Check if sync already in progress
    current_status = sync_status.get_status(current_user.id, provider_name)
    if current_status and not current_status.get("is_complete", True):
        return {"status": "in_progress", "message": "Sync already in progress"}

    # Start sync in background
    sync_status.status_starting(current_user.id, provider_name)

    background_tasks.add_task(
        run_sync_task,
        current_user.id,
        provider_name,
        link.id
    )

    return {"status": "started", "message": "Sync started. Check /sync-status for progress."}


def run_sync_task(user_id: int, provider_name: str, account_id: int):
    """Background task to run sync with status updates."""
    import asyncio
    try:
        from backend_v2.database import SessionLocal
        from backend_v2.services.crawlers_manager import run_regina_async, run_synevo_async
        from backend_v2.services.vault import vault, VaultLockedError
    except ImportError:
        from database import SessionLocal
        from services.crawlers_manager import run_regina_async, run_synevo_async
        from services.vault import vault, VaultLockedError

    # Check vault is unlocked
    if not vault.is_unlocked:
        sync_status.status_error(user_id, provider_name, "Vault is locked")
        return

    # Create new db session for background task
    db = SessionLocal()

    # Get account and decrypt credentials
    try:
        account = db.query(LinkedAccount).filter(LinkedAccount.id == account_id).first()
        if not account:
            sync_status.status_error(user_id, provider_name, "Account not found")
            db.close()
            return

        username = get_account_username(account)
        password = get_account_password(account)

        if not username or not password:
            sync_status.status_error(user_id, provider_name, "Could not decrypt credentials")
            db.close()
            return
    except VaultLockedError:
        sync_status.status_error(user_id, provider_name, "Vault locked during sync")
        db.close()
        return

    try:
        sync_status.status_logging_in(user_id, provider_name)

        # Run crawler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        if provider_name == "Regina Maria":
            res = loop.run_until_complete(run_regina_async(username, password, user_id=user_id))
        elif provider_name == "Synevo":
            res = loop.run_until_complete(run_synevo_async(username, password, user_id=user_id))
        else:
            sync_status.status_error(user_id, provider_name, "Unknown provider")
            return

        loop.close()

        if res.get("status") != "success":
            sync_status.status_error(user_id, provider_name, res.get("message", "Crawl failed"))
            return

        docs = res.get("documents", [])
        if not docs:
            sync_status.status_complete(user_id, provider_name, 0)
            return

        # Process documents
        try:
            from backend_v2.models import Document, TestResult
            from backend_v2.services.ai_service import AIService
            from backend_v2.services.biomarker_normalizer import get_canonical_name
        except ImportError:
            from models import Document, TestResult
            from services.ai_service import AIService
            from services.biomarker_normalizer import get_canonical_name

        try:
            ai_service = AIService()
        except Exception as e:
            sync_status.status_error(user_id, provider_name, f"AI Service init failed: {str(e)}")
            return

        count_processed = 0
        total_docs = len(docs)

        for i, doc_info in enumerate(docs):
            sync_status.status_processing(user_id, provider_name, i + 1, total_docs)

            # Calculate file hash for robust duplicate detection
            file_hash = calculate_file_hash(doc_info["local_path"])

            # Check for duplicate by file hash (most reliable)
            if file_hash:
                existing_by_hash = db.query(Document).filter(
                    Document.user_id == user_id,
                    Document.file_hash == file_hash
                ).first()

                if existing_by_hash:
                    # Same file already imported, skip
                    continue

            # Fallback: check by filename
            existing_doc = db.query(Document).filter(
                Document.user_id == user_id,
                Document.filename == doc_info["filename"]
            ).first()

            if existing_doc:
                continue

            # Create Document with file_hash
            try:
                new_doc = Document(
                    user_id=user_id,
                    filename=doc_info["filename"],
                    file_path=doc_info["local_path"],
                    file_hash=file_hash,
                    provider=provider_name,
                    document_date=doc_info["date"],
                    upload_date=datetime.datetime.now(),
                    is_processed=False
                )
                db.add(new_doc)
                db.commit()
                db.refresh(new_doc)
            except Exception as e:
                continue

            # AI Parse
            try:
                parsed_data = ai_service.process_document(doc_info["local_path"])

                if "results" in parsed_data and parsed_data["results"]:
                    for r in parsed_data["results"]:
                        # Handle numeric_value - try dedicated field first, then parse from value
                        numeric_val = r.get("numeric_value")
                        if numeric_val is None:
                            try:
                                numeric_val = float(r.get("value"))
                            except (TypeError, ValueError):
                                numeric_val = None

                        test_name = r.get("test_name")
                        tr = TestResult(
                            document_id=new_doc.id,
                            test_name=test_name,
                            canonical_name=get_canonical_name(test_name) if test_name else None,
                            value=str(r.get("value")),
                            numeric_value=numeric_val,
                            unit=r.get("unit"),
                            reference_range=r.get("reference_range"),
                            flags=r.get("flags", "NORMAL")
                        )
                        db.add(tr)

                    # Update document date from AI-extracted metadata
                    if "metadata" in parsed_data and parsed_data["metadata"].get("date"):
                        try:
                            extracted_date = datetime.datetime.strptime(
                                parsed_data["metadata"]["date"], "%Y-%m-%d"
                            )
                            new_doc.document_date = extracted_date
                        except (ValueError, TypeError):
                            pass  # Keep original date if parsing fails

                    # Extract patient name from document
                    if "patient_info" in parsed_data and parsed_data["patient_info"].get("full_name"):
                        new_doc.patient_name = parsed_data["patient_info"]["full_name"]

                    new_doc.is_processed = True
                    db.commit()
                    count_processed += 1
                elif "error" in parsed_data:
                    print(f"AI parsing error for {doc_info['filename']}: {parsed_data['error']}")
                    # Mark as processed but with no results to avoid re-processing
                    new_doc.is_processed = True
                    db.commit()
            except Exception as e:
                print(f"Failed to parse {doc_info['filename']}: {e}")
                # Mark document as processed to avoid re-processing loop
                new_doc.is_processed = True
                db.commit()

        sync_status.status_complete(user_id, provider_name, count_processed)

    except Exception as e:
        sync_status.status_error(user_id, provider_name, str(e))
    finally:
        db.close()


# ==================== GDPR Compliance Endpoints ====================

class DeleteAccountRequest(BaseModel):
    password: str
    confirm_deletion: bool = False


@router.get("/export-data")
def export_user_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GDPR Data Export - Download all your personal data.
    Returns a JSON object containing all user data.
    """
    from fastapi.responses import JSONResponse
    import json

    try:
        from backend_v2.models import Document, TestResult, HealthReport, Subscription, AuditLog, UserSession
    except ImportError:
        from models import Document, TestResult, HealthReport, Subscription, AuditLog, UserSession

    export_data = {
        "export_date": datetime.datetime.utcnow().isoformat(),
        "user_id": current_user.id,
        "account": {},
        "profile": {},
        "linked_accounts": [],
        "documents": [],
        "biomarkers": [],
        "health_reports": [],
        "subscription": None,
        "activity_log": []
    }

    # Account info
    export_data["account"] = {
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "email_verified": current_user.email_verified,
        "language": current_user.language,
        "is_admin": current_user.is_admin
    }

    # Profile data
    export_data["profile"] = get_profile_data(current_user)

    # Linked accounts (without passwords)
    for acc in current_user.linked_accounts:
        username = get_account_username(acc) if vault.is_unlocked else "[encrypted]"
        export_data["linked_accounts"].append({
            "provider": acc.provider_name,
            "username": username,
            "status": acc.status,
            "created_at": acc.created_at.isoformat() if acc.created_at else None,
            "last_sync": acc.last_sync.isoformat() if acc.last_sync else None
        })

    # Documents
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    for doc in documents:
        # Decrypt patient name if available
        patient_name = None
        if vault.is_unlocked and doc.patient_name_enc:
            try:
                patient_name = vault.decrypt_data(doc.patient_name_enc)
            except Exception:
                pass
        if patient_name is None:
            patient_name = doc.patient_name

        export_data["documents"].append({
            "id": doc.id,
            "filename": doc.filename,
            "provider": doc.provider,
            "document_date": doc.document_date.isoformat() if doc.document_date else None,
            "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
            "patient_name": patient_name,
            "is_processed": doc.is_processed
        })

    # Biomarkers/Test Results
    test_results = db.query(TestResult).join(Document).filter(
        Document.user_id == current_user.id
    ).all()
    for tr in test_results:
        export_data["biomarkers"].append({
            "document_id": tr.document_id,
            "test_name": tr.test_name,
            "canonical_name": tr.canonical_name,
            "value": tr.value,
            "numeric_value": tr.numeric_value,
            "unit": tr.unit,
            "reference_range": tr.reference_range,
            "flags": tr.flags
        })

    # Health Reports
    reports = db.query(HealthReport).filter(HealthReport.user_id == current_user.id).all()
    for report in reports:
        # Decrypt report content if available
        content = None
        if vault.is_unlocked and report.content_enc:
            try:
                content = vault.decrypt_data(report.content_enc)
            except Exception:
                pass
        if content is None:
            content = report.content

        export_data["health_reports"].append({
            "id": report.id,
            "report_type": report.report_type,
            "specialist_type": report.specialist_type,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "content": content,
            "summary": report.summary
        })

    # Subscription
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if subscription:
        export_data["subscription"] = {
            "tier": subscription.tier,
            "status": subscription.status,
            "billing_cycle": subscription.billing_cycle,
            "current_period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None
        }

    # Activity log (last 100 entries)
    audit_logs = db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id
    ).order_by(AuditLog.timestamp.desc()).limit(100).all()
    for log in audit_logs:
        export_data["activity_log"].append({
            "action": log.action,
            "resource_type": log.resource_type,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "ip_address": log.ip_address
        })

    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f"attachment; filename=analize_online_data_export_{datetime.datetime.now().strftime('%Y%m%d')}.json"
        }
    )


@router.delete("/account")
def delete_user_account(
    request: DeleteAccountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GDPR Account Deletion - Permanently delete your account and all data.
    Requires password confirmation and explicit consent.
    """
    import shutil

    try:
        from backend_v2.models import Document, TestResult, HealthReport, Subscription, AuditLog, UserSession
        from backend_v2.auth.security import verify_password
        from backend_v2.services.audit_service import AuditService
    except ImportError:
        from models import Document, TestResult, HealthReport, Subscription, AuditLog, UserSession
        from auth.security import verify_password
        from services.audit_service import AuditService

    # Verify password
    if not verify_password(request.password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    # Require explicit confirmation
    if not request.confirm_deletion:
        raise HTTPException(
            status_code=400,
            detail="You must confirm deletion by setting confirm_deletion to true"
        )

    # Prevent admin from deleting their own account if they're the only admin
    if current_user.is_admin:
        admin_count = db.query(User).filter(User.is_admin == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the only admin account"
            )

    user_id = current_user.id
    user_email = current_user.email

    try:
        # 1. Delete test results (cascade from documents)
        doc_ids = [d.id for d in db.query(Document.id).filter(Document.user_id == user_id).all()]
        if doc_ids:
            db.query(TestResult).filter(TestResult.document_id.in_(doc_ids)).delete(synchronize_session=False)

        # 2. Delete document files from disk
        documents = db.query(Document).filter(Document.user_id == user_id).all()
        for doc in documents:
            if doc.file_path and os.path.exists(doc.file_path):
                try:
                    os.remove(doc.file_path)
                except Exception:
                    pass  # Continue even if file deletion fails

        # 3. Delete documents from DB
        db.query(Document).filter(Document.user_id == user_id).delete(synchronize_session=False)

        # 4. Delete health reports
        db.query(HealthReport).filter(HealthReport.user_id == user_id).delete(synchronize_session=False)

        # 5. Delete linked accounts
        db.query(LinkedAccount).filter(LinkedAccount.user_id == user_id).delete(synchronize_session=False)

        # 6. Delete subscription
        db.query(Subscription).filter(Subscription.user_id == user_id).delete(synchronize_session=False)

        # 7. Delete user sessions
        db.query(UserSession).filter(UserSession.user_id == user_id).delete(synchronize_session=False)

        # 8. Anonymize audit logs (keep for compliance, but remove PII)
        db.query(AuditLog).filter(AuditLog.user_id == user_id).update({
            "user_id": None,
            "details": '{"deleted": true}',
            "ip_address": None,
            "user_agent": None
        }, synchronize_session=False)

        # 9. Delete user
        db.query(User).filter(User.id == user_id).delete(synchronize_session=False)

        # Commit all deletions
        db.commit()

        return {
            "status": "success",
            "message": f"Account {user_email} and all associated data have been permanently deleted"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete account: {str(e)}"
        )
