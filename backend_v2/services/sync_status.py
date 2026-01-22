"""
Sync status tracking for real-time feedback to users.
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import threading

# In-memory status store (per user, per provider)
# Structure: {user_id: {provider_name: SyncStatus}}
_sync_status: Dict[int, Dict[str, dict]] = {}
_lock = threading.Lock()

# Cleanup threshold - remove completed statuses older than this
STATUS_CLEANUP_MINUTES = 30


_last_cleanup: Optional[datetime] = None

def get_status(user_id: int, provider_name: str) -> Optional[dict]:
    """Get current sync status for a user/provider."""
    global _last_cleanup

    # Periodic cleanup (every 5 minutes)
    if _last_cleanup is None or datetime.now() - _last_cleanup > timedelta(minutes=5):
        _last_cleanup = datetime.now()
        # Run cleanup in a separate thread to avoid blocking
        cleanup_thread = threading.Thread(target=cleanup_old_statuses, daemon=True)
        cleanup_thread.start()

    with _lock:
        if user_id in _sync_status and provider_name in _sync_status[user_id]:
            return _sync_status[user_id][provider_name].copy()
    return None


def set_status(user_id: int, provider_name: str, stage: str, message: str,
               progress: int = 0, total: int = 0, is_complete: bool = False,
               is_error: bool = False):
    """Update sync status for a user/provider."""
    with _lock:
        if user_id not in _sync_status:
            _sync_status[user_id] = {}

        _sync_status[user_id][provider_name] = {
            "stage": stage,
            "message": message,
            "progress": progress,
            "total": total,
            "is_complete": is_complete,
            "is_error": is_error,
            "updated_at": datetime.now().isoformat()
        }


def clear_status(user_id: int, provider_name: str):
    """Clear sync status after completion."""
    with _lock:
        if user_id in _sync_status and provider_name in _sync_status[user_id]:
            del _sync_status[user_id][provider_name]


# Convenience functions for common stages
def status_starting(user_id: int, provider_name: str):
    set_status(user_id, provider_name, "starting", "Starting sync...")


def status_logging_in(user_id: int, provider_name: str):
    set_status(user_id, provider_name, "login", "Logging in...")


def status_logged_in(user_id: int, provider_name: str):
    set_status(user_id, provider_name, "logged_in", "Login successful")


def status_navigating(user_id: int, provider_name: str):
    set_status(user_id, provider_name, "navigating", "Navigating to documents...")


def status_scanning(user_id: int, provider_name: str):
    set_status(user_id, provider_name, "scanning", "Scanning for documents...")


def status_downloading(user_id: int, provider_name: str, current: int, total: int):
    set_status(user_id, provider_name, "downloading",
               f"Downloading document {current}/{total}", current, total)


def status_processing(user_id: int, provider_name: str, current: int, total: int):
    set_status(user_id, provider_name, "processing",
               f"Processing document {current}/{total}", current, total)


def status_complete(user_id: int, provider_name: str, doc_count: int):
    set_status(user_id, provider_name, "complete",
               f"Sync complete! {doc_count} documents", doc_count, doc_count,
               is_complete=True)


def status_error(user_id: int, provider_name: str, error_msg: str):
    set_status(user_id, provider_name, "error", error_msg,
               is_complete=True, is_error=True)


def cleanup_old_statuses():
    """Remove completed status entries older than STATUS_CLEANUP_MINUTES.
    Call this periodically to prevent memory leaks."""
    cutoff = datetime.now() - timedelta(minutes=STATUS_CLEANUP_MINUTES)

    with _lock:
        users_to_remove = []
        for user_id, providers in _sync_status.items():
            providers_to_remove = []
            for provider_name, status in providers.items():
                if status.get("is_complete", False):
                    updated_at = status.get("updated_at")
                    if updated_at:
                        try:
                            status_time = datetime.fromisoformat(updated_at)
                            if status_time < cutoff:
                                providers_to_remove.append(provider_name)
                        except ValueError:
                            pass

            for provider in providers_to_remove:
                del providers[provider]

            if not providers:
                users_to_remove.append(user_id)

        for user_id in users_to_remove:
            del _sync_status[user_id]
