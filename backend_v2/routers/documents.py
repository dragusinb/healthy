from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os
import datetime
import logging

from pathlib import Path
from io import BytesIO

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, Document, TestResult, HealthReport
    from backend_v2.routers.auth import oauth2_scheme
    from backend_v2.services.ai_parser import AIParser
    from backend_v2.services.biomarker_normalizer import get_canonical_name
    from backend_v2.services.vault_helper import get_vault_helper
    from backend_v2.services.vault import VaultLockedError
    from backend_v2.services.subscription_service import SubscriptionService
    from backend_v2.services.audit_service import AuditService
    from backend_v2.services.biomarker_categories import get_category_keywords, get_all_categories
except ImportError:
    from database import get_db
    from models import User, Document, TestResult, HealthReport
    from routers.auth import oauth2_scheme
    from services.ai_parser import AIParser
    from services.biomarker_normalizer import get_canonical_name
    from services.vault_helper import get_vault_helper
    from services.vault import VaultLockedError
    from services.subscription_service import SubscriptionService
    from services.audit_service import AuditService
    from services.biomarker_categories import get_category_keywords, get_all_categories


def get_encrypted_storage_path() -> Path:
    """Get path to encrypted file storage."""
    path = Path("data/encrypted")
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_document_content(doc: Document, user_id: int = None) -> bytes:
    """Read document content, decrypting if necessary.

    Args:
        doc: Document object
        user_id: User ID for per-user vault
    """
    # Try encrypted path first if available
    if doc.is_encrypted and doc.encrypted_path:
        vault_helper = get_vault_helper(user_id)

        # Check if vault is available
        if vault_helper.is_available:
            # Security: Validate encrypted path belongs to user's encrypted directory
            real_path = os.path.normpath(os.path.realpath(doc.encrypted_path))
            expected_pattern = f"/encrypted/{user_id}/"
            alt_pattern = f"\\encrypted\\{user_id}\\"  # Windows compatibility

            if expected_pattern not in real_path and alt_pattern not in real_path:
                logging.warning(f"Encrypted path traversal blocked: user={user_id}, path={doc.encrypted_path}")
                raise HTTPException(status_code=403, detail="Access denied")

            # Try to decrypt if file exists
            if os.path.exists(real_path):
                try:
                    encrypted_content = Path(real_path).read_bytes()
                    return vault_helper.decrypt_document(encrypted_content)
                except (VaultLockedError, Exception) as e:
                    # Decryption failed - fall back to unencrypted file if available
                    logging.warning(f"Decryption failed for doc {doc.id}, trying unencrypted: {e}")

    # Fall back to unencrypted file
    if doc.file_path and os.path.exists(doc.file_path):
        return Path(doc.file_path).read_bytes()

    raise HTTPException(status_code=404, detail="File not found")


def save_document_encrypted(content: bytes, user_id: int, doc_id: int) -> str:
    """Save document with vault encryption. Returns encrypted file path.

    Uses per-user vault if available, otherwise falls back to global vault.
    """
    vault_helper = get_vault_helper(user_id)
    if not vault_helper.is_available:
        raise HTTPException(
            status_code=503,
            detail="Your vault is locked. Please log out and log back in."
        )
    encrypted_content = vault_helper.encrypt_document(content)

    # Save to encrypted storage
    user_dir = get_encrypted_storage_path() / str(user_id)
    user_dir.mkdir(exist_ok=True)
    encrypted_path = user_dir / f"{doc_id}.enc"
    encrypted_path.write_bytes(encrypted_content)

    return str(encrypted_path)

router = APIRouter(prefix="/documents", tags=["documents"])

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from jose import jwt
    from sqlalchemy.orm import joinedload
    try:
        from backend_v2.auth.security import SECRET_KEY, ALGORITHM
    except ImportError:
        from auth.security import SECRET_KEY, ALGORITHM

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Eager load linked_accounts to avoid N+1 queries in /users/me endpoint
    user = db.query(User).options(
        joinedload(User.linked_accounts)
    ).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.get("/stats")
