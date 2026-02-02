"""
Notification management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

try:
    from backend_v2.database import get_db
    from backend_v2.auth.jwt import get_current_user
    from backend_v2.models import User, Notification, NotificationPreference
    from backend_v2.services.notification_service import NotificationService
except ImportError:
    from database import get_db
    from auth.jwt import get_current_user
    from models import User, Notification, NotificationPreference
    from services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationPreferencesUpdate(BaseModel):
    email_new_documents: Optional[bool] = None
    email_abnormal_biomarkers: Optional[bool] = None
    email_analysis_complete: Optional[bool] = None
    email_sync_failed: Optional[bool] = None
    email_reminders: Optional[bool] = None
    email_frequency: Optional[str] = None  # immediate, daily, weekly
    quiet_hours_start: Optional[int] = None  # 0-23
    quiet_hours_end: Optional[int] = None  # 0-23


class NotificationPreferencesResponse(BaseModel):
    email_new_documents: bool
    email_abnormal_biomarkers: bool
    email_analysis_complete: bool
    email_sync_failed: bool
    email_reminders: bool
    email_frequency: str
    quiet_hours_start: Optional[int]
    quiet_hours_end: Optional[int]


class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime


@router.get("/preferences", response_model=NotificationPreferencesResponse)
def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's notification preferences."""
    service = NotificationService(db)
    prefs = service.get_user_preferences(current_user.id)

    return NotificationPreferencesResponse(
        email_new_documents=prefs.email_new_documents,
        email_abnormal_biomarkers=prefs.email_abnormal_biomarkers,
        email_analysis_complete=prefs.email_analysis_complete,
        email_sync_failed=prefs.email_sync_failed,
        email_reminders=prefs.email_reminders,
        email_frequency=prefs.email_frequency,
        quiet_hours_start=prefs.quiet_hours_start,
        quiet_hours_end=prefs.quiet_hours_end
    )


@router.put("/preferences", response_model=NotificationPreferencesResponse)
def update_notification_preferences(
    updates: NotificationPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user's notification preferences."""
    service = NotificationService(db)
    prefs = service.get_user_preferences(current_user.id)

    # Update only provided fields
    if updates.email_new_documents is not None:
        prefs.email_new_documents = updates.email_new_documents
    if updates.email_abnormal_biomarkers is not None:
        prefs.email_abnormal_biomarkers = updates.email_abnormal_biomarkers
    if updates.email_analysis_complete is not None:
        prefs.email_analysis_complete = updates.email_analysis_complete
    if updates.email_sync_failed is not None:
        prefs.email_sync_failed = updates.email_sync_failed
    if updates.email_reminders is not None:
        prefs.email_reminders = updates.email_reminders
    if updates.email_frequency is not None:
        if updates.email_frequency not in ("immediate", "daily", "weekly"):
            raise HTTPException(status_code=400, detail="Invalid email frequency")
        prefs.email_frequency = updates.email_frequency
    if updates.quiet_hours_start is not None:
        if not (0 <= updates.quiet_hours_start <= 23):
            raise HTTPException(status_code=400, detail="Invalid quiet hours start (0-23)")
        prefs.quiet_hours_start = updates.quiet_hours_start
    if updates.quiet_hours_end is not None:
        if not (0 <= updates.quiet_hours_end <= 23):
            raise HTTPException(status_code=400, detail="Invalid quiet hours end (0-23)")
        prefs.quiet_hours_end = updates.quiet_hours_end

    db.commit()
    db.refresh(prefs)

    return NotificationPreferencesResponse(
        email_new_documents=prefs.email_new_documents,
        email_abnormal_biomarkers=prefs.email_abnormal_biomarkers,
        email_analysis_complete=prefs.email_analysis_complete,
        email_sync_failed=prefs.email_sync_failed,
        email_reminders=prefs.email_reminders,
        email_frequency=prefs.email_frequency,
        quiet_hours_start=prefs.quiet_hours_start,
        quiet_hours_end=prefs.quiet_hours_end
    )


@router.get("/", response_model=List[NotificationResponse])
def list_notifications(
    limit: int = 50,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's notifications."""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

    return [
        NotificationResponse(
            id=n.id,
            notification_type=n.notification_type,
            title=n.title,
            message=n.message,
            is_read=n.is_read,
            created_at=n.created_at
        )
        for n in notifications
    ]


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications."""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return {"unread_count": count}


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()

    return {"status": "ok"}


@router.post("/mark-all-read")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()

    return {"status": "ok"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a notification."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notification)
    db.commit()

    return {"status": "ok"}
