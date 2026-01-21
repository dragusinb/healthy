"""
Sync status tracking for real-time feedback to users.
"""
from typing import Dict, Optional
from datetime import datetime
import threading

# In-memory status store (per user, per provider)
# Structure: {user_id: {provider_name: SyncStatus}}
_sync_status: Dict[int, Dict[str, dict]] = {}
_lock = threading.Lock()


def get_status(user_id: int, provider_name: str) -> Optional[dict]:
    """Get current sync status for a user/provider."""
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