def get_document_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document statistics by provider."""
    from sqlalchemy import func

    # Count documents by provider
    provider_counts = db.query(
        Document.provider,
        func.count(Document.id).label('count')
    ).filter(
        Document.user_id == current_user.id
    ).group_by(Document.provider).all()

    # Count total biomarkers
    total_biomarkers = db.query(func.count(TestResult.id)).join(Document).filter(
        Document.user_id == current_user.id
    ).scalar()

    # Build response
    by_provider = {provider: count for provider, count in provider_counts}
    total_documents = sum(by_provider.values())

    return {
        "total_documents": total_documents,
        "total_biomarkers": total_biomarkers,
        "by_provider": by_provider
    }


@router.get("/")
def list_documents(
    limit: int = None,
    offset: int = 0,
    provider: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's documents with optional pagination and filtering."""
    # Explicitly filter by user_id to ensure proper isolation
    # Sort by document_date (test date) descending - newest first
    # Fall back to upload_date if document_date is null
    from sqlalchemy import func
    query = db.query(Document).filter(Document.user_id == current_user.id)

    # Optional provider filter
    if provider:
        query = query.filter(Document.provider == provider)

    # Sort by date
    query = query.order_by(func.coalesce(Document.document_date, Document.upload_date).desc())

    # Apply pagination
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)

    docs = query.all()
    return [{
        "id": d.id,
        "filename": d.filename,
        "provider": d.provider,
        "upload_date": d.upload_date.isoformat() if d.upload_date else None,
        "document_date": d.document_date.isoformat() if d.document_date else None,
        "is_processed": d.is_processed,
        "patient_name": d.patient_name,
        "patient_cnp_prefix": d.patient_cnp_prefix
    } for d in docs]


@router.get("/download-all")
def download_all_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Download all user documents as a ZIP archive."""
    import zipfile
    import tempfile
    from fastapi.responses import StreamingResponse
    import io

    docs = db.query(Document).filter(Document.user_id == current_user.id).all()

    if not docs:
        raise HTTPException(status_code=404, detail="No documents found")

    # Create a ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for doc in docs:
            try:
                # Read content (handles encryption)
                content = read_document_content(doc, current_user.id)

                # Create a meaningful filename with date
                date_str = doc.document_date.strftime("%Y-%m-%d") if doc.document_date else "unknown"
                provider = doc.provider or "Unknown"
                # Clean filename
                safe_name = f"{date_str}_{provider}_{doc.filename}"
                safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._- ")

                zip_file.writestr(safe_name, content)
            except Exception as e:
                # Skip files that can't be read
                continue

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=medical_documents_{current_user.id}.zip"}
    )


@router.get("/download-by-biomarker/{biomarker_name}")
def download_documents_by_biomarker(
    biomarker_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download documents containing a specific biomarker as a ZIP archive."""
    import zipfile
    from fastapi.responses import StreamingResponse
    import io
    from urllib.parse import unquote

    # Decode URL-encoded biomarker name
    decoded_name = unquote(biomarker_name)

    # Find document IDs with matching biomarkers
    matching_results = db.query(TestResult.document_id).join(Document).filter(
        Document.user_id == current_user.id
    ).filter(
        (TestResult.canonical_name.ilike(f"%{decoded_name}%")) |
        (TestResult.test_name.ilike(f"%{decoded_name}%"))
    ).distinct().all()

    doc_ids = [r.document_id for r in matching_results]

    if not doc_ids:
        raise HTTPException(status_code=404, detail="No documents found with this biomarker")

    # Get the documents
    docs = db.query(Document).filter(
        Document.id.in_(doc_ids),
        Document.user_id == current_user.id
    ).all()

    if not docs:
        raise HTTPException(status_code=404, detail="No documents found")

    # Create a ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for doc in docs:
            try:
                content = read_document_content(doc, current_user.id)
                date_str = doc.document_date.strftime("%Y-%m-%d") if doc.document_date else "unknown"
                provider = doc.provider or "Unknown"
                safe_name = f"{date_str}_{provider}_{doc.filename}"
                safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._- ")
                zip_file.writestr(safe_name, content)
            except Exception as e:
                logging.warning(f"Could not include document {doc.id} in ZIP: {e}")
                continue

    zip_buffer.seek(0)

    # Create safe filename for the biomarker
    safe_biomarker = "".join(c for c in decoded_name if c.isalnum() or c in "_- ").replace(" ", "_")

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=analize_{safe_biomarker}.zip"}
    )


