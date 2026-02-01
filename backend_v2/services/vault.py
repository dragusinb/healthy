"""
Vault Service - In-memory encryption key management.

This service holds encryption keys in memory only. Keys are lost on server restart
and must be re-entered by an administrator.

Security Model:
- Master password entered by admin after each server restart
- Keys derived from master password using PBKDF2
- All sensitive data encrypted with AES-256-GCM
- No keys ever written to disk
"""

import os
import secrets
import hashlib
import json
from typing import Optional, Tuple
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
import base64


class VaultError(Exception):
    """Base exception for vault operations."""
    pass


class VaultLockedError(VaultError):
    """Raised when trying to access encrypted data while vault is locked."""
    pass


class VaultNotInitializedError(VaultError):
    """Raised when vault has not been initialized with a master password."""
    pass


class Vault:
    """
    In-memory encryption vault.

    Holds encryption keys in memory only - lost on restart.
    Must be unlocked with master password after each server start.
    """

    # Key derivation parameters (OWASP recommendations)
    KDF_ITERATIONS = 600_000
    SALT_LENGTH = 32
    KEY_LENGTH = 32  # AES-256
    NONCE_LENGTH = 12  # GCM standard

    # Singleton instance
    _instance: Optional['Vault'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # In-memory keys (None when locked)
        self._master_key: Optional[bytes] = None
        self._credentials_key: Optional[bytes] = None
        self._documents_key: Optional[bytes] = None
        self._data_key: Optional[bytes] = None

        # Status
        self._is_unlocked: bool = False

        self._initialized = True

    @property
    def is_unlocked(self) -> bool:
        """Check if vault is currently unlocked."""
        return self._is_unlocked

    @property
    def is_configured(self) -> bool:
        """Check if vault has been initialized (has master password hash in DB)."""
        from backend_v2.database import SessionLocal
        from backend_v2.models import VaultConfig

        db = SessionLocal()
        try:
            config = db.query(VaultConfig).first()
            return config is not None and config.master_key_hash is not None
        finally:
            db.close()

    @staticmethod
    def _derive_key(password: str, salt: bytes, info: bytes = b"") -> bytes:
        """Derive an encryption key from password using PBKDF2."""
        # Add info to password for domain separation
        material = password.encode('utf-8') + info

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=Vault.KEY_LENGTH,
            salt=salt,
            iterations=Vault.KDF_ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(material)

    @staticmethod
    def _hash_password(password: str, salt: bytes) -> str:
        """Create a hash of the password for verification."""
        key = Vault._derive_key(password, salt, b"master-verify")
        return base64.b64encode(key).decode('utf-8')

    def initialize(self, master_password: str) -> Tuple[str, str]:
        """
        Initialize vault with a master password (first-time setup).

        Returns:
            Tuple of (salt_b64, master_key_hash) to store in database
        """
        if len(master_password) < 16:
            raise VaultError("Master password must be at least 16 characters")

        # Generate random salt
        salt = secrets.token_bytes(self.SALT_LENGTH)
        salt_b64 = base64.b64encode(salt).decode('utf-8')

        # Create password hash for verification
        master_key_hash = self._hash_password(master_password, salt)

        # Store in database
        from backend_v2.database import SessionLocal
        from backend_v2.models import VaultConfig

        db = SessionLocal()
        try:
            # Remove any existing config
            db.query(VaultConfig).delete()

            # Create new config
            config = VaultConfig(
                salt=salt_b64,
                master_key_hash=master_key_hash
            )
            db.add(config)
            db.commit()
        finally:
            db.close()

        # Automatically unlock after initialization
        self.unlock(master_password)

        return salt_b64, master_key_hash

    def unlock(self, master_password: str) -> bool:
        """
        Unlock the vault with the master password.

        Derives all encryption keys and stores them in memory.

        Returns:
            True if unlock successful, False if password incorrect
        """
        from backend_v2.database import SessionLocal
        from backend_v2.models import VaultConfig

        db = SessionLocal()
        try:
            config = db.query(VaultConfig).first()
            if not config:
                raise VaultNotInitializedError("Vault not initialized. Call initialize() first.")

            salt = base64.b64decode(config.salt)

            # Verify password
            expected_hash = config.master_key_hash
            actual_hash = self._hash_password(master_password, salt)

            if not secrets.compare_digest(expected_hash, actual_hash):
                return False

            # Derive all keys
            self._master_key = self._derive_key(master_password, salt, b"master")
            self._credentials_key = self._derive_key(master_password, salt, b"credentials")
            self._documents_key = self._derive_key(master_password, salt, b"documents")
            self._data_key = self._derive_key(master_password, salt, b"data")

            self._is_unlocked = True
            return True

        finally:
            db.close()

    def lock(self):
        """Lock the vault, clearing all keys from memory."""
        self._master_key = None
        self._credentials_key = None
        self._documents_key = None
        self._data_key = None
        self._is_unlocked = False

    def _require_unlocked(self):
        """Raise exception if vault is locked."""
        if not self._is_unlocked:
            raise VaultLockedError("Vault is locked. Unlock required.")

    def _encrypt(self, plaintext: bytes, key: bytes) -> bytes:
        """Encrypt data using AES-256-GCM."""
        nonce = secrets.token_bytes(self.NONCE_LENGTH)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext

    def _decrypt(self, data: bytes, key: bytes) -> bytes:
        """Decrypt data using AES-256-GCM."""
        nonce = data[:self.NONCE_LENGTH]
        ciphertext = data[self.NONCE_LENGTH:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)

    # Credential encryption (for provider usernames/passwords)

    def encrypt_credential(self, plaintext: str) -> bytes:
        """Encrypt a credential (username or password)."""
        self._require_unlocked()
        return self._encrypt(plaintext.encode('utf-8'), self._credentials_key)

    def decrypt_credential(self, ciphertext: bytes) -> str:
        """Decrypt a credential."""
        self._require_unlocked()
        return self._decrypt(ciphertext, self._credentials_key).decode('utf-8')

    # Document encryption (for PDF files)

    def encrypt_document(self, content: bytes) -> bytes:
        """Encrypt a document (PDF file content)."""
        self._require_unlocked()
        return self._encrypt(content, self._documents_key)

    def decrypt_document(self, ciphertext: bytes) -> bytes:
        """Decrypt a document."""
        self._require_unlocked()
        return self._decrypt(ciphertext, self._documents_key)

    # Data encryption (for biomarkers, reports, PII)

    def encrypt_data(self, plaintext: str) -> bytes:
        """Encrypt sensitive data (biomarker values, report content, PII)."""
        self._require_unlocked()
        return self._encrypt(plaintext.encode('utf-8'), self._data_key)

    def decrypt_data(self, ciphertext: bytes) -> str:
        """Decrypt sensitive data."""
        self._require_unlocked()
        return self._decrypt(ciphertext, self._data_key).decode('utf-8')

    def encrypt_json(self, data: dict) -> bytes:
        """Encrypt a JSON-serializable object."""
        self._require_unlocked()
        json_str = json.dumps(data, ensure_ascii=False)
        return self._encrypt(json_str.encode('utf-8'), self._data_key)

    def decrypt_json(self, ciphertext: bytes) -> dict:
        """Decrypt to a JSON object."""
        self._require_unlocked()
        json_str = self._decrypt(ciphertext, self._data_key).decode('utf-8')
        return json.loads(json_str)

    def encrypt_number(self, value: float) -> bytes:
        """Encrypt a numeric value."""
        return self.encrypt_data(str(value))

    def decrypt_number(self, ciphertext: bytes) -> float:
        """Decrypt a numeric value."""
        return float(self.decrypt_data(ciphertext))


# Global vault instance
vault = Vault()


def get_vault() -> Vault:
    """Get the global vault instance."""
    return vault


def require_vault_unlocked():
    """FastAPI dependency to require vault to be unlocked."""
    if not vault.is_unlocked:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Vault is locked. Please contact administrator to unlock the system."
        )
    return vault
