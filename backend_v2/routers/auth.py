from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
import httpx
import secrets

try:
    from backend_v2.database import get_db
    from backend_v2.models import User
    from backend_v2.auth.security import verify_password, get_password_hash, create_access_token
except ImportError:
    from database import get_db
    from models import User
    from auth.security import verify_password, get_password_hash, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class GoogleToken(BaseModel):
    access_token: str

@router.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
        random_password = secrets.token_urlsafe(32)
        hashed_pw = get_password_hash(random_password)
        user = User(email=email, hashed_password=hashed_pw)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Generate access token
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

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
