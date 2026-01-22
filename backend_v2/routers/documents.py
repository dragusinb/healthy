from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from backend_v2.database import get_db
from backend_v2.models import User, Document, TestResult
from backend_v2.routers.auth import oauth2_scheme
from backend_v2.services.ai_parser import AIParser
import shutil
import os
import datetime

router = APIRouter(prefix="/documents", tags=["documents"])

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from jose import jwt
    from backend_v2.auth.security import SECRET_KEY, ALGORITHM
    
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
    return current_user.documents


@router.get("/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Download/view a document PDF."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

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
            
        db.commit()

def _safe_float(val):
    try:
        return float(val)
    except:
        return None
