from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Text, LargeBinary, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone


def utc_now():
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)

try:
    from backend_v2.database import Base
except ImportError:
    from database import Base


class VaultConfig(Base):
    """Stores vault configuration (salt and master key hash for verification)."""
    __tablename__ = "vault_config"

    id = Column(Integer, primary_key=True, index=True)
    salt = Column(String, nullable=False)  # Base64 encoded salt
    master_key_hash = Column(String, nullable=False)  # Hash for password verification
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # Admin access
    language = Column(String, default="ro")  # User's preferred language (ro/en)
    created_at = Column(DateTime, default=utc_now)

    # Email verification
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)

    # Password reset
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)

    # Legal consent tracking
    terms_accepted_at = Column(DateTime, nullable=True)  # When user accepted Terms & Conditions
    privacy_accepted_at = Column(DateTime, nullable=True)  # When user accepted Privacy Policy
    terms_version = Column(String, nullable=True)  # Version of T&C accepted (e.g., "1.0")
    privacy_version = Column(String, nullable=True)  # Version of Privacy Policy accepted

    # Profile fields (legacy - will be removed after migration)
    full_name = Column(String, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String, nullable=True)  # male, female, other
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    blood_type = Column(String, nullable=True)  # A+, A-, B+, B-, AB+, AB-, O+, O-

    # Vault-encrypted profile fields
    full_name_enc = Column(LargeBinary, nullable=True)
    date_of_birth_enc = Column(LargeBinary, nullable=True)
    gender_enc = Column(LargeBinary, nullable=True)
    blood_type_enc = Column(LargeBinary, nullable=True)
    profile_data_enc = Column(LargeBinary, nullable=True)  # JSON with height, weight, etc.

    # Health context (legacy - will be removed after migration)
    allergies = Column(Text, nullable=True)  # JSON array
    chronic_conditions = Column(Text, nullable=True)  # JSON array
    current_medications = Column(Text, nullable=True)  # JSON array
    # Vault-encrypted health context
    health_context_enc = Column(LargeBinary, nullable=True)  # JSON with allergies, conditions, medications

    # Lifestyle factors
    smoking_status = Column(String, nullable=True)  # never, former, current
    alcohol_consumption = Column(String, nullable=True)  # none, occasional, moderate, heavy
    physical_activity = Column(String, nullable=True)  # sedentary, light, moderate, active, very_active

    # Per-user encryption vault
    vault_data = Column(Text, nullable=True)  # JSON with encrypted vault key, salts, recovery key hash
    vault_setup_at = Column(DateTime, nullable=True)  # When user set up their vault

    linked_accounts = relationship("LinkedAccount", back_populates="user")
    documents = relationship("Document", back_populates="user")

class LinkedAccount(Base):
    __tablename__ = "linked_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # Index for user queries
    provider_name = Column(String, index=True)  # Index for provider queries
    username = Column(String, nullable=True)  # Legacy - will be removed after migration
    encrypted_password = Column(String, nullable=True)  # Legacy - will be removed after migration
    # Vault-encrypted fields
    username_enc = Column(LargeBinary, nullable=True)  # Encrypted with vault
    password_enc = Column(LargeBinary, nullable=True)  # Encrypted with vault
    last_sync = Column(DateTime, nullable=True)
    last_sync_error = Column(String, nullable=True)  # Last error message if any
    error_type = Column(String, nullable=True)  # wrong_password, captcha_failed, site_down, session_expired, unknown
    error_acknowledged = Column(Boolean, default=False)  # User has seen the error
    consecutive_failures = Column(Integer, default=0)  # Track consecutive failures
    sync_frequency = Column(String, default="daily")  # daily, weekly, manual
    sync_enabled = Column(Boolean, default=True)  # Enable/disable auto-sync
    status = Column(String, default="ACTIVE")  # ACTIVE, SYNCING, ERROR

    user = relationship("User", back_populates="linked_accounts")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # Index for user queries
    filename = Column(String)
    file_path = Column(String, nullable=True)  # Legacy path (unencrypted files)
    encrypted_path = Column(String, nullable=True)  # Path to vault-encrypted file
    is_encrypted = Column(Boolean, default=False)  # Whether file is vault-encrypted
    provider = Column(String)  # "Regina Maria", "Synevo", "Upload"
    upload_date = Column(DateTime, default=utc_now)
    document_date = Column(DateTime, nullable=True)
    is_processed = Column(Boolean, default=False)
    patient_name = Column(String, nullable=True)  # Legacy - will be removed
    patient_name_enc = Column(LargeBinary, nullable=True)  # Vault-encrypted
    patient_cnp_prefix = Column(String(7), nullable=True)  # Legacy - will be removed
    patient_cnp_enc = Column(LargeBinary, nullable=True)  # Vault-encrypted
    file_hash = Column(String(32), nullable=True, index=True)  # MD5 hash of file content for duplicate detection

    user = relationship("User", back_populates="documents")
    results = relationship("TestResult", back_populates="document", cascade="all, delete-orphan")