@router.get("/download-by-category/{category}")
def download_documents_by_category(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download documents containing biomarkers from a specific category as a ZIP archive."""
    import zipfile
    from fastapi.responses import StreamingResponse
    import io
    from sqlalchemy import or_

    # Validate category
    valid_categories = get_all_categories()
    if category.lower() not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Valid categories: {', '.join(valid_categories)}"
        )

    # Get keywords for the category
    keywords = get_category_keywords(category)

    if not keywords:
        raise HTTPException(status_code=400, detail="Category has no keywords defined")

    # Build filter conditions for each keyword
    keyword_filters = []
    for kw in keywords:
        keyword_filters.append(TestResult.canonical_name.ilike(f"%{kw}%"))
        keyword_filters.append(TestResult.test_name.ilike(f"%{kw}%"))

    # Find document IDs with matching biomarkers
    matching_results = db.query(TestResult.document_id).join(Document).filter(
        Document.user_id == current_user.id
    ).filter(or_(*keyword_filters)).distinct().all()

    doc_ids = [r.document_id for r in matching_results]

    if not doc_ids:
        raise HTTPException(status_code=404, detail="No documents found for this category")

    # Get the documents
    docs = db.query(Document).filter(
        Document.id.in_(doc_ids),
        Document.user_id == current_user.id
    ).all()

    if not docs:
        raise HTTPException(status_code=404, detail="No documents found")

    # Create a ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for doc in docs:
            try:
                content = read_document_content(doc, current_user.id)
                date_str = doc.document_date.strftime("%Y-%m-%d") if doc.document_date else "unknown"
                provider = doc.provider or "Unknown"
                safe_name = f"{date_str}_{provider}_{doc.filename}"
                safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._- ")
                zip_file.writestr(safe_name, content)
            except Exception as e:
                logging.warning(f"Could not include document {doc.id} in ZIP: {e}")
                continue

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=analize_{category}.zip"}
    )


@router.get("/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Download/view a document PDF."""
    from fastapi.responses import StreamingResponse

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Handle encrypted documents
    if doc.is_encrypted and doc.encrypted_path:
        content = read_document_content(doc, current_user.id)
        return StreamingResponse(
            BytesIO(content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={doc.filename}"}
        )

    # Handle legacy unencrypted documents
    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Security: Validate file path belongs to user's directory
    real_path = os.path.normpath(os.path.realpath(doc.file_path))
    user_data_dir = os.path.normpath(os.path.realpath(f"data/raw/{current_user.id}"))

    try:
        common = os.path.commonpath([real_path, user_data_dir])
        is_inside_user_dir = (common == user_data_dir)
    except ValueError:
        is_inside_user_dir = False

    # Legacy path check
    user_id_str = str(current_user.id)
    path_parts = real_path.replace('\\', '/').split('/')
    is_legacy_path = user_id_str in path_parts

    if not (is_inside_user_dir or is_legacy_path):
        import logging
        logging.warning(f"Path traversal blocked: user={current_user.id}, path={doc.file_path}")
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        doc.file_path,
        media_type="application/pdf",
        filename=doc.filename
    )


@router.get("/{doc_id}/biomarkers")
def get_document_biomarkers(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all biomarkers from a specific document."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get user's vault helper
    vault_helper = get_vault_helper(current_user.id)

    results = db.query(TestResult).filter(TestResult.document_id == doc_id).all()

    biomarkers = []
    for r in results:
        # Get values, preferring vault-encrypted
        value = None
        numeric_value = None

        if vault_helper.is_available:
            try:
                if r.value_enc:
                    value = vault_helper.decrypt_data(r.value_enc)
                if r.numeric_value_enc:
                    numeric_value = vault_helper.decrypt_number(r.numeric_value_enc)
            except Exception:
                pass

        # Fall back to legacy
        if value is None:
            value = r.value
        if numeric_value is None:
            numeric_value = r.numeric_value

        biomarkers.append({
            "id": r.id,
            "name": r.test_name,
            "value": numeric_value if numeric_value is not None else value,
            "unit": r.unit,
            "range": r.reference_range,
            "status": "normal" if r.flags == "NORMAL" else ("low" if r.flags == "LOW" else "high"),
            "flags": r.flags
        })

    return {
        "document": {
            "id": doc.id,
            "filename": doc.filename,
            "date": doc.document_date.strftime("%Y-%m-%d") if doc.document_date else None,
            "provider": doc.provider
        },
        "biomarkers": biomarkers
    }

# Maximum file upload size: 20MB
MAX_UPLOAD_SIZE_MB = 20
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

@router.post("/upload")
def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    audit = AuditService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Check subscription quota
    subscription_service = SubscriptionService(db)
    can_upload, message = subscription_service.check_can_upload_document(current_user.id)
    if not can_upload:
        audit.log_action(
            user_id=current_user.id,
            action="document_upload",
            resource_type="document",
            details={"filename": file.filename, "reason": "quota_exceeded"},
            ip_address=ip_address,
            user_agent=user_agent,
            status="blocked"
        )
        raise HTTPException(status_code=403, detail=message)

    # Validate file extension
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Check file size by reading in chunks
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    # Read and count size first
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    # Validate PDF magic bytes (file starts with %PDF)
    magic_bytes = file.file.read(4)
    file.file.seek(0)  # Reset to beginning
    if magic_bytes != b'%PDF':
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file. File content does not match PDF format."
        )

    if file_size > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE_MB}MB"
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file not allowed")

    # Read file content
    safe_filename = file.filename
    content = file.file.read()

    # Create DB Entry first to get ID
    doc = Document(
        user_id=current_user.id,
        filename=safe_filename,
        provider="Upload",
        upload_date=datetime.datetime.now(),
        is_processed=False
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Save file - encrypted if user's vault is unlocked, otherwise plaintext
    vault_helper = get_vault_helper(current_user.id)
    if vault_helper.is_available:
        encrypted_path = save_document_encrypted(content, current_user.id, doc.id)
        doc.encrypted_path = encrypted_path
        doc.is_encrypted = True
    else:
        # Fall back to unencrypted storage
        upload_dir = f"data/uploads/{current_user.id}"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, safe_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        doc.file_path = file_path
        doc.is_encrypted = False

    db.commit()
    db.refresh(doc)

    # Log successful upload
    audit.log_action(
        user_id=current_user.id,
        action="document_upload",
        resource_type="document",
        resource_id=doc.id,
        details={"filename": safe_filename, "size_bytes": file_size},
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )

    # Track usage
    audit.track_usage(current_user.id, "documents_uploaded", 1)

    # Trigger Processing
    process_document(doc.id, db)

    return doc

def process_document(doc_id: int, db: Session):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return

    # Get user's vault helper
    vault_helper = get_vault_helper(doc.user_id)

    # Read PDF content - handle both encrypted and unencrypted
    import pdfplumber
    full_text = ""
    try:
        # Try to read content (handles encryption if needed)
        if doc.is_encrypted and doc.encrypted_path:
            content = read_document_content(doc, doc.user_id)
            pdf_file = BytesIO(content)
        elif doc.file_path and os.path.exists(doc.file_path):
            pdf_file = doc.file_path
        else:
            logging.error(f"No valid file path for document {doc.id}")
            return

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                full_text += (page.extract_text() or "") + "\n"
    except Exception as e:
        logging.error(f"Error reading PDF for document {doc.id}: {e}")
        return

    # AI Parse
    parser = AIParser() # Ensure API Key is set in ENV
    result = parser.parse_text(full_text)

    if "results" in result:
        for r in result["results"]:
             test_name = r.get("test_name")
             value_str = str(r.get("value"))
             numeric_val = _safe_float(r.get("value"))

             tr = TestResult(
                 document_id=doc.id,
                 test_name=test_name,
                 canonical_name=get_canonical_name(test_name) if test_name else None,
                 unit=r.get("unit"),
                 reference_range=r.get("reference_range"),
                 flags=r.get("flags", "NORMAL"),
             )

             # Encrypt values if user's vault is unlocked
             if vault_helper.is_available:
                 tr.value_enc = vault_helper.encrypt_data(value_str)
                 if numeric_val is not None:
                     tr.numeric_value_enc = vault_helper.encrypt_number(numeric_val)
             else:
                 # Fall back to unencrypted storage
                 tr.value = value_str
                 tr.numeric_value = numeric_val

             db.add(tr)
        
        doc.is_processed = True
        
        # Update provider/date if found
        meta = result.get("metadata", {})
        if "provider" in meta:
            doc.provider = meta["provider"]
        if "date" in meta:
            try:
                doc.document_date = datetime.datetime.strptime(meta["date"], "%Y-%m-%d")
            except (ValueError, TypeError) as e:
                import logging
                logging.warning(f"Invalid date format in document {doc.id}: {meta['date']} - {e}")

        # Extract patient info if found
        patient_info = result.get("patient_info", {})
        if patient_info.get("full_name"):
            doc.patient_name = patient_info["full_name"]

        # Extract CNP prefix for unique patient identification
        cnp_prefix = patient_info.get("cnp_prefix")
        if cnp_prefix and len(cnp_prefix) >= 7:
            doc.patient_cnp_prefix = cnp_prefix[:7]

        # Auto-populate user's blood type if found in document and not already set
        blood_type = patient_info.get("blood_type")
        if blood_type and not doc.user.blood_type:
            valid_blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
            if blood_type in valid_blood_types:
                user = db.query(User).filter(User.id == doc.user_id).first()
                if user and not user.blood_type:
                    user.blood_type = blood_type

        db.commit()

def _safe_float(val):
    """Safely convert a value to float, returning None on failure."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


@router.post("/rescan-patient-names")
def rescan_patient_names(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Rescan all documents to extract and populate patient names.
    Only rescans documents where patient_name is null.
    """
    import pdfplumber

    # Get all user's documents without patient_name
    docs = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.patient_name == None
    ).all()

    if not docs:
        return {"status": "success", "message": "No documents need rescanning", "updated": 0}

    parser = AIParser()
    updated_count = 0
    errors = []

    for doc in docs:
        try:
            if not doc.file_path or not os.path.exists(doc.file_path):
                errors.append(f"{doc.filename}: File not found")
                continue

            # Read PDF text
            full_text = ""
            with pdfplumber.open(doc.file_path) as pdf:
                for page in pdf.pages:
                    full_text += (page.extract_text() or "") + "\n"

            if not full_text.strip():
                errors.append(f"{doc.filename}: No text extracted")
                continue

            # Use the profile extraction method which is optimized for patient info
            result = parser.extract_profile(full_text)
            profile = result.get("profile", {})

            if profile.get("full_name"):
                doc.patient_name = profile["full_name"]
                updated_count += 1

            # Also extract CNP prefix for patient identification
            cnp_prefix = profile.get("cnp_prefix")
            if cnp_prefix and len(cnp_prefix) >= 7:
                doc.patient_cnp_prefix = cnp_prefix[:7]

        except Exception as e:
            errors.append(f"{doc.filename}: {str(e)}")

    db.commit()

    return {
        "status": "success",
        "message": f"Rescanned {len(docs)} documents, updated {updated_count} with patient names",
        "updated": updated_count,
        "total_scanned": len(docs),
        "errors": errors if errors else None
    }


