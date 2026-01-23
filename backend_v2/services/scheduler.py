"""Background scheduler for automatic syncing of linked accounts."""
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None
_lock = threading.Lock()

# Track running syncs to avoid overlap
_running_syncs = set()
MAX_CONCURRENT_SYNCS = 2


def init_scheduler():
    """Initialize the background scheduler."""
    global scheduler
    with _lock:
        if scheduler is None:
            scheduler = BackgroundScheduler()
            scheduler.start()

            # Add job to check for accounts that need syncing
            scheduler.add_job(
                check_and_run_syncs,
                IntervalTrigger(minutes=30),  # Check every 30 minutes
                id="sync_checker",
                replace_existing=True
            )

            # Add cleanup job for stuck syncs
            scheduler.add_job(
                cleanup_stuck_syncs,
                IntervalTrigger(hours=1),  # Run every hour
                id="sync_cleanup",
                replace_existing=True
            )

            logger.info("Scheduler initialized")

    return scheduler


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    global scheduler
    with _lock:
        if scheduler:
            scheduler.shutdown(wait=False)
            scheduler = None
            logger.info("Scheduler shutdown")


def check_and_run_syncs():
    """Check for accounts that need syncing and queue them."""
    try:
        from backend_v2.database import SessionLocal
        from backend_v2.models import LinkedAccount
    except ImportError:
        from database import SessionLocal
        from models import LinkedAccount

    logger.info("Checking for accounts that need syncing...")

    db = SessionLocal()
    try:
        now = datetime.utcnow()

        # Find accounts that need syncing
        accounts = db.query(LinkedAccount).filter(
            LinkedAccount.sync_enabled == True,
            LinkedAccount.status != "SYNCING",
            LinkedAccount.consecutive_failures < 5  # Skip accounts with too many failures
        ).all()

        queued = 0
        for account in accounts:
            if should_sync(account, now):
                # Check if we can run more syncs
                if len(_running_syncs) >= MAX_CONCURRENT_SYNCS:
                    logger.info(f"Max concurrent syncs reached, skipping {account.provider_name}")
                    continue

                # Queue the sync
                queue_sync(account.user_id, account.id, account.provider_name)
                queued += 1

        logger.info(f"Queued {queued} syncs")

    except Exception as e:
        logger.error(f"Error in sync checker: {e}")
    finally:
        db.close()


def should_sync(account, now):
    """Determine if an account should be synced based on frequency settings."""
    if not account.last_sync:
        return True  # Never synced, should sync

    time_since_sync = now - account.last_sync

    if account.sync_frequency == "daily":
        return time_since_sync > timedelta(hours=23)
    elif account.sync_frequency == "weekly":
        return time_since_sync > timedelta(days=6, hours=23)
    elif account.sync_frequency == "manual":
        return False  # Only manual syncs
    else:
        return time_since_sync > timedelta(hours=23)  # Default to daily


def queue_sync(user_id: int, account_id: int, provider_name: str):
    """Queue a sync job to run."""
    sync_key = f"{user_id}:{provider_name}"

    if sync_key in _running_syncs:
        logger.info(f"Sync already running for {sync_key}")
        return

    _running_syncs.add(sync_key)

    # Run in a thread to not block
    thread = threading.Thread(
        target=run_scheduled_sync,
        args=(user_id, account_id, provider_name, sync_key),
        daemon=True
    )
    thread.start()


