from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
import httpx
import secrets
import datetime

import json

try:
    from backend_v2.database import get_db
    from backend_v2.models import User
    from backend_v2.auth.security import verify_password, get_password_hash, create_access_token
    from backend_v2.auth.rate_limiter import check_login_rate_limit, check_register_rate_limit, reset_login_rate_limit
    from backend_v2.services.email_service import get_email_service
    from backend_v2.services.audit_service import AuditService
    from backend_v2.services.user_vault import UserVault, set_user_vault_session, get_user_vault
except ImportError:
    from database import get_db
    from models import User
    from auth.security import verify_password, get_password_hash, create_access_token
    from auth.rate_limiter import check_login_rate_limit, check_register_rate_limit, reset_login_rate_limit
    from services.email_service import get_email_service
    from services.audit_service import AuditService
    from services.user_vault import UserVault, set_user_vault_session, get_user_vault

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    accepted_terms: bool = False
    terms_version: str = None
    privacy_version: str = None

    @field_validator('password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class GoogleToken(BaseModel):
    access_token: str

class EmailVerifyRequest(BaseModel):
    token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class PasswordResetWithRecovery(BaseModel):
    token: str
    new_password: str
    recovery_key: str

    @field_validator('new_password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

def generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)

@router.post("/register")
def register(
    user: UserCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(check_register_rate_limit)
):
    audit = AuditService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        # Log failed registration attempt (email exists)
        audit.log_action(
            user_id=None,
            action="register",
            resource_type="user",
            details={"email": user.email, "reason": "email_exists"},
            ip_address=ip_address,
            user_agent=user_agent,
            status="failed"
        )
        raise HTTPException(status_code=400, detail="Email already registered")

    # Generate verification token
    verification_token = generate_token()
    token_expires = datetime.datetime.utcnow() + datetime.timedelta(hours=24)

    hashed_pw = get_password_hash(user.password)

    # Set consent timestamps if accepted
    consent_time = datetime.datetime.utcnow() if user.accepted_terms else None

    new_user = User(
        email=user.email,
        hashed_password=hashed_pw,
        email_verified=False,
        verification_token=verification_token,
        verification_token_expires=token_expires,
        terms_accepted_at=consent_time,
        privacy_accepted_at=consent_time,
        terms_version=user.terms_version if user.accepted_terms else None,
        privacy_version=user.privacy_version if user.accepted_terms else None
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Set up the user's encryption vault
    try:
        vault = UserVault(new_user.id)
        vault_result = vault.setup_vault(user.password)
    except Exception as e:
        # Vault setup failed - delete user to avoid orphaned account
        logging.error(f"Vault setup failed for user {new_user.id}: {e}")
        db.delete(new_user)
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to initialize encryption vault. Please try again.")

    # Store vault configuration in database
    new_user.vault_data = json.dumps(vault_result['vault_data'])
    new_user.vault_setup_at = datetime.datetime.utcnow()
    db.commit()

    # Store unlocked vault in session
    set_user_vault_session(new_user.id, vault)

    # Get recovery key to show to user (ONCE - they must save it!)
    recovery_key = vault_result['recovery_key']

    # Log successful registration
    audit.log_action(
        user_id=new_user.id,
        action="register",
        resource_type="user",
        resource_id=new_user.id,
        details={"email": new_user.email, "vault_setup": True},
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )

    # Send verification email in background
    email_service = get_email_service()
    if email_service.is_configured():
        background_tasks.add_task(
            email_service.send_verification_email,
            new_user.email,
            verification_token,
            new_user.language
        )

    access_token = create_access_token(data={"sub": new_user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email_verified": False,
        "verification_email_sent": email_service.is_configured(),
        "recovery_key": recovery_key  # User MUST save this - only shown once!
    }

@router.post("/token", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    _: None = Depends(check_login_rate_limit)
):
    audit = AuditService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Log failed login attempt
        audit.log_action(
            user_id=user.id if user else None,
            action="login",
            resource_type="session",
            details={"email": form_data.username, "reason": "invalid_credentials"},
            ip_address=ip_address,
            user_agent=user_agent,
            status="failed"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reset rate limit on successful login
    reset_login_rate_limit(request)

    # Unlock user's encryption vault
    vault_unlocked = False
    if user.vault_data:
        vault = UserVault(user.id)
        vault_data = json.loads(user.vault_data)
        vault_unlocked = vault.unlock_with_password(form_data.password, vault_data)
        if vault_unlocked:
            set_user_vault_session(user.id, vault)

    # Log successful login
    audit.log_action(
        user_id=user.id,
        action="login",
        resource_type="session",
        details={"email": user.email, "vault_unlocked": vault_unlocked},
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "vault_unlocked": vault_unlocked}


@router.post("/google", response_model=Token)
async def google_login(token_data: GoogleToken, request: Request, db: Session = Depends(get_db)):
    """Authenticate with Google OAuth access token."""
    audit = AuditService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        # Verify the access token with Google's userinfo endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token_data.access_token}"}
            )

            if response.status_code != 200:
                audit.log_action(
                    user_id=None,
                    action="google_login",
                    resource_type="session",
                    details={"reason": "invalid_token"},
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status="failed"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google access token"
                )

            google_user = response.json()
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to verify Google token"
        )

    email = google_user.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided by Google"
        )

    # Check if email is verified
    if not google_user.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google email not verified"
        )

    # Find or create user
    user = db.query(User).filter(User.email == email).first()
    is_new_user = False

    if not user:
        # Create new user with random password (they'll use Google to login)
        # Google-authenticated users are automatically verified
        # They accept terms implicitly by using the service
        random_password = secrets.token_urlsafe(32)
        hashed_pw = get_password_hash(random_password)
        consent_time = datetime.datetime.utcnow()
        user = User(
            email=email,
            hashed_password=hashed_pw,
            email_verified=True,
            terms_accepted_at=consent_time,
            privacy_accepted_at=consent_time,
            terms_version='1.0',
            privacy_version='1.0'
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        is_new_user = True
    elif not user.email_verified:
        # Mark existing user as verified if they login via Google
        user.email_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        db.commit()

    # Log the action
    action = "register" if is_new_user else "google_login"
    audit.log_action(
        user_id=user.id,
        action=action,
        resource_type="session",
        details={"email": email, "provider": "google"},
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )

    # Determine next step for user
    # - New user without vault: needs to set password (required for encryption)
    # - Existing user with vault: needs to unlock with password
    # - Existing user without vault: needs to set password
    needs_password_setup = not user.vault_data
    needs_vault_unlock = user.vault_data is not None

    # Generate access token
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email_verified": True,
        "is_new_user": is_new_user,
        "needs_password_setup": needs_password_setup,  # Must set password for encryption
        "needs_vault_unlock": needs_vault_unlock,       # Must enter password to unlock data
    }


