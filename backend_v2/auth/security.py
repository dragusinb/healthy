import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY environment variable not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 1  # Token valid for 1 day (reduced from 7 for security)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Supports both bcrypt (current) and legacy PBKDF2 (passlib) formats
    for backwards compatibility during migration.
    """
    password_bytes = plain_password.encode('utf-8')

    # Check if it's a bcrypt hash (starts with $2a$, $2b$, or $2y$)
    if hashed_password.startswith('$2'):
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)

    # Legacy passlib PBKDF2 format (starts with $pbkdf2-)
    if hashed_password.startswith('$pbkdf2-'):
        try:
            from passlib.hash import pbkdf2_sha256
            return pbkdf2_sha256.verify(plain_password, hashed_password)
        except ImportError:
            # passlib not installed, can't verify old hashes
            return False

    # Unknown hash format
    return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
