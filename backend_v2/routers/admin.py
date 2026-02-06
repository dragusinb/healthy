"""Admin API router for monitoring and management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import psutil
import os
import subprocess
from datetime import datetime, timedelta

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, Document, TestResult, LinkedAccount, HealthReport, SyncJob, AuditLog, AbuseFlag, UsageMetrics, OpenAIUsageLog
    from backend_v2.routers.documents import get_current_user
    from backend_v2.services.audit_service import AuditService
except ImportError:
    from database import get_db
    from models import User, Document, TestResult, LinkedAccount, HealthReport, SyncJob, AuditLog, AbuseFlag, UsageMetrics, OpenAIUsageLog
    from routers.documents import get_current_user
    from services.audit_service import AuditService

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
    try:
        from backend_v2.models import Subscription
        from backend_v2.services.subscription_service import SubscriptionService
    except ImportError:
        from models import Subscription
        from services.subscription_service import SubscriptionService

    users = db.query(User).all()
    service = SubscriptionService(db)
    result = []

    for user in users:
        doc_count = db.query(Document).filter(Document.user_id == user.id).count()
        biomarker_count = db.query(TestResult).join(Document).filter(Document.user_id == user.id).count()
        linked_count = db.query(LinkedAccount).filter(LinkedAccount.user_id == user.id).count()

        # Get subscription info
        subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        tier = service.get_user_tier(user.id)

        result.append({
            "id": user.id,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "language": user.language,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "documents": doc_count,
            "biomarkers": biomarker_count,
            "linked_accounts": linked_count,
            "subscription_tier": tier,
            "subscription_status": subscription.status if subscription else "free",
            "subscription_end": subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None
        })

    return result


def interpret_sync_error(error_message: str) -> dict:
    """Interpret sync error message into user-friendly summary."""
    if not error_message:
        return {"summary": None, "category": None}

    error_lower = error_message.lower()

    # Server-side issues (XServer, display) - check FIRST before other categories
    if any(phrase in error_lower for phrase in ["xserver", "x server", "xvfb", "display", "headed browser", "no display"]):
        return {"summary": "Server display not available (Xvfb restart needed)", "category": "server"}
    elif "password" in error_lower or "credentials" in error_lower or "authentication" in error_lower or "login failed" in error_lower:
        return {"summary": "Wrong password or username", "category": "auth"}
    elif "captcha" in error_lower:
        return {"summary": "CAPTCHA verification required", "category": "captcha"}
    elif "timeout" in error_lower:
        return {"summary": "Connection timed out", "category": "timeout"}
    elif "connection" in error_lower or "network" in error_lower or "unreachable" in error_lower:
        return {"summary": "Provider site unreachable", "category": "network"}
    elif "maintenance" in error_lower or "unavailable" in error_lower or "503" in error_lower or "502" in error_lower:
        return {"summary": "Provider site down for maintenance", "category": "site_down"}
    elif "session" in error_lower or "expired" in error_lower:
        return {"summary": "Session expired during sync", "category": "session"}
    elif "rate limit" in error_lower or "too many" in error_lower:
        return {"summary": "Too many requests - rate limited", "category": "rate_limit"}
    elif "element" in error_lower or "selector" in error_lower or "locator" in error_lower:
        return {"summary": "Provider site layout changed", "category": "scraping"}
    elif "pdf" in error_lower or "download" in error_lower:
        return {"summary": "Failed to download documents", "category": "download"}
    else:
        return {"summary": "Unexpected error occurred", "category": "unknown"}


@router.get("/sync-jobs")
def get_sync_jobs(
    limit: int = 50,
    status: str = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get recent sync jobs with user info and interpreted errors."""
    query = db.query(SyncJob).order_by(SyncJob.created_at.desc())

    if status:
        query = query.filter(SyncJob.status == status)

    jobs = query.limit(limit).all()

    result = []
    for job in jobs:
        # Get user email
        user = db.query(User).filter(User.id == job.user_id).first()
        user_email = user.email if user else "Unknown"

        # Interpret error
        error_info = interpret_sync_error(job.error_message)

        result.append({
            "id": job.id,
            "user_id": job.user_id,
            "user_email": user_email,
            "provider_name": job.provider_name,
            "status": job.status,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "documents_found": job.documents_found,
            "documents_processed": job.documents_processed,
            "error_message": job.error_message,
            "error_summary": error_info["summary"],
            "error_category": error_info["category"],
            "retry_count": job.retry_count,
            "created_at": job.created_at.isoformat() if job.created_at else None
        })

    return result


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


