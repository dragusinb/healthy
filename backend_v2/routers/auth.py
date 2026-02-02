from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
import httpx
import secrets
import datetime

try:
    from backend_v2.database import get_db
    from backend_v2.models import User
    from backend_v2.auth.security import verify_password, get_password_hash, create_access_token
    from backend_v2.auth.rate_limiter import check_login_rate_limit, check_register_rate_limit, reset_login_rate_limit
    from backend_v2.services.email_service import get_email_service
except ImportError:
    from database import get_db
    from models import User
    from auth.security import verify_password, get_password_hash, create_access_token
    from auth.rate_limiter import check_login_rate_limit, check_register_rate_limit, reset_login_rate_limit
    from services.email_service import get_email_service

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
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
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
        "verification_email_sent": email_service.is_configured()
    }

@router.post("/token", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    _: None = Depends(check_login_rate_limit)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reset rate limit on successful login
    reset_login_rate_limit(request)

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/google", response_model=Token)
async def google_login(token_data: GoogleToken, db: Session = Depends(get_db)):
    """Authenticate with Google OAuth access token."""
    try:
        # Verify the access token with Google's userinfo endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token_data.access_token}"}
            )

            if response.status_code != 200:
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
    elif not user.email_verified:
        # Mark existing user as verified if they login via Google
        user.email_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        db.commit()

    # Generate access token
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "email_verified": True}


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
def reset_password(data: PasswordReset, db: Session = Depends(get_db)):
    """Reset password using token from email link."""
    user = db.query(User).filter(User.reset_token == data.token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    if user.reset_token_expires and user.reset_token_expires < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token expired")

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

    return {"message": "Password reset successfully"}

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