@router.post("/verify-email")
def verify_email(data: EmailVerifyRequest, db: Session = Depends(get_db)):
    """Verify email address using token from email link."""
    user = db.query(User).filter(User.verification_token == data.token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    if user.verification_token_expires and user.verification_token_expires < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification token expired")

    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()

    return {"message": "Email verified successfully", "email": user.email}


@router.post("/resend-verification")
def resend_verification(
    data: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Resend verification email."""
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a verification link has been sent"}

    if user.email_verified:
        return {"message": "Email is already verified"}

    # Generate new token
    verification_token = generate_token()
    user.verification_token = verification_token
    user.verification_token_expires = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    db.commit()

    # Send email
    email_service = get_email_service()
    if email_service.is_configured():
        background_tasks.add_task(
            email_service.send_verification_email,
            user.email,
            verification_token,
            user.language
        )

    return {"message": "If the email exists, a verification link has been sent"}


@router.post("/forgot-password")
def forgot_password(
    data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request password reset email."""
    user = db.query(User).filter(User.email == data.email).first()

    # Always return success to not reveal if email exists
    if not user:
        return {"message": "If the email exists, a password reset link has been sent"}

    # Generate reset token (expires in 1 hour)
    reset_token = generate_token()
    user.reset_token = reset_token
    user.reset_token_expires = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    db.commit()

    # Send email
    email_service = get_email_service()
    if email_service.is_configured():
        background_tasks.add_task(
            email_service.send_password_reset_email,
            user.email,
            reset_token,
            user.language
        )

    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
def reset_password(data: PasswordReset, request: Request, db: Session = Depends(get_db)):
    """Reset password using token from email link.
    Note: This endpoint is for users WITHOUT a vault set up.
    For users with vault, use /reset-password-with-recovery endpoint.
    """
    audit = AuditService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user = db.query(User).filter(User.reset_token == data.token).first()

    if not user:
        audit.log_action(
            user_id=None,
            action="password_reset",
            resource_type="user",
            details={"reason": "invalid_token"},
            ip_address=ip_address,
            user_agent=user_agent,
            status="failed"
        )
        raise HTTPException(status_code=400, detail="Invalid reset token")

    if user.reset_token_expires and user.reset_token_expires < datetime.datetime.utcnow():
        audit.log_action(
            user_id=user.id,
            action="password_reset",
            resource_type="user",
            details={"reason": "token_expired"},
            ip_address=ip_address,
            user_agent=user_agent,
            status="failed"
        )
        raise HTTPException(status_code=400, detail="Reset token expired")

    # Check if user has vault - they need to use recovery key
    if user.vault_data:
        raise HTTPException(
            status_code=400,
            detail="This account has encrypted data. Please use the recovery key to reset your password."
        )

    # Update password (no vault to re-encrypt)
    user.hashed_password = get_password_hash(data.new_password)
    user.reset_token = None
    user.reset_token_expires = None

    # Also verify email if not already verified
    if not user.email_verified:
        user.email_verified = True
        user.verification_token = None
        user.verification_token_expires = None

    db.commit()

    # Log successful password reset
    audit.log_action(
        user_id=user.id,
        action="password_reset",
        resource_type="user",
        details={"email": user.email, "vault": False},
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )

    return {"message": "Password reset successfully"}


@router.post("/reset-password-with-recovery")
def reset_password_with_recovery(data: PasswordResetWithRecovery, request: Request, db: Session = Depends(get_db)):
    """Reset password using token from email AND recovery key.
    Required for accounts with encrypted data to re-encrypt the vault key.
    """
    audit = AuditService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user = db.query(User).filter(User.reset_token == data.token).first()

    if not user:
        audit.log_action(
            user_id=None,
            action="password_reset_recovery",
            resource_type="user",
            details={"reason": "invalid_token"},
            ip_address=ip_address,
            user_agent=user_agent,
            status="failed"
        )
        raise HTTPException(status_code=400, detail="Invalid reset token")

    if user.reset_token_expires and user.reset_token_expires < datetime.datetime.utcnow():
        audit.log_action(
            user_id=user.id,
            action="password_reset_recovery",
            resource_type="user",
            details={"reason": "token_expired"},
            ip_address=ip_address,
            user_agent=user_agent,
            status="failed"
        )
        raise HTTPException(status_code=400, detail="Reset token expired")

    # Verify and unlock vault with recovery key
    if user.vault_data:
        vault = UserVault(user.id)
        vault_data = json.loads(user.vault_data)

        if not vault.unlock_with_recovery_key(data.recovery_key, vault_data):
            audit.log_action(
                user_id=user.id,
                action="password_reset_recovery",
                resource_type="user",
                details={"reason": "invalid_recovery_key"},
                ip_address=ip_address,
                user_agent=user_agent,
                status="failed"
            )
            raise HTTPException(status_code=400, detail="Invalid recovery key")

        # Re-encrypt vault key with new password
        new_vault_data = vault.change_password(data.new_password, vault_data)
        user.vault_data = json.dumps(new_vault_data)

        # Store unlocked vault in session
        set_user_vault_session(user.id, vault)

    # Update password
    user.hashed_password = get_password_hash(data.new_password)
    user.reset_token = None
    user.reset_token_expires = None

    # Also verify email if not already verified
    if not user.email_verified:
        user.email_verified = True
        user.verification_token = None
        user.verification_token_expires = None

    db.commit()

    # Log successful password reset
    audit.log_action(
        user_id=user.id,
        action="password_reset_recovery",
        resource_type="user",
        details={"email": user.email, "vault": True},
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )

    return {"message": "Password reset successfully", "vault_unlocked": True}

@router.get("/check-reset-token/{token}")
def check_reset_token(token: str, db: Session = Depends(get_db)):
    """Check if a reset token is valid and whether it requires a recovery key."""
    user = db.query(User).filter(User.reset_token == token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    if user.reset_token_expires and user.reset_token_expires < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token expired")

    return {
        "valid": True,
        "requires_recovery_key": user.vault_data is not None
    }


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Change password for logged-in user. Re-encrypts vault key with new password."""
    from jose import jwt
    try:
        from backend_v2.auth.security import SECRET_KEY, ALGORITHM
    except ImportError:
        from auth.security import SECRET_KEY, ALGORITHM

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    current_user = db.query(User).filter(User.email == email).first()
    if current_user is None:
        raise HTTPException(status_code=401, detail="User not found")

    audit = AuditService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Verify current password
    if not verify_password(data.current_password, current_user.hashed_password):
        audit.log_action(
            user_id=current_user.id,
            action="change_password",
            resource_type="user",
            details={"reason": "wrong_password"},
            ip_address=ip_address,
            user_agent=user_agent,
            status="failed"
        )
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Update vault if exists
    if current_user.vault_data:
        vault = UserVault(current_user.id)
        vault_data = json.loads(current_user.vault_data)

        # Unlock with current password
        if not vault.unlock_with_password(data.current_password, vault_data):
            raise HTTPException(status_code=500, detail="Failed to unlock vault")

        # Re-encrypt with new password
        new_vault_data = vault.change_password(data.new_password, vault_data)
        current_user.vault_data = json.dumps(new_vault_data)

        # Update session
        set_user_vault_session(current_user.id, vault)

    # Update password hash
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()

    audit.log_action(
        user_id=current_user.id,
        action="change_password",
        resource_type="user",
        details={"vault_updated": current_user.vault_data is not None},
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )

    return {"message": "Password changed successfully"}


class SetupPasswordRequest(BaseModel):
    """Used by Google OAuth users to set their password (for encryption + backup login)."""
    password: str

    @field_validator('password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


@router.post("/setup-password")
def setup_password(
    data: SetupPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Set up password for Google OAuth users.

    This password serves TWO purposes:
    1. Encrypts all your medical data (vault key)
    2. Backup login method (can login with email+password instead of Google)

    After this, the user can login with either Google or email+password.
    """
    from jose import jwt
    try:
        from backend_v2.auth.security import SECRET_KEY, ALGORITHM
    except ImportError:
        from auth.security import SECRET_KEY, ALGORITHM

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    current_user = db.query(User).filter(User.email == email).first()
    if current_user is None:
        raise HTTPException(status_code=401, detail="User not found")

    audit = AuditService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Check if vault already exists
    if current_user.vault_data:
        raise HTTPException(status_code=400, detail="Password and encryption already set up")

    # 1. Set the account password (for backup email+password login)
    current_user.hashed_password = get_password_hash(data.password)

    # 2. Create the encryption vault with the same password
    vault = UserVault(current_user.id)
    vault_result = vault.setup_vault(data.password)

    # Store vault configuration
    current_user.vault_data = json.dumps(vault_result['vault_data'])
    current_user.vault_setup_at = datetime.datetime.utcnow()
    db.commit()

    # Store unlocked vault in session
    set_user_vault_session(current_user.id, vault)

    audit.log_action(
        user_id=current_user.id,
        action="setup_password",
        resource_type="user",
        details={"email": current_user.email, "method": "google_oauth"},
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )

    return {
        "message": "Password and encryption set up successfully",
        "recovery_key": vault_result['recovery_key'],  # User MUST save this!
        "can_login_with_password": True  # Now they can use email+password login too
    }


@router.get("/vault-status")
def get_vault_status(request: Request, db: Session = Depends(get_db)):
    """Check current user's vault status."""
    from jose import jwt
    try:
        from backend_v2.auth.security import SECRET_KEY, ALGORITHM
    except ImportError:
        from auth.security import SECRET_KEY, ALGORITHM

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    current_user = db.query(User).filter(User.email == email).first()
    if current_user is None:
        raise HTTPException(status_code=401, detail="User not found")

    vault = get_user_vault(current_user.id)

    return {
        "vault_exists": current_user.vault_data is not None,
        "vault_unlocked": vault is not None and vault.is_unlocked,
        "vault_setup_at": current_user.vault_setup_at.isoformat() if current_user.vault_setup_at else None
    }


class UnlockDataRequest(BaseModel):
    password: str


@router.post("/unlock-data")
def unlock_data(
    data: UnlockDataRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Unlock encrypted data after Google OAuth login.

    When you login with Google, we verify your identity but can't access
    your encrypted data. Enter your password to unlock your medical records.

    This is the same password you set up when you first registered.
    """
    from jose import jwt
    try:
        from backend_v2.auth.security import SECRET_KEY, ALGORITHM
    except ImportError:
        from auth.security import SECRET_KEY, ALGORITHM

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    current_user = db.query(User).filter(User.email == email).first()
    if current_user is None:
        raise HTTPException(status_code=401, detail="User not found")

    audit = AuditService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Check if vault exists
    if not current_user.vault_data:
        raise HTTPException(status_code=400, detail="No encrypted data to unlock")

    # Try to unlock
    vault = UserVault(current_user.id)
    vault_data = json.loads(current_user.vault_data)

    if not vault.unlock_with_password(data.password, vault_data):
        audit.log_action(
            user_id=current_user.id,
            action="unlock_data",
            resource_type="user",
            details={"reason": "wrong_password"},
            ip_address=ip_address,
            user_agent=user_agent,
            status="failed"
        )
        raise HTTPException(status_code=400, detail="Incorrect password")

    # Store unlocked vault in session
    set_user_vault_session(current_user.id, vault)

    audit.log_action(
        user_id=current_user.id,
        action="unlock_data",
        resource_type="user",
        details={"email": current_user.email},
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )

    return {"message": "Data unlocked successfully", "vault_unlocked": True}


# --- Seeding Utility ---
# SECURITY: Only run in development/local environments
import os

def seed_default_user(db: Session):
    """
    Seeds a default development user. Only runs when ENVIRONMENT is 'development'.
    In production, users must register through the normal flow.
    """
    env = os.environ.get("ENVIRONMENT", "production")
    if env != "development":
        return  # Don't seed default user in production

    email = os.environ.get("DEV_USER_EMAIL", "dev@localhost")
    pwd = os.environ.get("DEV_USER_PASSWORD")

    if not pwd:
        print("DEV_USER_PASSWORD not set, skipping default user seed.")
        return

    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"[DEV MODE] Seeding default user: {email}")
        hashed = get_password_hash(pwd)
        u = User(email=email, hashed_password=hashed)
        db.add(u)
        db.commit()
    else:
        print(f"[DEV MODE] User {email} already exists.")
