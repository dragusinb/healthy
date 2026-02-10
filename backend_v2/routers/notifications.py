"""
Notification management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

try:
    from backend_v2.database import get_db
    from backend_v2.routers.documents import get_current_user
    from backend_v2.models import User, Notification, NotificationPreference
    from backend_v2.services.notification_service import NotificationService
    from backend_v2.services.push_service import PushNotificationService, get_vapid_public_key
except ImportError:
    from database import get_db
    from routers.documents import get_current_user
    from models import User, Notification, NotificationPreference
    from services.notification_service import NotificationService
    from services.push_service import PushNotificationService, get_vapid_public_key

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
    # Push notification preferences
    push_enabled: Optional[bool] = None
    push_new_documents: Optional[bool] = None
    push_abnormal_biomarkers: Optional[bool] = None
    push_analysis_complete: Optional[bool] = None
    push_sync_failed: Optional[bool] = None


class NotificationPreferencesResponse(BaseModel):
    email_new_documents: bool
    email_abnormal_biomarkers: bool
    email_analysis_complete: bool
    email_sync_failed: bool
    email_reminders: bool
    email_frequency: str
    quiet_hours_start: Optional[int]
    quiet_hours_end: Optional[int]
    # Push notification preferences
    push_enabled: bool
    push_new_documents: bool
    push_abnormal_biomarkers: bool
    push_analysis_complete: bool
    push_sync_failed: bool


class PushSubscriptionRequest(BaseModel):
    """Request to register a push subscription."""
    endpoint: str
    keys: dict  # Contains p256dh and auth keys


class PushSubscriptionResponse(BaseModel):
    """Response for push subscription operations."""
    status: str
    subscription_id: Optional[int] = None


class DeviceSubscription(BaseModel):
    """Info about a user's push subscription/device."""
    id: int
    device_name: Optional[str]
    created_at: Optional[str]
    last_used: Optional[str]


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
        quiet_hours_end=prefs.quiet_hours_end,
        push_enabled=getattr(prefs, 'push_enabled', True),
        push_new_documents=getattr(prefs, 'push_new_documents', True),
        push_abnormal_biomarkers=getattr(prefs, 'push_abnormal_biomarkers', True),
        push_analysis_complete=getattr(prefs, 'push_analysis_complete', True),
        push_sync_failed=getattr(prefs, 'push_sync_failed', True)
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

    # Update only provided fields - Email preferences
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

    # Update push notification preferences
    if updates.push_enabled is not None:
        prefs.push_enabled = updates.push_enabled
    if updates.push_new_documents is not None:
        prefs.push_new_documents = updates.push_new_documents
    if updates.push_abnormal_biomarkers is not None:
        prefs.push_abnormal_biomarkers = updates.push_abnormal_biomarkers
    if updates.push_analysis_complete is not None:
        prefs.push_analysis_complete = updates.push_analysis_complete
    if updates.push_sync_failed is not None:
        prefs.push_sync_failed = updates.push_sync_failed

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
        quiet_hours_end=prefs.quiet_hours_end,
        push_enabled=getattr(prefs, 'push_enabled', True),
        push_new_documents=getattr(prefs, 'push_new_documents', True),
        push_abnormal_biomarkers=getattr(prefs, 'push_abnormal_biomarkers', True),
        push_analysis_complete=getattr(prefs, 'push_analysis_complete', True),
        push_sync_failed=getattr(prefs, 'push_sync_failed', True)
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


# =============================================================================
# Push Notification Endpoints
# =============================================================================

@router.get("/push/vapid-key")
def get_push_vapid_key():
    """
    Get the VAPID public key needed for push notification subscription.

    Frontend uses this to subscribe to push notifications.
    """
    vapid_key = get_vapid_public_key()
    if not vapid_key:
        raise HTTPException(
            status_code=503,
            detail="Push notifications not configured on this server"
        )
    return {"vapid_public_key": vapid_key}


@router.post("/push/subscribe", response_model=PushSubscriptionResponse)
def subscribe_to_push(
    subscription: PushSubscriptionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register a push notification subscription for the current user.

    This should be called after the browser's Push API returns a subscription.
    """
    if not subscription.endpoint:
        raise HTTPException(status_code=400, detail="Endpoint is required")

    keys = subscription.keys
    if not keys.get("p256dh") or not keys.get("auth"):
        raise HTTPException(status_code=400, detail="p256dh and auth keys are required")

    user_agent = request.headers.get("user-agent", "")

    service = PushNotificationService(db)
    result = service.register_subscription(
        user_id=current_user.id,
        endpoint=subscription.endpoint,
        p256dh_key=keys["p256dh"],
        auth_key=keys["auth"],
        user_agent=user_agent
    )

    return PushSubscriptionResponse(**result)


@router.post("/push/unsubscribe")
def unsubscribe_from_push(
    subscription: PushSubscriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unregister a push notification subscription.

    This should be called when the user disables push notifications
    or when the subscription is no longer valid.
    """
    service = PushNotificationService(db)
    success = service.unregister_subscription(
        user_id=current_user.id,
        endpoint=subscription.endpoint
    )

    if success:
        return {"status": "ok"}
    else:
        return {"status": "not_found"}


@router.get("/push/subscriptions", response_model=List[DeviceSubscription])
def list_push_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all push subscriptions/devices for the current user.

    Useful for showing users which devices are registered for push notifications.
    """
    service = PushNotificationService(db)
    subscriptions = service.get_user_subscriptions(current_user.id)
    return subscriptions


@router.delete("/push/subscriptions/{subscription_id}")
def delete_push_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific push subscription by ID.

    Allows users to remove specific devices from push notifications.
    """
    try:
        from backend_v2.models import PushSubscription
    except ImportError:
        from models import PushSubscription

    subscription = db.query(PushSubscription).filter(
        PushSubscription.id == subscription_id,
        PushSubscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    db.delete(subscription)
    db.commit()

    return {"status": "ok"}


@router.post("/push/test")
def test_push_notification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a test push notification to the current user.

    Useful for testing push notification setup.
    """
    service = PushNotificationService(db)

    if not service.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Push notifications not configured on this server"
        )

    result = service.send_push_notification(
        user_id=current_user.id,
        title="Test Notification",
        body="Notificarile push functioneaza corect!",
        notification_type="test",
        url="/settings"
    )

    if result.get("sent", 0) > 0:
        return {"status": "ok", "message": f"Sent to {result['sent']} device(s)"}
    elif result.get("reason") == "no_subscriptions":
        raise HTTPException(
            status_code=400,
            detail="No push subscriptions found. Please enable notifications in your browser first."
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send notification: {result.get('reason', 'unknown')}"
        )
