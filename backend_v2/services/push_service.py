"""
Web Push Notification Service using VAPID.

This service handles sending push notifications to browsers that have
subscribed using the Web Push API. Uses VAPID for authentication.

Environment variables required:
- VAPID_PRIVATE_KEY: Base64-encoded VAPID private key
- VAPID_PUBLIC_KEY: Base64-encoded VAPID public key
- VAPID_SUBJECT: mailto: or https: URL for VAPID

Generate keys using:
    from py_vapid import Vapid
    vapid = Vapid()
    vapid.generate_keys()
    print("Private:", vapid.private_key)
    print("Public:", vapid.public_key)
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# VAPID configuration
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_SUBJECT = os.getenv("VAPID_SUBJECT", "mailto:contact@analize.online")

# Check if pywebpush is available
try:
    from pywebpush import webpush, WebPushException
    PUSH_AVAILABLE = True
except ImportError:
    PUSH_AVAILABLE = False
    logger.warning("pywebpush not installed. Push notifications disabled.")


class PushNotificationService:
    """Service for sending Web Push notifications."""

    def __init__(self, db: Session):
        self.db = db
        self._check_configuration()

    def _check_configuration(self):
        """Check if VAPID keys are configured."""
        self.is_configured = bool(
            PUSH_AVAILABLE and
            VAPID_PRIVATE_KEY and
            VAPID_PUBLIC_KEY
        )
        if not self.is_configured:
            if not PUSH_AVAILABLE:
                logger.debug("Push notifications disabled: pywebpush not installed")
            elif not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
                logger.debug("Push notifications disabled: VAPID keys not configured")

    def get_vapid_public_key(self) -> Optional[str]:
        """Get the VAPID public key for frontend subscription."""
        return VAPID_PUBLIC_KEY

    def register_subscription(
        self,
        user_id: int,
        endpoint: str,
        p256dh_key: str,
        auth_key: str,
        user_agent: Optional[str] = None,
        device_name: Optional[str] = None
    ) -> dict:
        """Register a new push subscription for a user."""
        try:
            from backend_v2.models import PushSubscription
        except ImportError:
            from models import PushSubscription

        # Check if subscription already exists
        existing = self.db.query(PushSubscription).filter(
            PushSubscription.endpoint == endpoint
        ).first()

        if existing:
            # Update existing subscription
            existing.user_id = user_id
            existing.p256dh_key = p256dh_key
            existing.auth_key = auth_key
            existing.user_agent = user_agent
            existing.device_name = device_name
            existing.is_active = True
            existing.failure_count = 0
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            logger.info(f"Updated push subscription for user {user_id}")
            return {"status": "updated", "subscription_id": existing.id}

        # Create new subscription
        subscription = PushSubscription(
            user_id=user_id,
            endpoint=endpoint,
            p256dh_key=p256dh_key,
            auth_key=auth_key,
            user_agent=user_agent,
            device_name=device_name or self._derive_device_name(user_agent)
        )
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)

        logger.info(f"Created push subscription {subscription.id} for user {user_id}")
        return {"status": "created", "subscription_id": subscription.id}

    def unregister_subscription(self, user_id: int, endpoint: str) -> bool:
        """Unregister a push subscription."""
        try:
            from backend_v2.models import PushSubscription
        except ImportError:
            from models import PushSubscription

        subscription = self.db.query(PushSubscription).filter(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == user_id
        ).first()

        if subscription:
            self.db.delete(subscription)
            self.db.commit()
            logger.info(f"Deleted push subscription for user {user_id}")
            return True

        return False

    def get_user_subscriptions(self, user_id: int) -> List[dict]:
        """Get all active push subscriptions for a user."""
        try:
            from backend_v2.models import PushSubscription
        except ImportError:
            from models import PushSubscription

        subscriptions = self.db.query(PushSubscription).filter(
            PushSubscription.user_id == user_id,
            PushSubscription.is_active == True
        ).all()

        return [
            {
                "id": s.id,
                "device_name": s.device_name,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "last_used": s.last_used.isoformat() if s.last_used else None
            }
            for s in subscriptions
        ]

    def send_push_notification(
        self,
        user_id: int,
        title: str,
        body: str,
        notification_type: str,
        data: Optional[Dict[str, Any]] = None,
        url: Optional[str] = None
    ) -> dict:
        """
        Send a push notification to all user's subscribed devices.

        Args:
            user_id: Target user ID
            title: Notification title
            body: Notification body/message
            notification_type: Type of notification (for filtering by preferences)
            data: Additional data to include in notification
            url: URL to open when notification is clicked

        Returns:
            dict with success/failure counts
        """
        if not self.is_configured:
            logger.debug("Push notifications not configured, skipping")
            return {"sent": 0, "failed": 0, "reason": "not_configured"}

        # Check user preferences
        if not self._should_send_push(user_id, notification_type):
            return {"sent": 0, "failed": 0, "reason": "disabled_by_user"}

        try:
            from backend_v2.models import PushSubscription
        except ImportError:
            from models import PushSubscription

        # Get all active subscriptions for user
        subscriptions = self.db.query(PushSubscription).filter(
            PushSubscription.user_id == user_id,
            PushSubscription.is_active == True
        ).all()

        if not subscriptions:
            return {"sent": 0, "failed": 0, "reason": "no_subscriptions"}

        # Build notification payload
        payload = {
            "title": title,
            "body": body,
            "icon": "/favicon.svg",
            "badge": "/favicon.svg",
            "tag": notification_type,
            "data": {
                "type": notification_type,
                "url": url or self._get_default_url(notification_type),
                **(data or {})
            }
        }

        sent = 0
        failed = 0

        for subscription in subscriptions:
            success = self._send_to_subscription(subscription, payload)
            if success:
                sent += 1
            else:
                failed += 1

        self.db.commit()

        logger.info(f"Push notifications for user {user_id}: sent={sent}, failed={failed}")
        return {"sent": sent, "failed": failed}

    def _send_to_subscription(self, subscription, payload: dict) -> bool:
        """Send a push notification to a single subscription."""
        if not PUSH_AVAILABLE:
            return False

        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh_key,
                "auth": subscription.auth_key
            }
        }

        vapid_claims = {
            "sub": VAPID_SUBJECT
        }

        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=vapid_claims
            )

            # Update last used timestamp
            subscription.last_used = datetime.now(timezone.utc)
            subscription.failure_count = 0
            return True

        except WebPushException as e:
            logger.warning(f"Push notification failed for subscription {subscription.id}: {e}")

            # Handle subscription expiration/invalidation
            if e.response and e.response.status_code in (404, 410):
                # Subscription no longer valid - mark as inactive
                subscription.is_active = False
                logger.info(f"Subscription {subscription.id} marked inactive (expired)")
            else:
                # Increment failure count
                subscription.failure_count += 1
                # Deactivate after 5 consecutive failures
                if subscription.failure_count >= 5:
                    subscription.is_active = False
                    logger.info(f"Subscription {subscription.id} deactivated after 5 failures")

            return False

        except Exception as e:
            logger.error(f"Unexpected error sending push: {e}")
            subscription.failure_count += 1
            return False

    def _should_send_push(self, user_id: int, notification_type: str) -> bool:
        """Check if user wants push notifications for this type."""
        try:
            from backend_v2.models import NotificationPreference
        except ImportError:
            from models import NotificationPreference

        prefs = self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

        if not prefs:
            return True  # Default to enabled

        if not prefs.push_enabled:
            return False

        type_to_pref = {
            "new_documents": prefs.push_new_documents,
            "abnormal_biomarker": prefs.push_abnormal_biomarkers,
            "analysis_complete": prefs.push_analysis_complete,
            "sync_failed": prefs.push_sync_failed,
        }

        return type_to_pref.get(notification_type, True)

    def _get_default_url(self, notification_type: str) -> str:
        """Get the default URL to open for a notification type."""
        urls = {
            "new_documents": "/documents",
            "abnormal_biomarker": "/biomarkers",
            "analysis_complete": "/health",
            "sync_failed": "/accounts",
            "reminder": "/biomarkers"
        }
        return urls.get(notification_type, "/dashboard")

    def _derive_device_name(self, user_agent: Optional[str]) -> str:
        """Derive a friendly device name from user agent string."""
        if not user_agent:
            return "Unknown Device"

        ua_lower = user_agent.lower()

        # Detect browser
        browser = "Browser"
        if "chrome" in ua_lower and "edg" not in ua_lower:
            browser = "Chrome"
        elif "firefox" in ua_lower:
            browser = "Firefox"
        elif "safari" in ua_lower and "chrome" not in ua_lower:
            browser = "Safari"
        elif "edg" in ua_lower:
            browser = "Edge"

        # Detect OS/device
        device = ""
        if "iphone" in ua_lower:
            device = "iPhone"
        elif "ipad" in ua_lower:
            device = "iPad"
        elif "android" in ua_lower:
            device = "Android"
        elif "windows" in ua_lower:
            device = "Windows"
        elif "mac os" in ua_lower or "macos" in ua_lower:
            device = "Mac"
        elif "linux" in ua_lower:
            device = "Linux"

        if device:
            return f"{browser} on {device}"
        return browser


# Helper functions for easy integration
def send_push_new_documents(db: Session, user_id: int, provider: str, document_count: int, biomarker_count: int = 0):
    """Send push notification for new documents."""
    service = PushNotificationService(db)
    if document_count == 1:
        body = f"1 document nou de la {provider}"
    else:
        body = f"{document_count} documente noi de la {provider}"
    if biomarker_count:
        body += f" ({biomarker_count} biomarkeri)"

    service.send_push_notification(
        user_id=user_id,
        title="Rezultate noi disponibile",
        body=body,
        notification_type="new_documents",
        data={"provider": provider, "count": document_count},
        url="/documents"
    )


def send_push_abnormal_biomarker(db: Session, user_id: int, biomarker_name: str, value: str, unit: str, flag: str):
    """Send push notification for abnormal biomarker."""
    service = PushNotificationService(db)
    flag_text = "ridicat" if flag == "HIGH" else "scazut"
    service.send_push_notification(
        user_id=user_id,
        title=f"{biomarker_name} {flag_text}",
        body=f"Valoare: {value} {unit}",
        notification_type="abnormal_biomarker",
        data={"biomarker": biomarker_name, "value": value, "flag": flag},
        url="/biomarkers"
    )


def send_push_analysis_complete(db: Session, user_id: int, report_type: str, risk_level: str):
    """Send push notification when AI analysis is complete."""
    service = PushNotificationService(db)
    report_labels = {
        "general": "Generalist",
        "cardiology": "Cardiologie",
        "endocrinology": "Endocrinologie",
        "hematology": "Hematologie",
        "hepatology": "Hepatologie",
        "nephrology": "Nefrologie"
    }
    service.send_push_notification(
        user_id=user_id,
        title="Analiza AI completa",
        body=f"Raport {report_labels.get(report_type, report_type)} disponibil",
        notification_type="analysis_complete",
        data={"report_type": report_type, "risk_level": risk_level},
        url="/health"
    )


def send_push_sync_failed(db: Session, user_id: int, provider: str, error_type: str):
    """Send push notification when sync fails."""
    service = PushNotificationService(db)
    service.send_push_notification(
        user_id=user_id,
        title=f"Sincronizare esuata - {provider}",
        body="Verifica datele de autentificare",
        notification_type="sync_failed",
        data={"provider": provider, "error_type": error_type},
        url="/accounts"
    )


def get_vapid_public_key() -> Optional[str]:
    """Get the VAPID public key for frontend subscription."""
    return VAPID_PUBLIC_KEY
