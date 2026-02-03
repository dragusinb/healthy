"""
Audit logging, usage tracking, and abuse detection service.
"""
import datetime
import json
import hashlib
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

try:
    from backend_v2.models import (
        User, AuditLog, UserSession, AbuseFlag,
        RateLimitCounter, UsageMetrics
    )
except ImportError:
    from models import (
        User, AuditLog, UserSession, AbuseFlag,
        RateLimitCounter, UsageMetrics
    )


# =============================================================================
# Configuration
# =============================================================================

# Rate limits per action (requests per window)
RATE_LIMITS = {
    "api_call": {"limit": 1000, "window_minutes": 60},
    "login": {"limit": 10, "window_minutes": 15},
    "login_failed": {"limit": 5, "window_minutes": 15},
    "register": {"limit": 3, "window_minutes": 60},
    "upload": {"limit": 50, "window_minutes": 60},
    "analyze": {"limit": 10, "window_minutes": 60},
    "sync": {"limit": 10, "window_minutes": 60},
    "password_reset": {"limit": 3, "window_minutes": 60},
}

# Abuse detection thresholds
ABUSE_THRESHOLDS = {
    "failed_logins_per_hour": 10,
    "unique_ips_per_hour": 5,  # Account sharing detection
    "api_calls_per_minute": 100,  # Scraping detection
    "documents_per_hour": 100,  # Bulk upload detection
}

# Actions that should be logged
LOGGED_ACTIONS = [
    "login", "login_failed", "logout", "register",
    "password_change", "password_reset", "email_verify",
    "document_upload", "document_delete", "document_view",
    "analyze_health", "analyze_specialist", "analyze_gap",
    "link_account", "unlink_account", "sync_start", "sync_complete", "sync_failed",
    "subscription_upgrade", "subscription_cancel", "subscription_reactivate",
    "family_create", "family_join", "family_leave", "family_remove_member",
    "profile_update", "settings_update",
    "admin_action", "export_data",
]


