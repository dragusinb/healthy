from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Text, LargeBinary
from sqlalchemy.orm import relationship
import datetime

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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # Admin access
    language = Column(String, default="ro")  # User's preferred language (ro/en)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Email verification
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)

    # Password reset
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)

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

    linked_accounts = relationship("LinkedAccount", back_populates="user")
    documents = relationship("Document", back_populates="user")

class LinkedAccount(Base):
    __tablename__ = "linked_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    provider_name = Column(String)  # "Regina Maria" or "Synevo"
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
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String)
    file_path = Column(String, nullable=True)  # Legacy path (unencrypted files)
    encrypted_path = Column(String, nullable=True)  # Path to vault-encrypted file
    is_encrypted = Column(Boolean, default=False)  # Whether file is vault-encrypted
    provider = Column(String)  # "Regina Maria", "Synevo", "Upload"
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
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
    document_id = Column(Integer, ForeignKey("documents.id"))
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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
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

    # Digest preference: immediate, daily, weekly
    email_frequency = Column(String, default="immediate")

    # Quiet hours (don't send during these hours)
    quiet_hours_start = Column(Integer, nullable=True)  # 0-23
    quiet_hours_end = Column(Integer, nullable=True)  # 0-23

    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="notification_preferences")


# Add relationship to User model
User.health_reports = relationship("HealthReport", back_populates="user")
User.notifications = relationship("Notification", back_populates="user")
User.notification_preferences = relationship("NotificationPreference", back_populates="user", uselist=False)
