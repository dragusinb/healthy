"""Admin API router for monitoring and management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import psutil
import os
from datetime import datetime, timedelta

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, Document, TestResult, LinkedAccount, HealthReport, SyncJob
    from backend_v2.routers.documents import get_current_user
except ImportError:
    from database import get_db
    from models import User, Document, TestResult, LinkedAccount, HealthReport, SyncJob
    from routers.documents import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require admin access."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Get overall system statistics."""
    # User stats
    total_users = db.query(User).count()
    active_users_24h = db.query(User).filter(
        User.created_at > datetime.utcnow() - timedelta(hours=24)
    ).count()

    # Document stats
    total_documents = db.query(Document).count()
    processed_documents = db.query(Document).filter(Document.is_processed == True).count()
    pending_documents = db.query(Document).filter(Document.is_processed == False).count()

    # Biomarker stats
    total_biomarkers = db.query(TestResult).count()
    abnormal_biomarkers = db.query(TestResult).filter(TestResult.flags != "NORMAL").count()

    # Linked accounts stats
    total_linked_accounts = db.query(LinkedAccount).count()
    syncing_accounts = db.query(LinkedAccount).filter(LinkedAccount.status == "SYNCING").count()
    error_accounts = db.query(LinkedAccount).filter(LinkedAccount.status == "ERROR").count()

    # Health reports
    total_reports = db.query(HealthReport).count()

    # Recent sync jobs
    recent_syncs = db.query(SyncJob).filter(
        SyncJob.created_at > datetime.utcnow() - timedelta(hours=24)
    ).count()
    failed_syncs_24h = db.query(SyncJob).filter(
        SyncJob.created_at > datetime.utcnow() - timedelta(hours=24),
        SyncJob.status == "failed"
    ).count()

    return {
        "users": {
            "total": total_users,
            "new_24h": active_users_24h
        },
        "documents": {
            "total": total_documents,
            "processed": processed_documents,
            "pending": pending_documents
        },
        "biomarkers": {
            "total": total_biomarkers,
            "abnormal": abnormal_biomarkers
        },
        "linked_accounts": {
            "total": total_linked_accounts,
            "syncing": syncing_accounts,
            "error": error_accounts
        },
        "health_reports": {
            "total": total_reports
        },
        "syncs": {
            "last_24h": recent_syncs,
            "failed_24h": failed_syncs_24h
        }
    }


@router.get("/server")
def get_server_stats(admin: User = Depends(require_admin)):
    """Get server resource usage."""
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()

    # Memory
    memory = psutil.virtual_memory()

    # Disk
    disk = psutil.disk_usage('/')

    # Load average (Unix only)
    try:
        load_avg = os.getloadavg()
    except (AttributeError, OSError):
        load_avg = (0, 0, 0)

    return {
        "cpu": {
            "percent": cpu_percent,
            "cores": cpu_count,
            "load_avg_1m": load_avg[0],
            "load_avg_5m": load_avg[1],
            "load_avg_15m": load_avg[2]
        },
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent": memory.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent
        }
    }


@router.get("/users")
def get_all_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Get all users with their stats."""
    users = db.query(User).all()
    result = []
    for user in users:
        doc_count = db.query(Document).filter(Document.user_id == user.id).count()
        biomarker_count = db.query(TestResult).join(Document).filter(Document.user_id == user.id).count()
        linked_count = db.query(LinkedAccount).filter(LinkedAccount.user_id == user.id).count()

        result.append({
            "id": user.id,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "language": user.language,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "documents": doc_count,
            "biomarkers": biomarker_count,
            "linked_accounts": linked_count
        })

    return result


@router.get("/sync-jobs")
def get_sync_jobs(
    limit: int = 50,
    status: str = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get recent sync jobs."""
    query = db.query(SyncJob).order_by(SyncJob.created_at.desc())

    if status:
        query = query.filter(SyncJob.status == status)

    jobs = query.limit(limit).all()

    return [{
        "id": job.id,
        "user_id": job.user_id,
        "provider_name": job.provider_name,
        "status": job.status,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "documents_found": job.documents_found,
        "documents_processed": job.documents_processed,
        "error_message": job.error_message,
        "retry_count": job.retry_count,
        "created_at": job.created_at.isoformat() if job.created_at else None
    } for job in jobs]


@router.post("/users/{user_id}/set-admin")
def set_user_admin(
    user_id: int,
    is_admin: bool = True,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Set or remove admin status for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_admin = is_admin
    db.commit()

    return {"message": f"User {user.email} admin status set to {is_admin}"}


@router.post("/cleanup-limbo-documents")
def cleanup_limbo_documents(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Clean up documents that are stuck in unprocessed state for too long."""
    cutoff = datetime.utcnow() - timedelta(hours=1)

    # Find old unprocessed documents
    limbo_docs = db.query(Document).filter(
        Document.is_processed == False,
        Document.upload_date < cutoff
    ).all()

    cleaned = 0
    for doc in limbo_docs:
        # Delete any partial test results
        db.query(TestResult).filter(TestResult.document_id == doc.id).delete()
        # Delete the document
        db.delete(doc)
        cleaned += 1

    db.commit()

    return {"message": f"Cleaned up {cleaned} limbo documents"}


@router.post("/retry-failed-syncs")
def retry_failed_syncs(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Reset failed sync jobs for retry."""
    # Reset accounts with errors
    updated = db.query(LinkedAccount).filter(
        LinkedAccount.status == "ERROR",
        LinkedAccount.consecutive_failures < 5  # Don't retry too many times
    ).update({"status": "ACTIVE"})

    db.commit()

    return {"message": f"Reset {updated} accounts for retry"}


@router.post("/reprocess-documents")
def reprocess_pending_documents(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Manually trigger reprocessing of all unprocessed documents."""
    from threading import Thread

    try:
        from backend_v2.services.scheduler import process_pending_documents
    except ImportError:
        from services.scheduler import process_pending_documents

    # Count pending documents
    pending_count = db.query(Document).filter(Document.is_processed == False).count()

    if pending_count == 0:
        return {"message": "No pending documents to process", "pending": 0}

    # Trigger processing in background thread
    thread = Thread(target=process_pending_documents, daemon=True)
    thread.start()

    return {
        "message": f"Started processing {pending_count} pending documents",
        "pending": pending_count
    }


@router.get("/pending-documents")
def get_pending_documents(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Get list of documents that haven't been processed yet."""
    pending = db.query(Document).filter(Document.is_processed == False).all()

    return [{
        "id": doc.id,
        "user_id": doc.user_id,
        "filename": doc.filename,
        "provider": doc.provider,
        "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
        "file_path": doc.file_path
    } for doc in pending]