class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), index=True)  # Index for document joins
    test_name = Column(String, index=True)  # Original name from lab report
    canonical_name = Column(String, index=True, nullable=True)  # Normalized name for grouping
    value = Column(String, nullable=True)  # Legacy - will be removed after migration
    numeric_value = Column(Float, nullable=True)  # Legacy - will be removed after migration
    # Vault-encrypted fields
    value_enc = Column(LargeBinary, nullable=True)  # Encrypted with vault
    numeric_value_enc = Column(LargeBinary, nullable=True)  # Encrypted with vault
    unit = Column(String, nullable=True)
    reference_range = Column(String, nullable=True)
    flags = Column(String, default="NORMAL")  # NORMAL, HIGH, LOW - kept unencrypted for filtering
    category = Column(String, default="General")

    document = relationship("Document", back_populates="results")


class HealthReport(Base):
    __tablename__ = "health_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    report_type = Column(String)  # "general", "cardiology", "endocrinology", etc.
    title = Column(String)
    summary = Column(Text, nullable=True)  # Legacy - will be removed after migration
    findings = Column(Text, nullable=True)  # Legacy - will be removed after migration
    recommendations = Column(Text, nullable=True)  # Legacy - will be removed after migration
    # Vault-encrypted content (JSON with summary, findings, recommendations)
    content_enc = Column(LargeBinary, nullable=True)  # Encrypted with vault
    risk_level = Column(String, default="normal")  # normal, attention, concern, urgent - kept for filtering
    created_at = Column(DateTime, default=utc_now)
    biomarkers_analyzed = Column(Integer, default=0)

    user = relationship("User", back_populates="health_reports")


class SyncJob(Base):
    """Track sync jobs for reliability and retry logic."""
    __tablename__ = "sync_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    linked_account_id = Column(Integer, ForeignKey("linked_accounts.id"))
    provider_name = Column(String)
    status = Column(String, default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    documents_found = Column(Integer, default=0)
    documents_processed = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User")
    linked_account = relationship("LinkedAccount")


class Notification(Base):
    """Track notifications sent to users."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    notification_type = Column(String)  # new_documents, abnormal_biomarker, analysis_complete, sync_failed, reminder
    title = Column(String)
    message = Column(Text)
    data = Column(Text, nullable=True)  # JSON with additional context
    is_read = Column(Boolean, default=False)
    is_sent_email = Column(Boolean, default=False)  # Email already sent
    created_at = Column(DateTime, default=utc_now)
    sent_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="notifications")


class NotificationPreference(Base):
    """User notification preferences."""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    # Email notification toggles
    email_new_documents = Column(Boolean, default=True)
    email_abnormal_biomarkers = Column(Boolean, default=True)
    email_analysis_complete = Column(Boolean, default=True)
    email_sync_failed = Column(Boolean, default=True)
    email_reminders = Column(Boolean, default=True)

    # Push notification toggles
    push_enabled = Column(Boolean, default=True)
    push_new_documents = Column(Boolean, default=True)
    push_abnormal_biomarkers = Column(Boolean, default=True)
    push_analysis_complete = Column(Boolean, default=True)
    push_sync_failed = Column(Boolean, default=True)

    # Digest preference: immediate, daily, weekly
    email_frequency = Column(String, default="immediate")

    # Quiet hours (don't send during these hours)
    quiet_hours_start = Column(Integer, nullable=True)  # 0-23
    quiet_hours_end = Column(Integer, nullable=True)  # 0-23

    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="notification_preferences")


class PushSubscription(Base):
    """Store Web Push subscriptions for push notifications."""
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    # Web Push subscription data
    endpoint = Column(String, unique=True, index=True)  # Push service endpoint URL
    p256dh_key = Column(String)  # Public key for encryption
    auth_key = Column(String)  # Auth secret for encryption

    # Device info
    user_agent = Column(String, nullable=True)  # Browser/device info
    device_name = Column(String, nullable=True)  # User-friendly device name

    # Status tracking
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, nullable=True)
    failure_count = Column(Integer, default=0)  # Track delivery failures

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="push_subscriptions")


# =============================================================================
# Subscription & Monetization Models
# =============================================================================

class Subscription(Base):
    """User subscription for freemium model."""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    tier = Column(String, default="free")  # free, premium, family

    # Stripe integration
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    stripe_price_id = Column(String, nullable=True)

    # Billing cycle
    billing_cycle = Column(String, default="monthly")  # monthly, yearly
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)

    # Status
    status = Column(String, default="active")  # active, cancelled, past_due, trialing
    cancel_at_period_end = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="subscription")


class UsageTracker(Base):
    """Track user's usage against tier limits."""
    __tablename__ = "usage_trackers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    # Monthly counters (reset on billing cycle)
    ai_analyses_this_month = Column(Integer, default=0)
    month_start = Column(DateTime, default=utc_now)

    # Lifetime stats
    total_ai_analyses = Column(Integer, default=0)
    total_documents_uploaded = Column(Integer, default=0)

    user = relationship("User", back_populates="usage_tracker")


class FamilyGroup(Base):
    """Family group for family subscription plan."""
    __tablename__ = "family_groups"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, default="My Family")
    invite_code = Column(String, unique=True, nullable=True)  # For invite links
    created_at = Column(DateTime, default=utc_now)

    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_family")
    members = relationship("FamilyMember", back_populates="family", cascade="all, delete-orphan")