@router.post("/regenerate-health-reports")
def regenerate_all_health_reports(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Regenerate health reports for all users in their preferred language."""
    from threading import Thread
    import json

    try:
        from backend_v2.models import TestResult
        from backend_v2.services.health_agents import HealthAnalysisService
    except ImportError:
        from models import TestResult
        from services.health_agents import HealthAnalysisService

    def regenerate_for_user(user_id: int, language: str):
        """Regenerate reports for a single user."""
        from database import SessionLocal
        from models import Document, TestResult, HealthReport

        db_session = SessionLocal()
        try:
            # Get user's biomarkers
            results = db_session.query(TestResult).join(Document)\
                .filter(Document.user_id == user_id)\
                .order_by(Document.document_date.desc())\
                .all()

            if not results:
                return 0

            biomarkers = []
            for r in results:
                biomarkers.append({
                    "name": r.test_name,
                    "value": r.numeric_value if r.numeric_value is not None else r.value,
                    "unit": r.unit,
                    "range": r.reference_range,
                    "date": r.document.document_date.strftime("%Y-%m-%d") if r.document.document_date else "Unknown",
                    "status": "normal" if r.flags == "NORMAL" else "abnormal",
                    "flags": r.flags
                })

            # Delete old reports
            db_session.query(HealthReport).filter(HealthReport.user_id == user_id).delete()

            # Run new analysis in user's language
            service = HealthAnalysisService(language=language)
            analysis = service.run_full_analysis(biomarkers)

            # Save general report
            general = analysis.get("general", {})
            report = HealthReport(
                user_id=user_id,
                report_type="general",
                title="Comprehensive Health Analysis",
                summary=general.get("summary", "Analysis complete"),
                findings=json.dumps(general.get("findings", [])),
                recommendations=json.dumps(general.get("recommendations", [])),
                risk_level=general.get("risk_level", "normal"),
                biomarkers_analyzed=len(biomarkers)
            )
            db_session.add(report)

            # Save specialist reports
            for specialty, specialist_data in analysis.get("specialists", {}).items():
                specialist_report = HealthReport(
                    user_id=user_id,
                    report_type=specialty,
                    title=f"{specialty.title()} Analysis",
                    summary=specialist_data.get("summary", ""),
                    findings=json.dumps(specialist_data.get("key_findings", [])),
                    recommendations=json.dumps(specialist_data.get("recommendations", [])),
                    risk_level=specialist_data.get("risk_level", "normal"),
                    biomarkers_analyzed=len(specialist_data.get("key_findings", []))
                )
                db_session.add(specialist_report)

            db_session.commit()
            return len(analysis.get("specialists", {})) + 1

        except Exception as e:
            print(f"Error regenerating for user {user_id}: {e}")
            return 0
        finally:
            db_session.close()

    def regenerate_all():
        """Background task to regenerate all reports."""
        from database import SessionLocal
        from models import User

        db_session = SessionLocal()
        try:
            users = db_session.query(User).all()
            for user in users:
                language = user.language if user.language else "ro"
                print(f"Regenerating reports for user {user.id} ({user.email}) in {language}")
                count = regenerate_for_user(user.id, language)
                print(f"  Generated {count} reports")
        finally:
            db_session.close()

    # Get count of users with biomarkers
    users_with_biomarkers = db.query(User).join(Document, Document.user_id == User.id)\
        .join(TestResult, TestResult.document_id == Document.id)\
        .distinct().count()

    # Run regeneration in background
    thread = Thread(target=regenerate_all, daemon=True)
    thread.start()

    return {
        "message": f"Started regenerating health reports for {users_with_biomarkers} users",
        "users": users_with_biomarkers
    }


@router.get("/server-logs")
def get_server_logs(lines: int = 100, admin: User = Depends(require_admin)):
    """Get recent server logs."""
    log_file = "/var/log/healthy.log"

    try:
        # Use tail to get last N lines
        result = subprocess.run(
            ["tail", "-n", str(min(lines, 500)), log_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        log_lines = result.stdout.split("\n") if result.stdout else []

        # Parse for errors and warnings
        errors = [l for l in log_lines if "ERROR" in l or "Error" in l or "error" in l]
        warnings = [l for l in log_lines if "WARNING" in l or "Warning" in l]

        return {
            "logs": log_lines[-100:],  # Last 100 lines
            "errors": errors[-20:],     # Last 20 errors
            "warnings": warnings[-20:], # Last 20 warnings
            "total_lines": len(log_lines)
        }
    except FileNotFoundError:
        return {"logs": [], "errors": [], "warnings": [], "message": "Log file not found"}
    except subprocess.TimeoutExpired:
        return {"logs": [], "errors": [], "warnings": [], "message": "Timeout reading logs"}
    except Exception as e:
        return {"logs": [], "errors": [], "warnings": [], "message": str(e)}


@router.get("/scheduler-status")
def get_scheduler_status(admin: User = Depends(require_admin)):
    """Get scheduler job information and next run times."""
    try:
        from backend_v2.services.scheduler import scheduler
    except ImportError:
        from services.scheduler import scheduler

    if not scheduler or not scheduler.running:
        return {"status": "not_running", "jobs": []}

    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name or job.id,
            "next_run": next_run.isoformat() if next_run else None,
            "trigger": str(job.trigger),
        })

    return {
        "status": "running",
        "jobs": jobs
    }


@router.post("/trigger-sync-job")
def trigger_sync_job(
    job_type: str = "provider_sync",
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Manually trigger a scheduler job."""
    from threading import Thread

    try:
        from backend_v2.services.scheduler import run_all_syncs, process_pending_documents
    except ImportError:
        from services.scheduler import run_all_syncs, process_pending_documents

    if job_type == "provider_sync":
        thread = Thread(target=run_all_syncs, daemon=True)
        thread.start()
        return {"message": "Provider sync job triggered", "job_type": job_type}
    elif job_type == "document_processing":
        thread = Thread(target=process_pending_documents, daemon=True)
        thread.start()
        return {"message": "Document processing job triggered", "job_type": job_type}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown job type: {job_type}")


@router.get("/sync-history")
def get_sync_history(
    days: int = 7,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get sync job history for visual schedule display."""
    from sqlalchemy import func, cast, Date

    cutoff = datetime.utcnow() - timedelta(days=days)

    # Get all sync jobs in the period
    jobs = db.query(SyncJob).filter(SyncJob.created_at > cutoff).order_by(SyncJob.created_at).all()

    # Group by date
    history = {}
    for job in jobs:
        date_str = job.created_at.strftime("%Y-%m-%d") if job.created_at else None
        if not date_str:
            continue

        if date_str not in history:
            history[date_str] = {"date": date_str, "total": 0, "completed": 0, "failed": 0, "jobs": []}

        history[date_str]["total"] += 1
        if job.status == "completed":
            history[date_str]["completed"] += 1
        elif job.status == "failed":
            history[date_str]["failed"] += 1

        history[date_str]["jobs"].append({
            "id": job.id,
            "provider_name": job.provider_name,
            "status": job.status,
            "time": job.created_at.strftime("%H:%M") if job.created_at else None
        })

    # Convert to list sorted by date
    result = list(history.values())
    result.sort(key=lambda x: x["date"])

    # Get next scheduled runs
    next_runs = []
    try:
        from backend_v2.services.scheduler import scheduler
    except ImportError:
        from services.scheduler import scheduler

    if scheduler and scheduler.running:
        for job in scheduler.get_jobs():
            if job.next_run_time:
                next_runs.append({
                    "job_id": job.id,
                    "next_run": job.next_run_time.isoformat()
                })

    return {
        "history": result,
        "next_runs": next_runs,
        "days": days
    }


@router.post("/scan-profiles")
def scan_documents_for_profiles(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Scan all documents and extract profile data for users who don't have complete profiles."""
    from threading import Thread
    import json

    try:
        from backend_v2.services.ai_parser import AIParser
    except ImportError:
        from services.ai_parser import AIParser

    def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return ""

    def scan_user_documents(user_id: int):
        """Scan documents for a user and extract profile data.
        OPTIMIZED: Uses batch extraction (1 API call for multiple documents).
        """
        from database import SessionLocal
        from models import User, Document
        import os

        db_session = SessionLocal()
        try:
            user = db_session.query(User).filter(User.id == user_id).first()
            if not user:
                return {"user_id": user_id, "status": "user_not_found"}

            # Check if user already has most profile data
            has_dob = user.date_of_birth is not None
            has_gender = user.gender is not None
            has_name = user.full_name is not None

            # If all basic fields are set, skip
            if has_dob and has_gender and has_name:
                return {"user_id": user_id, "status": "profile_already_complete"}

            # Get user's processed documents
            documents = db_session.query(Document).filter(
                Document.user_id == user_id,
                Document.is_processed == True
            ).order_by(Document.document_date.desc()).limit(10).all()

            if not documents:
                return {"user_id": user_id, "status": "no_documents"}

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
                        "text": text
                    })
                if len(doc_texts) >= 5:  # Max 5 documents for batch
                    break

            if not doc_texts:
                return {"user_id": user_id, "status": "no_readable_documents"}

            # OPTIMIZED: Single API call for all documents
            parser = AIParser()
            result = parser.extract_profiles_batch(doc_texts, max_docs=5)

            if result.get("error"):
                return {"user_id": user_id, "status": "error", "message": result["error"]}

            patient_info = result.get("profile", {})

            if not patient_info or not any(patient_info.values()):
                return {"user_id": user_id, "status": "no_profile_data_found"}

            # Apply profile updates (don't overwrite existing)
            profile_updates = {}

            if patient_info.get("full_name") and not user.full_name:
                profile_updates["full_name"] = patient_info["full_name"]

            if patient_info.get("date_of_birth") and not user.date_of_birth:
                try:
                    from datetime import datetime
                    dob = datetime.strptime(patient_info["date_of_birth"], "%Y-%m-%d")
                    profile_updates["date_of_birth"] = dob
                except (ValueError, TypeError):
                    pass  # Invalid date format - skip

            if patient_info.get("gender") and not user.gender:
                profile_updates["gender"] = patient_info["gender"]

            if patient_info.get("blood_type") and not user.blood_type:
                profile_updates["blood_type"] = patient_info["blood_type"]

            if patient_info.get("age_years") and not user.date_of_birth and not profile_updates.get("date_of_birth"):
                # Estimate DOB from age if no DOB found
                try:
                    from datetime import datetime
                    age = int(patient_info["age_years"])
                    estimated_dob = datetime.now().replace(year=datetime.now().year - age, month=1, day=1)
                    profile_updates["date_of_birth"] = estimated_dob
                except (ValueError, TypeError):
                    pass

            # Apply updates
            if profile_updates:
                for key, value in profile_updates.items():
                    setattr(user, key, value)
                db_session.commit()
                return {"user_id": user_id, "status": "updated", "fields": list(profile_updates.keys())}
            else:
                return {"user_id": user_id, "status": "no_new_profile_data"}

        except Exception as e:
            print(f"Error scanning for user {user_id}: {e}")
            return {"user_id": user_id, "status": "error", "message": str(e)}
        finally:
            db_session.close()

    def scan_all_users():
        """Background task to scan all users."""
        from database import SessionLocal
        from models import User

        db_session = SessionLocal()
        results = []
        try:
            users = db_session.query(User).all()
            for user in users:
                print(f"Scanning documents for user {user.id} ({user.email})")
                result = scan_user_documents(user.id)
                results.append(result)
                print(f"  Result: {result}")
        finally:
            db_session.close()
            print(f"Profile scan complete. Results: {results}")

    # Get count of users
    user_count = db.query(User).count()

    # Run scan in background
    thread = Thread(target=scan_all_users, daemon=True)
    thread.start()

    return {
        "message": f"Started scanning documents for {user_count} users",
        "users": user_count
    }