def run_scheduled_sync(user_id: int, account_id: int, provider_name: str, sync_key: str):
    """Run a scheduled sync for an account."""
    try:
        from backend_v2.database import SessionLocal
        from backend_v2.models import LinkedAccount, SyncJob
        from backend_v2.auth.crypto import decrypt_password
        from backend_v2.services.crawlers_manager import run_regina_async, run_synevo_async
        from backend_v2.services import sync_status
    except ImportError:
        from database import SessionLocal
        from models import LinkedAccount, SyncJob
        from auth.crypto import decrypt_password
        from services.crawlers_manager import run_regina_async, run_synevo_async
        from services import sync_status

    db = SessionLocal()

    try:
        # Get account
        account = db.query(LinkedAccount).filter(LinkedAccount.id == account_id).first()
        if not account:
            logger.error(f"Account {account_id} not found")
            return

        # Create sync job record
        sync_job = SyncJob(
            user_id=user_id,
            linked_account_id=account_id,
            provider_name=provider_name,
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(sync_job)
        account.status = "SYNCING"
        db.commit()

        # Decrypt password
        password = decrypt_password(account.encrypted_password)

        # Set status
        sync_status.status_starting(user_id, provider_name)
        sync_status.status_logging_in(user_id, provider_name)

        # Run crawler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            if provider_name == "Regina Maria":
                res = loop.run_until_complete(run_regina_async(account.username, password, user_id=user_id))
            elif provider_name == "Synevo":
                res = loop.run_until_complete(run_synevo_async(account.username, password, user_id=user_id))
            else:
                raise ValueError(f"Unknown provider: {provider_name}")
        finally:
            loop.close()

        if res.get("status") != "success":
            error_msg = res.get("message", "Sync failed")
            sync_job.status = "failed"
            sync_job.error_message = error_msg
            sync_job.completed_at = datetime.utcnow()
            account.status = "ERROR"
            account.last_sync_error = error_msg
            account.consecutive_failures += 1
            db.commit()
            sync_status.status_error(user_id, provider_name, error_msg)
            logger.error(f"Sync failed for {provider_name}: {error_msg}")
            return

        # Process documents (similar to users.py run_sync_task)
        docs = res.get("documents", [])
        sync_job.documents_found = len(docs)

        if docs:
            processed = process_sync_documents(db, user_id, provider_name, docs, sync_job)
            sync_job.documents_processed = processed

        # Success
        sync_job.status = "completed"
        sync_job.completed_at = datetime.utcnow()
        account.status = "ACTIVE"
        account.last_sync = datetime.utcnow()
        account.last_sync_error = None
        account.consecutive_failures = 0
        db.commit()

        sync_status.status_complete(user_id, provider_name, sync_job.documents_processed)
        logger.info(f"Sync completed for {provider_name}: {sync_job.documents_processed} documents")

    except Exception as e:
        logger.error(f"Scheduled sync error: {e}")
        try:
            account = db.query(LinkedAccount).filter(LinkedAccount.id == account_id).first()
            if account:
                account.status = "ERROR"
                account.last_sync_error = str(e)
                account.consecutive_failures += 1
            sync_job = db.query(SyncJob).filter(
                SyncJob.linked_account_id == account_id,
                SyncJob.status == "running"
            ).first()
            if sync_job:
                sync_job.status = "failed"
                sync_job.error_message = str(e)
                sync_job.completed_at = datetime.utcnow()
            db.commit()
        except:
            pass
        sync_status.status_error(user_id, provider_name, str(e))
    finally:
        db.close()
        _running_syncs.discard(sync_key)


def process_sync_documents(db, user_id, provider_name, docs, sync_job):
    """Process downloaded documents - extract biomarkers with AI."""
    try:
        from backend_v2.models import Document, TestResult
        from backend_v2.services.ai_service import AIService
        from backend_v2.services import sync_status
    except ImportError:
        from models import Document, TestResult
        from services.ai_service import AIService
        from services import sync_status

    import datetime as dt

    try:
        ai_service = AIService()
    except Exception as e:
        logger.error(f"AI Service init failed: {e}")
        return 0

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
                document_date=doc_info.get("date"),
                upload_date=dt.datetime.now(),
                is_processed=False
            )
            db.add(new_doc)
            db.commit()
            db.refresh(new_doc)
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            continue

        # AI Parse
        try:
            parsed_data = ai_service.process_document(doc_info["local_path"])

            if "results" in parsed_data and parsed_data["results"]:
                for r in parsed_data["results"]:
                    numeric_val = r.get("numeric_value")
                    if numeric_val is None:
                        try:
                            numeric_val = float(r.get("value"))
                        except (TypeError, ValueError):
                            numeric_val = None

                    tr = TestResult(
                        document_id=new_doc.id,
                        test_name=r.get("test_name"),
                        value=str(r.get("value")),
                        numeric_value=numeric_val,
                        unit=r.get("unit"),
                        reference_range=r.get("reference_range"),
                        flags=r.get("flags", "NORMAL")
                    )
                    db.add(tr)

                # Update document date from metadata
                if "metadata" in parsed_data and parsed_data["metadata"].get("date"):
                    try:
                        extracted_date = dt.datetime.strptime(
                            parsed_data["metadata"]["date"], "%Y-%m-%d"
                        )
                        new_doc.document_date = extracted_date
                    except:
                        pass

                new_doc.is_processed = True
                db.commit()
                count_processed += 1
            else:
                new_doc.is_processed = True
                db.commit()
        except Exception as e:
            logger.error(f"Failed to parse {doc_info['filename']}: {e}")
            new_doc.is_processed = True
            db.commit()

    return count_processed


def cleanup_stuck_syncs():
    """Clean up syncs that have been running too long (stuck)."""
    try:
        from backend_v2.database import SessionLocal
        from backend_v2.models import LinkedAccount, SyncJob
    except ImportError:
        from database import SessionLocal
        from models import LinkedAccount, SyncJob

    logger.info("Cleaning up stuck syncs...")

    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(hours=1)

        # Find stuck sync jobs
        stuck_jobs = db.query(SyncJob).filter(
            SyncJob.status == "running",
            SyncJob.started_at < cutoff
        ).all()

        for job in stuck_jobs:
            job.status = "failed"
            job.error_message = "Sync timed out (stuck for >1 hour)"
            job.completed_at = datetime.utcnow()

            # Reset account status
            account = db.query(LinkedAccount).filter(
                LinkedAccount.id == job.linked_account_id
            ).first()
            if account:
                account.status = "ERROR"
                account.last_sync_error = "Sync timed out"
                account.consecutive_failures += 1

        if stuck_jobs:
            db.commit()
            logger.info(f"Cleaned up {len(stuck_jobs)} stuck syncs")

        # Also reset accounts stuck in SYNCING state
        stuck_accounts = db.query(LinkedAccount).filter(
            LinkedAccount.status == "SYNCING"
        ).all()

        for account in stuck_accounts:
            # Check if there's actually a running job
            running_job = db.query(SyncJob).filter(
                SyncJob.linked_account_id == account.id,
                SyncJob.status == "running"
            ).first()

            if not running_job:
                account.status = "ACTIVE"  # Reset if no running job

        db.commit()

    except Exception as e:
        logger.error(f"Error in cleanup: {e}")
    finally:
        db.close()