@router.delete("/{doc_id}")
def delete_document(
    doc_id: int,
    request: Request,
    regenerate_reports: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document and its associated biomarkers. Optionally regenerate health reports."""
    audit = AuditService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Store document info for audit log before deletion
    doc_filename = doc.filename

    # Delete associated test results
    db.query(TestResult).filter(TestResult.document_id == doc_id).delete()

    # Delete the file from disk if it exists
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logging.warning(f"Could not delete file {doc.file_path}: {e}")

    # Delete encrypted file if exists
    if doc.encrypted_path and os.path.exists(doc.encrypted_path):
        try:
            os.remove(doc.encrypted_path)
        except Exception as e:
            logging.warning(f"Could not delete encrypted file {doc.encrypted_path}: {e}")

    # Delete the document record
    db.delete(doc)

    # Delete existing health reports (they're now outdated)
    if regenerate_reports:
        db.query(HealthReport).filter(HealthReport.user_id == current_user.id).delete()

    db.commit()

    # Log document deletion
    audit.log_action(
        user_id=current_user.id,
        action="document_delete",
        resource_type="document",
        resource_id=doc_id,
        details={"filename": doc_filename, "reports_cleared": regenerate_reports},
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )

    return {
        "status": "success",
        "message": "Document deleted successfully",
        "reports_cleared": regenerate_reports
    }
