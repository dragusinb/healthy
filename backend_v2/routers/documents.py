from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os
import datetime

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, Document, TestResult, HealthReport
    from backend_v2.routers.auth import oauth2_scheme
    from backend_v2.services.ai_parser import AIParser
except ImportError:
    from database import get_db
    from models import User, Document, TestResult, HealthReport
    from routers.auth import oauth2_scheme
    from services.ai_parser import AIParser

router = APIRouter(prefix="/documents", tags=["documents"])

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from jose import jwt
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
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.get("/")
def list_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Explicitly filter by user_id to ensure proper isolation
    # Sort by document_date (test date) descending - newest first
    # Fall back to upload_date if document_date is null
    from sqlalchemy import func, case
    docs = db.query(Document).filter(Document.user_id == current_user.id).order_by(
        func.coalesce(Document.document_date, Document.upload_date).desc()
    ).all()
    return [{
        "id": d.id,
        "filename": d.filename,
        "provider": d.provider,
        "upload_date": d.upload_date.isoformat() if d.upload_date else None,
        "document_date": d.document_date.isoformat() if d.document_date else None,
        "is_processed": d.is_processed,
        "patient_name": d.patient_name
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
            if doc.file_path and os.path.exists(doc.file_path):
                # Create a meaningful filename with date
                date_str = doc.document_date.strftime("%Y-%m-%d") if doc.document_date else "unknown"
                provider = doc.provider or "Unknown"
                # Clean filename
                safe_name = f"{date_str}_{provider}_{doc.filename}"
                safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._- ")
                zip_file.write(doc.file_path, safe_name)

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=medical_documents_{current_user.id}.zip"}
    )


@router.get("/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Download/view a document PDF."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Security: Validate file path belongs to user's directory
    # Normalize path to prevent directory traversal attacks
    real_path = os.path.realpath(doc.file_path)
    user_data_dir = os.path.realpath(f"data/raw/{current_user.id}")
    # Also allow legacy paths for backwards compatibility during migration
    if not (real_path.startswith(user_data_dir) or f"/{current_user.id}/" in real_path):
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

    results = db.query(TestResult).filter(TestResult.document_id == doc_id).all()

    return {
        "document": {
            "id": doc.id,
            "filename": doc.filename,
            "date": doc.document_date.strftime("%Y-%m-%d") if doc.document_date else None,
            "provider": doc.provider
        },
        "biomarkers": [{
            "id": r.id,
            "name": r.test_name,
            "value": r.numeric_value if r.numeric_value is not None else r.value,
            "unit": r.unit,
            "range": r.reference_range,
            "status": "normal" if r.flags == "NORMAL" else ("low" if r.flags == "LOW" else "high"),
            "flags": r.flags
        } for r in results]
    }

@router.post("/upload")
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Save file
    safe_filename = file.filename
    upload_dir = f"data/uploads/{current_user.id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create DB Entry
    doc = Document(
        user_id=current_user.id,
        filename=safe_filename,
        file_path=file_path,
        provider="Upload",
        upload_date=datetime.datetime.now(),
        is_processed=False
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # Trigger Async Processing (Synchronous for now)
    process_document(doc.id, db)
    
    return doc

def process_document(doc_id: int, db: Session):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return
        
    # Read text (simplified, assuming PDF)
    import pdfplumber
    full_text = ""
    try:
        with pdfplumber.open(doc.file_path) as pdf:
            for page in pdf.pages:
                full_text += (page.extract_text() or "") + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return

    # AI Parse
    parser = AIParser() # Ensure API Key is set in ENV
    result = parser.parse_text(full_text)
    
    if "results" in result:
        for r in result["results"]:
             tr = TestResult(
                 document_id=doc.id,
                 test_name=r.get("test_name"),
                 value=str(r.get("value")),
                 unit=r.get("unit"),
                 reference_range=r.get("reference_range"),
                 flags=r.get("flags", "NORMAL"),
                 numeric_value= _safe_float(r.get("value"))
             )
             db.add(tr)
        
        doc.is_processed = True
        
        # Update provider/date if found
        meta = result.get("metadata", {})
        if "provider" in meta:
            doc.provider = meta["provider"]
        if "date" in meta:
            try:
                doc.document_date = datetime.datetime.strptime(meta["date"], "%Y-%m-%d")
            except: pass

        # Extract patient name if found
        patient_info = result.get("patient_info", {})
        if patient_info.get("full_name"):
            doc.patient_name = patient_info["full_name"]

        db.commit()

def _safe_float(val):
    try:
        return float(val)
    except:
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
    regenerate_reports: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document and its associated biomarkers. Optionally regenerate health reports."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete associated test results
    db.query(TestResult).filter(TestResult.document_id == doc_id).delete()

    # Delete the file from disk if it exists
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            print(f"Warning: Could not delete file {doc.file_path}: {e}")

    # Delete the document record
    db.delete(doc)

    # Delete existing health reports (they're now outdated)
    if regenerate_reports:
        db.query(HealthReport).filter(HealthReport.user_id == current_user.id).delete()

    db.commit()

    return {
        "status": "success",
        "message": "Document deleted successfully",
        "reports_cleared": regenerate_reports
    }