@router.get("/backups")
def get_backup_status(admin: User = Depends(require_admin)):
    """Get database backup status and list of recent backups."""
    import glob
    from pathlib import Path

    backup_dir = "/opt/healthy/backups"
    backup_pattern = f"{backup_dir}/healthy_*.sql.gz"

    backups = []
    total_size = 0

    try:
        for filepath in sorted(glob.glob(backup_pattern), reverse=True):
            path = Path(filepath)
            stat = path.stat()
            size_bytes = stat.st_size
            total_size += size_bytes

            backups.append({
                "filename": path.name,
                "size_bytes": size_bytes,
                "size_human": f"{size_bytes / 1024:.1f} KB" if size_bytes < 1024*1024 else f"{size_bytes / (1024*1024):.1f} MB",
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "backups": []
        }

    # Check if cron job is set up
    cron_active = False
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=5
        )
        cron_active = "backup_db.sh" in result.stdout
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, OSError):
        pass  # crontab not available or failed - not critical

    return {
        "status": "ok",
        "backup_dir": backup_dir,
        "total_backups": len(backups),
        "total_size_bytes": total_size,
        "total_size_human": f"{total_size / 1024:.1f} KB" if total_size < 1024*1024 else f"{total_size / (1024*1024):.1f} MB",
        "cron_active": cron_active,
        "retention_days": 7,
        "backups": backups[:10]  # Return last 10 backups
    }


