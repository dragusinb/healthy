from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import datetime
import json

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, LinkedAccount
    from backend_v2.routers.documents import get_current_user
    from backend_v2.services import sync_status
    from backend_v2.auth.crypto import encrypt_password, decrypt_password
except ImportError:
    from database import get_db
    from models import User, LinkedAccount
    from routers.documents import get_current_user
    from services import sync_status
    from auth.crypto import encrypt_password, decrypt_password


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
        acc_data = {
            "id": acc.id,
            "provider_name": acc.provider_name,
            "username": acc.username,
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
        "language": current_user.language,
        "linked_accounts": linked_accounts_data,
        "profile": get_profile_data(current_user)
    }


def get_profile_data(user: User) -> dict:
    """Extract profile data from user model."""
    return {
        "full_name": user.full_name,
        "date_of_birth": user.date_of_birth.strftime("%Y-%m-%d") if user.date_of_birth else None,
        "age": calculate_age(user.date_of_birth) if user.date_of_birth else None,
        "gender": user.gender,
        "height_cm": user.height_cm,
        "weight_kg": user.weight_kg,
        "bmi": calculate_bmi(user.height_cm, user.weight_kg) if user.height_cm and user.weight_kg else None,
        "blood_type": user.blood_type,
        "allergies": json.loads(user.allergies) if user.allergies else [],
        "chronic_conditions": json.loads(user.chronic_conditions) if user.chronic_conditions else [],
        "current_medications": json.loads(user.current_medications) if user.current_medications else [],
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
    if profile.full_name is not None:
        current_user.full_name = profile.full_name

    if profile.date_of_birth is not None:
        try:
            current_user.date_of_birth = datetime.datetime.strptime(profile.date_of_birth, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    if profile.gender is not None:
        if profile.gender not in ["male", "female", "other", ""]:
            raise HTTPException(status_code=400, detail="Invalid gender value")
        current_user.gender = profile.gender if profile.gender else None

    if profile.height_cm is not None:
        current_user.height_cm = profile.height_cm

    if profile.weight_kg is not None:
        current_user.weight_kg = profile.weight_kg

    if profile.blood_type is not None:
        valid_blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", ""]
        if profile.blood_type not in valid_blood_types:
            raise HTTPException(status_code=400, detail="Invalid blood type")
        current_user.blood_type = profile.blood_type if profile.blood_type else None

    if profile.allergies is not None:
        current_user.allergies = json.dumps(profile.allergies)

    if profile.chronic_conditions is not None:
        current_user.chronic_conditions = json.dumps(profile.chronic_conditions)

    if profile.current_medications is not None:
        current_user.current_medications = json.dumps(profile.current_medications)

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
    """Scan user's documents to extract profile information using AI."""
    import os

    try:
        from backend_v2.models import Document
        from backend_v2.services.ai_parser import AIParser
    except ImportError:
        from models import Document
        from services.ai_parser import AIParser

    # Get user's processed documents (most recent first)
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
                # Focus on first 3 pages where patient info usually is
                for i, page in enumerate(pdf.pages[:3]):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return ""

    parser = AIParser()
    extracted_profiles = []
    scanned_count = 0

    for doc in documents:
        if not doc.file_path or not os.path.exists(doc.file_path):
            continue

        text = extract_text_from_pdf(doc.file_path)
        if not text:
            continue

        scanned_count += 1
        result = parser.extract_profile(text)

        if result.get("profile") and not result.get("error"):
            profile_data = result["profile"]
            profile_data["source_document"] = doc.filename
            profile_data["confidence"] = result.get("confidence", "low")
            extracted_profiles.append(profile_data)

        # Stop after finding good data
        if extracted_profiles and extracted_profiles[-1].get("confidence") == "high":
            break

    if not extracted_profiles:
        return {
            "status": "no_profile_found",
            "message": f"Scanned {scanned_count} documents but could not extract profile information",
            "profile": {}
        }

    # Merge extracted profiles (prefer higher confidence, more recent)
    merged_profile = {}
    for profile in reversed(extracted_profiles):  # Oldest first, so newer overwrites
        for key, value in profile.items():
            if value and key not in ["source_document", "confidence", "source_hints"]:
                if key not in merged_profile or profile.get("confidence") == "high":
                    merged_profile[key] = value

    # Apply to user profile (only fill empty fields)
    updates_made = []

    if merged_profile.get("full_name") and not current_user.full_name:
        current_user.full_name = merged_profile["full_name"]
        updates_made.append("full_name")

    if not current_user.date_of_birth:
        # Try direct date_of_birth first
        if merged_profile.get("date_of_birth"):
            try:
                dob = datetime.datetime.strptime(merged_profile["date_of_birth"], "%Y-%m-%d")
                current_user.date_of_birth = dob
                updates_made.append("date_of_birth")
            except:
                pass
        # Fallback: calculate from age_years if no birth date found
        elif merged_profile.get("age_years"):
            try:
                age = int(merged_profile["age_years"])
                # Approximate birth date (use January 1st of birth year)
                birth_year = datetime.date.today().year - age
                dob = datetime.datetime(birth_year, 1, 1)
                current_user.date_of_birth = dob
                updates_made.append("date_of_birth (estimated from age)")
            except (ValueError, TypeError):
                pass

    if merged_profile.get("gender") and not current_user.gender:
        if merged_profile["gender"] in ["male", "female"]:
            current_user.gender = merged_profile["gender"]
            updates_made.append("gender")

    if updates_made:
        db.commit()

    return {
        "status": "success" if updates_made else "no_new_data",
        "message": f"Updated {len(updates_made)} fields" if updates_made else "No new profile data to update (fields already filled or no data found)",
        "updates": updates_made,
        "extracted": merged_profile,
        "documents_scanned": scanned_count,
        "profile": get_profile_data(current_user)
    }


@router.post("/link-account")
def link_account(
    account: LinkedAccountCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Encrypt the password before storing
    encrypted_pwd = encrypt_password(account.password)

    # Check if exists
    existing = db.query(LinkedAccount).filter(
        LinkedAccount.user_id == current_user.id,
        LinkedAccount.provider_name == account.provider_name
    ).first()

    if existing:
        was_in_error = existing.status == 'ERROR'
        existing.username = account.username
        existing.encrypted_password = encrypted_pwd
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
                account.username,
                encrypted_pwd
            )
            return {"message": "Account updated", "sync_triggered": True}

        return {"message": "Account updated", "sync_triggered": False}

    new_link = LinkedAccount(
        user_id=current_user.id,
        provider_name=account.provider_name,
        username=account.username,
        encrypted_password=encrypted_pwd
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
        link.username,
        link.encrypted_password
    )

    return {"status": "started", "message": "Sync started. Check /sync-status for progress."}


def run_sync_task(user_id: int, provider_name: str, username: str, encrypted_password: str):
    """Background task to run sync with status updates."""
    import asyncio
    try:
        from backend_v2.database import SessionLocal
        from backend_v2.services.crawlers_manager import run_regina_async, run_synevo_async
    except ImportError:
        from database import SessionLocal
        from services.crawlers_manager import run_regina_async, run_synevo_async

    # Decrypt password for use
    password = decrypt_password(encrypted_password)

    # Create new db session for background task
    db = SessionLocal()

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

            # Check if exists
            existing_doc = db.query(Document).filter(
                Document.user_id == user_id,
                Document.filename == doc_info["filename"]
            ).first()

            if existing_doc:
                continue

            # Create Document
            try:
                new_doc = Document(
                    user_id=user_id,
                    filename=doc_info["filename"],
                    file_path=doc_info["local_path"],
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
                        except:
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
