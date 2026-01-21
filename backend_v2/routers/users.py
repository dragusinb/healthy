from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend_v2.database import get_db
from backend_v2.models import User, LinkedAccount
from backend_v2.routers.documents import get_current_user
from backend_v2.services import sync_status
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


def run_sync_task(user_id: int, provider_name: str, username: str, password: str):
    """Background task to run sync with status updates."""
    import asyncio
    from backend_v2.database import SessionLocal
    from backend_v2.services.crawlers_manager import run_regina_async, run_synevo_async

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
        from backend_v2.models import Document, TestResult
        from backend_v2.services.ai_service import AIService

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

                    # Update document date from AI-extracted metadata
                    if "metadata" in parsed_data and parsed_data["metadata"].get("date"):
                        try:
                            extracted_date = datetime.datetime.strptime(
                                parsed_data["metadata"]["date"], "%Y-%m-%d"
                            )
                            new_doc.document_date = extracted_date
                        except:
                            pass  # Keep original date if parsing fails

                    new_doc.is_processed = True
                    db.commit()
                    count_processed += 1
            except Exception as e:
                print(f"Failed to parse {doc_info['filename']}: {e}")

        sync_status.status_complete(user_id, provider_name, count_processed)

    except Exception as e:
        sync_status.status_error(user_id, provider_name, str(e))
    finally:
        db.close()
