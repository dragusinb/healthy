"""Encryption utilities for sensitive data storage."""
import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

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
        # WARNING: Using passphrase-based key derivation is less secure.
        # Prefer using a proper Fernet key (44-char base64 ending with =).
        # Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        import logging
        logging.warning(
            "ENCRYPTION_KEY appears to be a passphrase, not a proper Fernet key. "
            "For better security, use a randomly generated Fernet key."
        )
        # Use deployment-specific salt from env - REQUIRED for security
        salt_str = os.getenv("ENCRYPTION_SALT") or os.getenv("INSTANCE_ID")
        if not salt_str:
            raise ValueError(
                "ENCRYPTION_SALT or INSTANCE_ID environment variable required when using passphrase-based key. "
                "Set ENCRYPTION_SALT to a unique random string for this deployment."
            )
        salt = salt_str.encode()[:16].ljust(16, b'\x00')  # Ensure 16 bytes

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
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
        logger.warning(f"Encryption key issue: {e}")
        # Assume it's a legacy plain password
        return encrypted_password
    except Exception as e:
        logger.warning(f"Decryption failed, returning as legacy password: {type(e).__name__}")
        # Return as-is for legacy compatibility
        return encrypted_password