@router.post("/backups/create")
def create_backup(admin: User = Depends(require_admin)):
    """Manually trigger a database backup."""
    try:
        result = subprocess.run(
            ["/opt/healthy/scripts/backup_db.sh"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Backup created successfully",
                "output": result.stdout
            }
        else:
            return {
                "status": "error",
                "message": "Backup failed",
                "output": result.stderr or result.stdout
            }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Backup timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# =============================================================================
# Biomarker Mapping Management
# =============================================================================

@router.get("/biomarker-mappings")
def get_biomarker_mappings(admin: User = Depends(require_admin)):
    """Get all biomarker canonical name mappings."""
    try:
        from backend_v2.services.biomarker_normalizer import BIOMARKER_MAPPINGS
    except ImportError:
        from services.biomarker_normalizer import BIOMARKER_MAPPINGS

    # Format for frontend display
    mappings = []
    for canonical, variants in BIOMARKER_MAPPINGS.items():
        mappings.append({
            "canonical_name": canonical,
            "variants": variants,
            "variant_count": len(variants)
        })

    # Sort by canonical name
    mappings.sort(key=lambda x: x["canonical_name"])

    return {
        "total": len(mappings),
        "mappings": mappings
    }


@router.get("/biomarker-stats")
def get_biomarker_normalization_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get statistics on biomarker name normalization."""
    from sqlalchemy import func

    # Count total biomarkers
    total = db.query(TestResult).count()

    # Count biomarkers with canonical_name set
    with_canonical = db.query(TestResult).filter(
        TestResult.canonical_name.isnot(None)
    ).count()

    # Count without canonical_name (old records)
    without_canonical = db.query(TestResult).filter(
        TestResult.canonical_name.is_(None)
    ).count()

    # Get top 20 canonical names by count
    top_canonical = db.query(
        TestResult.canonical_name,
        func.count(TestResult.id).label('count')
    ).filter(
        TestResult.canonical_name.isnot(None)
    ).group_by(
        TestResult.canonical_name
    ).order_by(
        func.count(TestResult.id).desc()
    ).limit(20).all()

    # Get unmapped test names (those where canonical_name equals test_name, meaning no mapping found)
    try:
        from backend_v2.services.biomarker_normalizer import BIOMARKER_MAPPINGS
    except ImportError:
        from services.biomarker_normalizer import BIOMARKER_MAPPINGS

    known_canonicals = set(BIOMARKER_MAPPINGS.keys())

    # Find test names that don't map to any known canonical name
    unmapped = db.query(
        TestResult.test_name,
        TestResult.canonical_name,
        func.count(TestResult.id).label('count')
    ).filter(
        TestResult.canonical_name.isnot(None),
        ~TestResult.canonical_name.in_(known_canonicals)
    ).group_by(
        TestResult.test_name,
        TestResult.canonical_name
    ).order_by(
        func.count(TestResult.id).desc()
    ).limit(30).all()

    return {
        "total_biomarkers": total,
        "with_canonical_name": with_canonical,
        "without_canonical_name": without_canonical,
        "top_canonical_names": [
            {"name": name, "count": count}
            for name, count in top_canonical
        ],
        "unmapped_test_names": [
            {"test_name": tn, "canonical_name": cn, "count": count}
            for tn, cn, count in unmapped
        ]
    }


@router.post("/run-biomarker-migration")
def run_biomarker_migration(admin: User = Depends(require_admin)):
    """Run the biomarker canonical name migration for existing records."""
    from threading import Thread
    from sqlalchemy import text

    try:
        from backend_v2.database import SessionLocal
        from backend_v2.services.biomarker_normalizer import get_canonical_name
    except ImportError:
        from database import SessionLocal
        from services.biomarker_normalizer import get_canonical_name

    def migrate_in_background():
        db = SessionLocal()
        try:
            # Get all test results without canonical_name
            result = db.execute(text("""
                SELECT id, test_name FROM test_results
                WHERE canonical_name IS NULL AND test_name IS NOT NULL
            """))

            records = result.fetchall()
            total = len(records)

            if total == 0:
                print("No records need updating.")
                return

            print(f"Migrating {total} records...")

            # Update in batches
            batch_size = 100
            updated = 0

            for i in range(0, total, batch_size):
                batch = records[i:i + batch_size]

                for row in batch:
                    record_id, test_name = row
                    canonical = get_canonical_name(test_name)

                    db.execute(text("""
                        UPDATE test_results
                        SET canonical_name = :canonical
                        WHERE id = :id
                    """), {"canonical": canonical, "id": record_id})

                db.commit()
                updated += len(batch)
                print(f"  Updated {updated}/{total} records...")

            print(f"Migration complete: {updated} records updated.")

        except Exception as e:
            print(f"Error during migration: {e}")
            db.rollback()
        finally:
            db.close()

    # Run in background
    thread = Thread(target=migrate_in_background, daemon=True)
    thread.start()

    # Return immediately
    pending = db.query(TestResult).filter(
        TestResult.canonical_name.is_(None),
        TestResult.test_name.isnot(None)
    ).count()

    return {
        "status": "started",
        "message": f"Started migration for {pending} records in background"
    }


# =============================================================================
# Audit Logging & Abuse Detection
# =============================================================================

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    user_id: int = None,
    action: str = None,
    status: str = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get audit logs with filtering."""
    audit_service = AuditService(db)
    logs = audit_service.get_recent_activity(
        limit=limit,
        user_id=user_id,
        action_filter=action
    )

    # Get total count
    query = db.query(func.count(AuditLog.id))
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if status:
        query = query.filter(AuditLog.status == status)
    total = query.scalar()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "logs": logs
    }