class AuditService:
    """Service for audit logging and abuse detection."""

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # Audit Logging
    # =========================================================================

    def log_action(
        self,
        action: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success"
    ) -> AuditLog:
        """Log a user action."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
        self.db.add(log)
        self.db.commit()

        # Check for abuse after logging
        if user_id or ip_address:
            self._check_for_abuse(user_id, ip_address, action)

        return log

    def get_user_audit_logs(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
        action_filter: Optional[str] = None,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None
    ) -> List[AuditLog]:
        """Get audit logs for a user."""
        query = self.db.query(AuditLog).filter(AuditLog.user_id == user_id)

        if action_filter:
            query = query.filter(AuditLog.action == action_filter)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    def get_recent_activity(
        self,
        limit: int = 100,
        user_id: Optional[int] = None,
        action_filter: Optional[str] = None
    ) -> List[Dict]:
        """Get recent activity for admin dashboard."""
        query = self.db.query(AuditLog)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action_filter:
            query = query.filter(AuditLog.action == action_filter)

        logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()

        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "user_email": log.user.email if log.user else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": json.loads(log.details) if log.details else None,
                "ip_address": log.ip_address,
                "status": log.status,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]

    # =========================================================================
    # Session Tracking
    # =========================================================================

    def create_session(
        self,
        user_id: int,
        token: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None
    ) -> UserSession:
        """Create a new user session."""
        # Hash the token for storage
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:32]

        session = UserSession(
            user_id=user_id,
            session_token=token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint
        )
        self.db.add(session)
        self.db.commit()

        # Check for account sharing
        self._check_account_sharing(user_id, ip_address)

        return session

    def update_session_activity(self, user_id: int, token: str):
        """Update last activity for a session."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:32]
        session = self.db.query(UserSession).filter(
            UserSession.session_token == token_hash,
            UserSession.is_active == True
        ).first()

        if session:
            session.last_activity = datetime.datetime.utcnow()
            self.db.commit()

    def end_session(self, user_id: int, token: str):
        """End a user session."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:32]
        session = self.db.query(UserSession).filter(
            UserSession.session_token == token_hash
        ).first()

        if session:
            session.is_active = False
            session.ended_at = datetime.datetime.utcnow()
            self.db.commit()

    def get_active_sessions(self, user_id: int) -> List[Dict]:
        """Get active sessions for a user."""
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).order_by(UserSession.last_activity.desc()).all()

        return [
            {
                "id": s.id,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "location": s.location,
                "started_at": s.started_at.isoformat(),
                "last_activity": s.last_activity.isoformat(),
            }
            for s in sessions
        ]

    def end_all_sessions(self, user_id: int, except_token: Optional[str] = None):
        """End all sessions for a user (e.g., on password change)."""
        query = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        )

        if except_token:
            token_hash = hashlib.sha256(except_token.encode()).hexdigest()[:32]
            query = query.filter(UserSession.session_token != token_hash)

        now = datetime.datetime.utcnow()
        query.update({
            UserSession.is_active: False,
            UserSession.ended_at: now
        })
        self.db.commit()

    # =========================================================================
    # Rate Limiting
    # =========================================================================

    def check_rate_limit(
        self,
        identifier: str,
        action: str,
        custom_limit: Optional[int] = None,
        custom_window: Optional[int] = None
    ) -> tuple[bool, int]:
        """
        Check if rate limit is exceeded.
        Returns (is_allowed, remaining_requests).
        """
        config = RATE_LIMITS.get(action, {"limit": 100, "window_minutes": 60})
        limit = custom_limit or config["limit"]
        window_minutes = custom_window or config["window_minutes"]

        now = datetime.datetime.utcnow()
        window_start = now - datetime.timedelta(minutes=window_minutes)

        # Get or create counter
        counter = self.db.query(RateLimitCounter).filter(
            RateLimitCounter.identifier == identifier,
            RateLimitCounter.action == action
        ).first()

        if not counter:
            counter = RateLimitCounter(
                identifier=identifier,
                action=action,
                count=0,
                window_start=now,
                window_minutes=window_minutes
            )
            self.db.add(counter)
            self.db.commit()

        # Reset if window expired
        if counter.window_start < window_start:
            counter.count = 0
            counter.window_start = now
            self.db.commit()

        # Check limit
        remaining = limit - counter.count
        is_allowed = counter.count < limit

        if is_allowed:
            counter.count += 1
            self.db.commit()

        return is_allowed, max(0, remaining - 1)

    def increment_rate_limit(self, identifier: str, action: str):
        """Manually increment rate limit counter."""
        counter = self.db.query(RateLimitCounter).filter(
            RateLimitCounter.identifier == identifier,
            RateLimitCounter.action == action
        ).first()

        if counter:
            counter.count += 1
            self.db.commit()

    # =========================================================================
    # Abuse Detection
    # =========================================================================

    def _check_for_abuse(
        self,
        user_id: Optional[int],
        ip_address: Optional[str],
        action: str
    ):
        """Check for potential abuse after an action."""
        now = datetime.datetime.utcnow()
        hour_ago = now - datetime.timedelta(hours=1)

        # Check failed logins
        if action == "login_failed" and (user_id or ip_address):
            self._check_failed_logins(user_id, ip_address, hour_ago)

        # Check API abuse (scraping)
        if user_id:
            self._check_api_abuse(user_id, ip_address)

    def _check_failed_logins(
        self,
        user_id: Optional[int],
        ip_address: Optional[str],
        since: datetime.datetime
    ):
        """Check for brute force login attempts."""
        query = self.db.query(func.count(AuditLog.id)).filter(
            AuditLog.action == "login_failed",
            AuditLog.created_at >= since
        )

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        elif ip_address:
            query = query.filter(AuditLog.ip_address == ip_address)

        count = query.scalar()

        if count >= ABUSE_THRESHOLDS["failed_logins_per_hour"]:
            self._create_abuse_flag(
                user_id=user_id,
                ip_address=ip_address,
                flag_type="failed_login",
                severity="high" if count >= 20 else "medium",
                description=f"Multiple failed login attempts: {count} in the last hour",
                details={"count": count, "threshold": ABUSE_THRESHOLDS["failed_logins_per_hour"]}
            )

    def _check_account_sharing(self, user_id: int, ip_address: str):
        """Check for account sharing (multiple IPs in short time)."""
        hour_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=1)

        unique_ips = self.db.query(func.count(func.distinct(UserSession.ip_address))).filter(
            UserSession.user_id == user_id,
            UserSession.started_at >= hour_ago
        ).scalar()

        if unique_ips >= ABUSE_THRESHOLDS["unique_ips_per_hour"]:
            self._create_abuse_flag(
                user_id=user_id,
                ip_address=ip_address,
                flag_type="account_sharing",
                severity="medium",
                description=f"Possible account sharing: {unique_ips} unique IPs in the last hour",
                details={"unique_ips": unique_ips, "threshold": ABUSE_THRESHOLDS["unique_ips_per_hour"]}
            )

    def _check_api_abuse(self, user_id: int, ip_address: Optional[str]):
        """Check for API abuse (scraping)."""
        minute_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)

        api_calls = self.db.query(func.count(AuditLog.id)).filter(
            AuditLog.user_id == user_id,
            AuditLog.created_at >= minute_ago
        ).scalar()

        if api_calls >= ABUSE_THRESHOLDS["api_calls_per_minute"]:
            self._create_abuse_flag(
                user_id=user_id,
                ip_address=ip_address,
                flag_type="scraping",
                severity="high",
                description=f"Possible scraping: {api_calls} API calls in the last minute",
                details={"api_calls": api_calls, "threshold": ABUSE_THRESHOLDS["api_calls_per_minute"]}
            )

    def _create_abuse_flag(
        self,
        flag_type: str,
        description: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        severity: str = "low",
        details: Optional[Dict] = None
    ):
        """Create an abuse flag (avoid duplicates within 1 hour)."""
        hour_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=1)

        # Check for existing unresolved flag of same type
        existing = self.db.query(AbuseFlag).filter(
            AbuseFlag.flag_type == flag_type,
            AbuseFlag.is_resolved == False,
            AbuseFlag.created_at >= hour_ago
        )

        if user_id:
            existing = existing.filter(AbuseFlag.user_id == user_id)
        elif ip_address:
            existing = existing.filter(AbuseFlag.ip_address == ip_address)

        if existing.first():
            return  # Don't create duplicate

        flag = AbuseFlag(
            user_id=user_id,
            ip_address=ip_address,
            flag_type=flag_type,
            severity=severity,
            description=description,
            details=json.dumps(details) if details else None
        )
        self.db.add(flag)
        self.db.commit()

    def get_abuse_flags(
        self,
        unresolved_only: bool = True,
        user_id: Optional[int] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get abuse flags for admin review."""
        query = self.db.query(AbuseFlag)

        if unresolved_only:
            query = query.filter(AbuseFlag.is_resolved == False)
        if user_id:
            query = query.filter(AbuseFlag.user_id == user_id)
        if severity:
            query = query.filter(AbuseFlag.severity == severity)

        flags = query.order_by(AbuseFlag.created_at.desc()).limit(limit).all()

        return [
            {
                "id": f.id,
                "user_id": f.user_id,
                "user_email": f.user.email if f.user else None,
                "ip_address": f.ip_address,
                "flag_type": f.flag_type,
                "severity": f.severity,
                "description": f.description,
                "details": json.loads(f.details) if f.details else None,
                "is_resolved": f.is_resolved,
                "created_at": f.created_at.isoformat(),
            }
            for f in flags
        ]

    def resolve_abuse_flag(
        self,
        flag_id: int,
        resolved_by: int,
        notes: Optional[str] = None
    ):
        """Resolve an abuse flag."""
        flag = self.db.query(AbuseFlag).filter(AbuseFlag.id == flag_id).first()
        if flag:
            flag.is_resolved = True
            flag.resolved_by = resolved_by
            flag.resolved_at = datetime.datetime.utcnow()
            flag.resolution_notes = notes
            self.db.commit()

    # =========================================================================
    # Usage Metrics
    # =========================================================================

    def track_usage(
        self,
        user_id: int,
        metric: str,
        increment: int = 1
    ):
        """Track a usage metric."""
        today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        metrics = self.db.query(UsageMetrics).filter(
            UsageMetrics.user_id == user_id,
            UsageMetrics.date == today
        ).first()

        if not metrics:
            metrics = UsageMetrics(user_id=user_id, date=today)
            self.db.add(metrics)
            self.db.commit()

        # Increment the appropriate field
        if hasattr(metrics, metric):
            current = getattr(metrics, metric) or 0
            setattr(metrics, metric, current + increment)
            self.db.commit()

    def get_user_metrics(
        self,
        user_id: int,
        days: int = 30
    ) -> List[Dict]:
        """Get usage metrics for a user."""
        start_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)

        metrics = self.db.query(UsageMetrics).filter(
            UsageMetrics.user_id == user_id,
            UsageMetrics.date >= start_date
        ).order_by(UsageMetrics.date.desc()).all()

        return [
            {
                "date": m.date.isoformat(),
                "api_calls": m.api_calls,
                "documents_uploaded": m.documents_uploaded,
                "documents_viewed": m.documents_viewed,
                "ai_analyses_run": m.ai_analyses_run,
                "reports_generated": m.reports_generated,
                "sessions_count": m.sessions_count,
                "syncs_triggered": m.syncs_triggered,
            }
            for m in metrics
        ]

    def get_system_metrics(self, days: int = 7) -> Dict:
        """Get system-wide metrics for admin dashboard."""
        start_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)

        # Aggregate metrics
        totals = self.db.query(
            func.sum(UsageMetrics.api_calls).label("api_calls"),
            func.sum(UsageMetrics.documents_uploaded).label("documents_uploaded"),
            func.sum(UsageMetrics.ai_analyses_run).label("ai_analyses_run"),
            func.sum(UsageMetrics.reports_generated).label("reports_generated"),
            func.sum(UsageMetrics.syncs_triggered).label("syncs_triggered"),
            func.count(func.distinct(UsageMetrics.user_id)).label("active_users"),
        ).filter(UsageMetrics.date >= start_date).first()

        # Daily breakdown
        daily = self.db.query(
            UsageMetrics.date,
            func.sum(UsageMetrics.api_calls).label("api_calls"),
            func.sum(UsageMetrics.documents_uploaded).label("documents_uploaded"),
            func.sum(UsageMetrics.ai_analyses_run).label("ai_analyses_run"),
            func.count(func.distinct(UsageMetrics.user_id)).label("active_users"),
        ).filter(
            UsageMetrics.date >= start_date
        ).group_by(UsageMetrics.date).order_by(UsageMetrics.date).all()

        return {
            "period_days": days,
            "totals": {
                "api_calls": totals.api_calls or 0,
                "documents_uploaded": totals.documents_uploaded or 0,
                "ai_analyses_run": totals.ai_analyses_run or 0,
                "reports_generated": totals.reports_generated or 0,
                "syncs_triggered": totals.syncs_triggered or 0,
                "active_users": totals.active_users or 0,
            },
            "daily": [
                {
                    "date": d.date.isoformat(),
                    "api_calls": d.api_calls or 0,
                    "documents_uploaded": d.documents_uploaded or 0,
                    "ai_analyses_run": d.ai_analyses_run or 0,
                    "active_users": d.active_users or 0,
                }
                for d in daily
            ]
        }
