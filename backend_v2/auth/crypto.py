"""Encryption utilities for sensitive data storage."""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Get encryption key from environment or generate a warning
_ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

def _get_fernet():
    """Get Fernet instance for encryption/decryption."""
    if not _ENCRYPTION_KEY:
        raise ValueError(
            "ENCRYPTION_KEY not set. Generate one with: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )

    # If the key is a passphrase, derive a proper key from it
    if len(_ENCRYPTION_KEY) == 44 and _ENCRYPTION_KEY.endswith("="):
        # Already a valid Fernet key
        return Fernet(_ENCRYPTION_KEY.encode())
    else:
        # Derive key from passphrase using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"healthy_salt_v1",  # Fixed salt - acceptable for this use case
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(_ENCRYPTION_KEY.encode()))
        return Fernet(key)


def encrypt_password(plain_password: str) -> str:
    """Encrypt a password for storage."""
    if not plain_password:
        return ""

    f = _get_fernet()  # Will raise ValueError if ENCRYPTION_KEY not set
    encrypted = f.encrypt(plain_password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password: str) -> str:
    """Decrypt a stored password."""
    if not encrypted_password:
        return ""

    # Handle legacy plain text passwords
    if encrypted_password.startswith("PLAIN:"):
        return encrypted_password[6:]

    try:
        f = _get_fernet()
        decrypted = f.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except ValueError as e:
        print(f"WARNING: {e}")
        # Assume it's a legacy plain password
        return encrypted_password
    except Exception as e:
        print(f"Decryption failed: {e}")
        # Return as-is for legacy compatibility
        return encrypted_password
