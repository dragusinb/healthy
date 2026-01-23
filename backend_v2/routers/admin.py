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


@router.get("/service-status")
def get_service_status(admin: User = Depends(require_admin)):
    """Get systemd service status and restart history."""
    try:
        # Get service status
        status_result = subprocess.run(
            ["systemctl", "status", "healthy", "--no-pager"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Get recent restarts from journal
        journal_result = subprocess.run(
            ["journalctl", "-u", "healthy", "--no-pager", "-n", "50", "--output=short-iso"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Parse status
        status_lines = status_result.stdout.split("\n") if status_result.stdout else []
        is_active = any("Active: active" in line for line in status_lines)
        is_failed = any("Active: failed" in line for line in status_lines)

        # Find restarts in journal
        journal_lines = journal_result.stdout.split("\n") if journal_result.stdout else []
        restarts = [l for l in journal_lines if "Started" in l or "Stopped" in l or "failed" in l.lower()]

        # Get uptime
        uptime = None
        for line in status_lines:
            if "Active:" in line and "since" in line:
                # Extract the time part
                try:
                    since_part = line.split("since")[1].strip()
                    uptime = since_part.split(";")[0].strip()
                except:
                    pass

        # Get memory usage from status
        memory = None
        for line in status_lines:
            if "Memory:" in line:
                memory = line.split("Memory:")[1].strip()

        return {
            "is_active": is_active,
            "is_failed": is_failed,
            "uptime": uptime,
            "memory": memory,
            "status_output": status_lines[:15],  # First 15 lines of status
            "recent_events": restarts[-10:],      # Last 10 restart events
            "journal_lines": journal_lines[-30:]  # Last 30 journal entries
        }
    except subprocess.TimeoutExpired:
        return {"error": "Timeout getting service status"}
    except Exception as e:
        return {"error": str(e)}


@router.post("/restart-server")
def restart_server(admin: User = Depends(require_admin)):
    """Restart the healthy service (use with caution)."""
    try:
        # Schedule restart in background so we can return response first
        import threading

        def delayed_restart():
            import time
            time.sleep(2)  # Wait 2 seconds before restarting
            subprocess.run(["systemctl", "restart", "healthy"], timeout=30)

        thread = threading.Thread(target=delayed_restart, daemon=True)
        thread.start()

        return {"message": "Server restart scheduled in 2 seconds"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
