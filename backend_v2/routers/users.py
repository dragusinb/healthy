from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend_v2.database import get_db
from backend_v2.models import User, LinkedAccount
from backend_v2.routers.documents import get_current_user
import datetime



router = APIRouter(prefix="/users", tags=["users"])

class LinkedAccountCreate(BaseModel):
    provider_name: str
    username: str
    password: str

@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "id": current_user.id,
        "linked_accounts": current_user.linked_accounts
    }

@router.post("/link-account")
def link_account(account: LinkedAccountCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check if exists
    existing = db.query(LinkedAccount).filter(
        LinkedAccount.user_id == current_user.id,
        LinkedAccount.provider_name == account.provider_name
    ).first()
    
    if existing:
        existing.username = account.username
        existing.encrypted_password = account.password # TODO: Encrypt
        db.commit()
        return {"message": "Account updated"}
    
    new_link = LinkedAccount(
        user_id=current_user.id,
        provider_name=account.provider_name,
        username=account.username,
        encrypted_password=account.password # TODO: Encrypt
    )
    db.add(new_link)
    db.commit()
    return {"message": "Account linked"}

@router.post("/sync/{provider_name}")
async def sync_provider(provider_name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    link = db.query(LinkedAccount).filter(
        LinkedAccount.user_id == current_user.id,
        LinkedAccount.provider_name == provider_name
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Provider not linked")
        
    # Trigger Crawl
    from backend_v2.services.crawlers_manager import run_regina_async, run_synevo_async
    
    if provider_name == "Regina Maria":
        res = await run_regina_async(link.username, link.encrypted_password)
    elif provider_name == "Synevo":
        res = await run_synevo_async(link.username, link.encrypted_password)
    else:
        raise HTTPException(status_code=400, detail="Unknown provider")

        
    
    if res.get("status") == "success" and "documents" in res:
        docs = res["documents"]
        from backend_v2.models import Document, TestResult
        from backend_v2.services.ai_service import AIService
        
        try:
            ai_service = AIService()
        except Exception as e:
            return {"status": "warning", "message": f"Crawler finished, but AI Service failed to init: {str(e)}", "processed_count": 0}
        
        count_processed = 0
        errors = []
        
        for doc_info in docs:
            # Check if exists
            existing_doc = db.query(Document).filter(
                Document.user_id == current_user.id,
                Document.filename == doc_info["filename"]
            ).first()
            
            if existing_doc:
                continue # Skip duplicates
                
            # Create Document
            try:
                new_doc = Document(
                    user_id=current_user.id,
                    filename=doc_info["filename"],
                    file_path=doc_info["local_path"],
                    provider=provider_name,
                    document_date=doc_info["date"],
                    upload_date=datetime.datetime.now(),
                    is_processed=False
                )
                db.add(new_doc)
                db.commit() # Commit to get ID
                db.refresh(new_doc)
            except Exception as e:
                errors.append(f"DB Insert Error ({doc_info['filename']}): {str(e)}")
                continue

            # AI Parse
            try:
                print(f"Parsing document: {doc_info['local_path']}")
                parsed_data = ai_service.process_document(doc_info["local_path"])
                
                if "error" in parsed_data:
                    errors.append(f"AI Error ({doc_info['filename']}): {parsed_data['error']}")
                
                if "results" in parsed_data:
                    for r in parsed_data["results"]:
                        tr = TestResult(
                            document_id=new_doc.id,
                            test_name=r.get("test_name"),
                            value=str(r.get("value")),
                            numeric_value=r.get("numeric_value") if r.get("numeric_value") else None,
                            unit=r.get("unit"),
                            reference_range=r.get("reference_range"),
                            flags=r.get("flags", "NORMAL")
                        )
                        db.add(tr)
                    
                    new_doc.is_processed = True
                    db.commit()
                    count_processed += 1
            except Exception as e:
                errors.append(f"Parse Exception ({doc_info['filename']}): {str(e)}")
                print(f"Failed to parse {new_doc.filename}: {e}")
                
        res["processed_count"] = count_processed
        if errors:
            # If we processed some but had errors, show warning
            if count_processed > 0:
                 res["message"] = f"Processed {count_processed} docs. Errors: {'; '.join(errors[:3])}..."
            else:
                 res["status"] = "error" 
                 res["message"] = f"Failed to process documents: {'; '.join(errors[:3])}"
        
    return res