class FamilyMember(Base):
    """Family group membership."""
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String, default="member")  # owner, admin, member
    joined_at = Column(DateTime, default=utc_now)

    family = relationship("FamilyGroup", back_populates="members")
    user = relationship("User", back_populates="family_membership")


# =============================================================================
# Audit Logging & Abuse Detection Models
# =============================================================================

class AuditLog(Base):
    """Audit log for tracking user actions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for anonymous actions
    action = Column(String, index=True)  # login, logout, upload, delete, analyze, etc.
    resource_type = Column(String, nullable=True)  # document, linked_account, report, etc.
    resource_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)  # JSON with additional context
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    status = Column(String, default="success")  # success, failed, blocked
    created_at = Column(DateTime, default=utc_now, index=True)

    user = relationship("User", back_populates="audit_logs")


class UserSession(Base):
    """Track user sessions for security monitoring."""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    session_token = Column(String, unique=True, index=True)  # JWT token hash or session ID
    ip_address = Column(String)
    user_agent = Column(String, nullable=True)
    device_fingerprint = Column(String, nullable=True)  # Browser fingerprint
    location = Column(String, nullable=True)  # Geo-location from IP
    started_at = Column(DateTime, default=utc_now)
    last_activity = Column(DateTime, default=utc_now)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="sessions")


class AbuseFlag(Base):
    """Track potential abuse incidents."""
    __tablename__ = "abuse_flags"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    ip_address = Column(String, nullable=True, index=True)
    flag_type = Column(String, index=True)  # rate_limit, failed_login, suspicious_activity, account_sharing, scraping
    severity = Column(String, default="low")  # low, medium, high, critical
    description = Column(Text)
    details = Column(Text, nullable=True)  # JSON with additional context
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="abuse_flags")


class RateLimitCounter(Base):
    """Track rate limiting counters."""
    __tablename__ = "rate_limit_counters"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, index=True)  # user_id, ip_address, or combination
    action = Column(String, index=True)  # api_call, login, upload, analyze, etc.
    count = Column(Integer, default=0)
    window_start = Column(DateTime, default=utc_now)
    window_minutes = Column(Integer, default=60)  # Window size in minutes

    __table_args__ = (
        # Composite index for fast lookups
        Index('ix_rate_limit_identifier_action', 'identifier', 'action'),
    )


class UsageMetrics(Base):
    """Daily usage metrics for analytics."""
    __tablename__ = "usage_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    date = Column(DateTime, index=True)  # Date (day granularity)

    # API usage
    api_calls = Column(Integer, default=0)

    # Feature usage
    documents_uploaded = Column(Integer, default=0)
    documents_viewed = Column(Integer, default=0)
    documents_deleted = Column(Integer, default=0)
    ai_analyses_run = Column(Integer, default=0)
    biomarkers_viewed = Column(Integer, default=0)
    reports_generated = Column(Integer, default=0)
    reports_exported = Column(Integer, default=0)

    # Session metrics
    sessions_count = Column(Integer, default=0)
    total_session_minutes = Column(Integer, default=0)

    # Sync metrics
    syncs_triggered = Column(Integer, default=0)
    syncs_completed = Column(Integer, default=0)
    syncs_failed = Column(Integer, default=0)

    user = relationship("User", back_populates="usage_metrics")

    __table_args__ = (
        Index('ix_usage_metrics_user_date', 'user_id', 'date'),
    )


class OpenAIUsageLog(Base):
    """Track individual OpenAI API calls for monitoring and cost analysis."""
    __tablename__ = "openai_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=utc_now, index=True)
    date = Column(String, index=True)  # YYYY-MM-DD for daily aggregation

    # API call details
    model = Column(String)  # gpt-4o, gpt-4o-mini, etc.
    purpose = Column(String)  # document_parsing, profile_extraction, health_analysis
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Cost tracking (estimated based on model pricing)
    cost_usd = Column(Float, default=0.0)

    # Optional user attribution
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Additional context
    success = Column(Boolean, default=True)
    error_message = Column(String, nullable=True)

    __table_args__ = (
        Index('ix_openai_usage_date_purpose', 'date', 'purpose'),
    )


# =============================================================================
# Support Ticket Models
# =============================================================================

class SupportTicket(Base):
    """Support tickets created via feedback button."""
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String, unique=True, index=True)  # e.g. TICK-001
    subject = Column(String, default="Feedback")
    description = Column(Text)
    page_url = Column(String)  # URL where feedback was submitted
    type = Column(String, default="feedback")  # feedback, bug, feature
    priority = Column(String, default="normal")  # low, normal, high, urgent
    status = Column(String, default="open")  # open, in_progress, resolved, closed

    # Reporter info
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reporter_email = Column(String)
    reporter_name = Column(String, nullable=True)

    # AI processing
    ai_status = Column(String, default="pending")  # pending, processing, fixed, skipped, escalated
    ai_response = Column(Text, nullable=True)
    ai_fixed_at = Column(DateTime, nullable=True)

    # Timestamps
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    reporter = relationship("User", back_populates="support_tickets")
    replies = relationship("SupportTicketReply", back_populates="ticket", cascade="all, delete-orphan")
    attachments = relationship("SupportTicketAttachment", back_populates="ticket", cascade="all, delete-orphan")


class SupportTicketReply(Base):
    """Replies to support tickets."""
    __tablename__ = "support_ticket_replies"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), index=True)
    message = Column(Text)
    author_email = Column(String)
    author_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    ticket = relationship("SupportTicket", back_populates="replies")
    attachments = relationship("SupportTicketAttachment", back_populates="reply", cascade="all, delete-orphan")


class SupportTicketAttachment(Base):
    """Attachments for support tickets (screenshots, files)."""
    __tablename__ = "support_ticket_attachments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), index=True)
    reply_id = Column(Integer, ForeignKey("support_ticket_replies.id"), nullable=True)

    file_name = Column(String)
    file_path = Column(String)  # Path to file on disk
    file_type = Column(String)  # MIME type
    file_size = Column(Integer)  # Size in bytes
    uploaded_by_name = Column(String, nullable=True)

    created_at = Column(DateTime, default=utc_now)

    ticket = relationship("SupportTicket", back_populates="attachments")
    reply = relationship("SupportTicketReply", back_populates="attachments")


# Add relationships to User model
User.health_reports = relationship("HealthReport", back_populates="user")
User.notifications = relationship("Notification", back_populates="user")
User.notification_preferences = relationship("NotificationPreference", back_populates="user", uselist=False)
User.subscription = relationship("Subscription", back_populates="user", uselist=False)
User.usage_tracker = relationship("UsageTracker", back_populates="user", uselist=False)
User.owned_family = relationship("FamilyGroup", back_populates="owner", foreign_keys="FamilyGroup.owner_id", uselist=False)
User.family_membership = relationship("FamilyMember", back_populates="user", uselist=False)
User.audit_logs = relationship("AuditLog", back_populates="user")
User.sessions = relationship("UserSession", back_populates="user")
User.abuse_flags = relationship("AbuseFlag", foreign_keys="AbuseFlag.user_id", back_populates="user")
User.usage_metrics = relationship("UsageMetrics", back_populates="user")
User.push_subscriptions = relationship("PushSubscription", back_populates="user")
User.support_tickets = relationship("SupportTicket", back_populates="reporter")