@router.get("/audit-logs/actions")
def get_audit_action_types(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get list of unique action types for filtering."""
    actions = db.query(AuditLog.action).distinct().all()
    return {
        "actions": [a[0] for a in actions if a[0]]
    }


@router.get("/audit-logs/user/{user_id}")
def get_user_audit_logs(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get audit logs for a specific user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    audit_service = AuditService(db)
    logs = audit_service.get_user_audit_logs(user_id, limit=limit)

    return {
        "user_id": user_id,
        "user_email": user.email,
        "logs": [
            {
                "id": log.id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "ip_address": log.ip_address,
                "status": log.status,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
    }


@router.get("/abuse-flags")
def get_abuse_flags(
    unresolved_only: bool = True,
    severity: str = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get abuse flags for review."""
    audit_service = AuditService(db)
    flags = audit_service.get_abuse_flags(
        unresolved_only=unresolved_only,
        severity=severity,
        limit=limit
    )

    # Get counts by severity
    severity_counts = db.query(
        AbuseFlag.severity,
        func.count(AbuseFlag.id)
    ).filter(
        AbuseFlag.is_resolved == False
    ).group_by(AbuseFlag.severity).all()

    return {
        "total_unresolved": sum(c for _, c in severity_counts),
        "by_severity": {s: c for s, c in severity_counts},
        "flags": flags
    }


@router.post("/abuse-flags/{flag_id}/resolve")
def resolve_abuse_flag(
    flag_id: int,
    notes: str = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Resolve an abuse flag."""
    audit_service = AuditService(db)
    audit_service.resolve_abuse_flag(flag_id, admin.id, notes)

    # Log the action
    audit_service.log_action(
        action="admin_action",
        user_id=admin.id,
        details={"action": "resolve_abuse_flag", "flag_id": flag_id, "notes": notes}
    )

    return {"status": "success", "message": "Abuse flag resolved"}


@router.get("/usage-metrics")
def get_system_usage_metrics(
    days: int = 7,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get system-wide usage metrics."""
    audit_service = AuditService(db)
    return audit_service.get_system_metrics(days)


@router.get("/usage-metrics/user/{user_id}")
def get_user_usage_metrics(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get usage metrics for a specific user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    audit_service = AuditService(db)
    metrics = audit_service.get_user_metrics(user_id, days)

    return {
        "user_id": user_id,
        "user_email": user.email,
        "period_days": days,
        "metrics": metrics
    }


@router.get("/active-sessions")
def get_all_active_sessions(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get all active user sessions."""
    from sqlalchemy import func

    try:
        from backend_v2.models import UserSession
    except ImportError:
        from models import UserSession

    # Get active sessions grouped by user
    sessions = db.query(UserSession).filter(
        UserSession.is_active == True
    ).order_by(UserSession.last_activity.desc()).limit(100).all()

    # Group by user
    user_sessions = {}
    for session in sessions:
        uid = session.user_id
        if uid not in user_sessions:
            user = db.query(User).filter(User.id == uid).first()
            user_sessions[uid] = {
                "user_id": uid,
                "user_email": user.email if user else "Unknown",
                "sessions": []
            }
        user_sessions[uid]["sessions"].append({
            "id": session.id,
            "ip_address": session.ip_address,
            "user_agent": session.user_agent[:100] if session.user_agent else None,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "last_activity": session.last_activity.isoformat() if session.last_activity else None,
        })

    return {
        "total_active_sessions": len(sessions),
        "unique_users": len(user_sessions),
        "users": list(user_sessions.values())
    }


@router.post("/users/{user_id}/end-all-sessions")
def end_user_sessions(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """End all sessions for a user (force logout)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    audit_service = AuditService(db)
    audit_service.end_all_sessions(user_id)

    # Log the admin action
    audit_service.log_action(
        action="admin_action",
        user_id=admin.id,
        details={"action": "end_all_sessions", "target_user_id": user_id}
    )

    return {"status": "success", "message": f"All sessions ended for user {user.email}"}


@router.post("/users/{user_id}/disable")
def disable_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Disable a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot disable admin accounts")

    user.is_active = False
    db.commit()

    # End all sessions
    audit_service = AuditService(db)
    audit_service.end_all_sessions(user_id)

    # Log the action
    audit_service.log_action(
        action="admin_action",
        user_id=admin.id,
        details={"action": "disable_user", "target_user_id": user_id}
    )

    return {"status": "success", "message": f"User {user.email} disabled"}


@router.post("/users/{user_id}/enable")
def enable_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Re-enable a disabled user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    db.commit()

    # Log the action
    audit_service = AuditService(db)
    audit_service.log_action(
        action="admin_action",
        user_id=admin.id,
        details={"action": "enable_user", "target_user_id": user_id}
    )

    return {"status": "success", "message": f"User {user.email} enabled"}


@router.post("/users/{user_id}/set-subscription")
def set_user_subscription(
    user_id: int,
    tier: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Set user subscription tier (admin override)."""
    try:
        from backend_v2.services.subscription_service import SubscriptionService, TIER_LIMITS
    except ImportError:
        from services.subscription_service import SubscriptionService, TIER_LIMITS

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    valid_tiers = list(TIER_LIMITS.keys())
    if tier not in valid_tiers:
        raise HTTPException(status_code=400, detail=f"Invalid tier. Must be one of: {valid_tiers}")

    service = SubscriptionService(db)

    if tier == "free":
        service.downgrade_to_free(user_id)
    else:
        # Admin-granted subscriptions get a long period (1 year)
        service.upgrade_to_tier(user_id, tier, billing_cycle="admin_granted")

    # Log the action
    audit_service = AuditService(db)
    audit_service.log_action(
        action="admin_action",
        user_id=admin.id,
        details={"action": "set_subscription", "target_user_id": user_id, "tier": tier}
    )

    return {"status": "success", "message": f"User {user.email} subscription set to {tier}"}


# =============================================================================
# OpenAI Usage Monitoring
# =============================================================================

@router.get("/openai-usage")
def get_openai_usage(
    days: int = 30,
    admin: User = Depends(require_admin)
):
    """Get OpenAI API usage statistics."""
    try:
        from backend_v2.services.openai_tracker import get_usage_summary
    except ImportError:
        from services.openai_tracker import get_usage_summary

    return get_usage_summary(days)


@router.get("/openai-usage/daily")
def get_openai_daily_usage(
    days: int = 30,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get detailed daily OpenAI usage breakdown."""
    from sqlalchemy import func

    try:
        from backend_v2.models import OpenAIUsageLog
    except ImportError:
        from models import OpenAIUsageLog

    cutoff = datetime.utcnow() - timedelta(days=days)

    daily = db.query(
        OpenAIUsageLog.date,
        OpenAIUsageLog.model,
        OpenAIUsageLog.purpose,
        func.count(OpenAIUsageLog.id).label("calls"),
        func.sum(OpenAIUsageLog.tokens_input).label("input_tokens"),
        func.sum(OpenAIUsageLog.tokens_output).label("output_tokens"),
        func.sum(OpenAIUsageLog.cost_usd).label("cost")
    ).filter(
        OpenAIUsageLog.timestamp >= cutoff
    ).group_by(
        OpenAIUsageLog.date,
        OpenAIUsageLog.model,
        OpenAIUsageLog.purpose
    ).order_by(OpenAIUsageLog.date.desc()).all()

    return {
        "period_days": days,
        "details": [
            {
                "date": d.date,
                "model": d.model,
                "purpose": d.purpose,
                "calls": d.calls,
                "input_tokens": d.input_tokens or 0,
                "output_tokens": d.output_tokens or 0,
                "cost": round(d.cost or 0, 4)
            }
            for d in daily
        ]
    }
