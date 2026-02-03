"""
Per-User Encryption Vault Service

Each user has their own encryption key derived from their password.
A recovery key is generated that users must save - it can recover the vault
if they forget their password.

Security Model:
- Each user has a unique "vault key" (random AES-256 key)
- Vault key is encrypted with password-derived key (PBKDF2)
- Vault key is also encrypted with recovery key (for backup)
- Admin cannot access user data (doesn't know password or recovery key)
- Password change: re-encrypt vault key only (not all data)
- Recovery: use recovery key to decrypt vault key, set new password
"""

import os
import secrets
import hashlib
import json
import base64
from typing import Optional, Tuple, Dict
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


class UserVaultError(Exception):
    """Base exception for user vault operations."""
    pass


class UserVaultLockedError(UserVaultError):
    """Raised when vault is locked and decryption is attempted."""
    pass


class UserVaultNotSetupError(UserVaultError):
    """Raised when user hasn't set up their vault yet."""
    pass


class UserVault:
    """
    Per-user encryption vault.

    Each user has their own vault key that encrypts all their sensitive data.
    The vault key is protected by the user's password and a recovery key.
    """

    # Key derivation parameters (OWASP recommendations)
    KDF_ITERATIONS = 600_000
    SALT_LENGTH = 32
    KEY_LENGTH = 32  # AES-256
    NONCE_LENGTH = 12  # GCM standard
    RECOVERY_KEY_LENGTH = 32  # 256-bit recovery key

    def __init__(self, user_id: int):
        self.user_id = user_id
        self._vault_key: Optional[bytes] = None
        self._is_unlocked: bool = False

    @property
    def is_unlocked(self) -> bool:
        return self._is_unlocked

    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        """Derive an encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=UserVault.KEY_LENGTH,
            salt=salt,
            iterations=UserVault.KDF_ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))

    @staticmethod
    def _encrypt(plaintext: bytes, key: bytes) -> bytes:
        """Encrypt data using AES-256-GCM."""
        nonce = secrets.token_bytes(UserVault.NONCE_LENGTH)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext

    @staticmethod
    def _decrypt(data: bytes, key: bytes) -> bytes:
        """Decrypt data using AES-256-GCM."""
        nonce = data[:UserVault.NONCE_LENGTH]
        ciphertext = data[UserVault.NONCE_LENGTH:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)

    @staticmethod
    def generate_recovery_key() -> str:
        """Generate a human-readable recovery key (base32 encoded, grouped)."""
        # Generate 32 random bytes
        raw_key = secrets.token_bytes(UserVault.RECOVERY_KEY_LENGTH)
        # Encode as base32 (easier to read/type than hex)
        encoded = base64.b32encode(raw_key).decode('utf-8').rstrip('=')
        # Group into 4-character chunks for readability
        groups = [encoded[i:i+4] for i in range(0, len(encoded), 4)]
        return '-'.join(groups)

    @staticmethod
    def _recovery_key_to_bytes(recovery_key: str) -> bytes:
        """Convert recovery key string back to bytes."""
        # Remove dashes and add padding
        clean = recovery_key.replace('-', '').upper()
        # Add padding if needed
        padding = (8 - len(clean) % 8) % 8
        clean += '=' * padding
        return base64.b32decode(clean)

    @staticmethod
    def _hash_recovery_key(recovery_key: str) -> str:
        """Hash recovery key for verification (stored in DB)."""
        raw = UserVault._recovery_key_to_bytes(recovery_key)
        return hashlib.sha256(raw).hexdigest()

    def setup_vault(self, password: str) -> Dict:
        """
        Initialize a new vault for the user.

        Returns:
            Dict with vault_data (to store in DB) and recovery_key (show to user ONCE)
        """
        # Generate random vault key (the actual encryption key)
        vault_key = secrets.token_bytes(self.KEY_LENGTH)

        # Generate salt for password derivation
        password_salt = secrets.token_bytes(self.SALT_LENGTH)

        # Derive key from password
        password_derived_key = self._derive_key(password, password_salt)

        # Encrypt vault key with password-derived key
        encrypted_vault_key_pwd = self._encrypt(vault_key, password_derived_key)

        # Generate recovery key
        recovery_key = self.generate_recovery_key()
        recovery_key_bytes = self._recovery_key_to_bytes(recovery_key)

        # Generate salt for recovery key derivation
        recovery_salt = secrets.token_bytes(self.SALT_LENGTH)

        # Derive key from recovery key
        recovery_derived_key = self._derive_key(
            base64.b64encode(recovery_key_bytes).decode('utf-8'),
            recovery_salt
        )

        # Encrypt vault key with recovery-derived key
        encrypted_vault_key_recovery = self._encrypt(vault_key, recovery_derived_key)

        # Hash recovery key for verification
        recovery_key_hash = self._hash_recovery_key(recovery_key)

        # Store vault key in memory
        self._vault_key = vault_key
        self._is_unlocked = True

        return {
            'vault_data': {
                'password_salt': base64.b64encode(password_salt).decode('utf-8'),
                'encrypted_vault_key': base64.b64encode(encrypted_vault_key_pwd).decode('utf-8'),
                'recovery_salt': base64.b64encode(recovery_salt).decode('utf-8'),
                'encrypted_vault_key_recovery': base64.b64encode(encrypted_vault_key_recovery).decode('utf-8'),
                'recovery_key_hash': recovery_key_hash,
            },
            'recovery_key': recovery_key  # SHOW TO USER ONCE - NEVER STORE THIS
        }

    def unlock_with_password(self, password: str, vault_data: Dict) -> bool:
        """
        Unlock vault using password.

        Args:
            password: User's password
            vault_data: Stored vault configuration from DB

        Returns:
            True if unlocked successfully, False if wrong password
        """
        try:
            password_salt = base64.b64decode(vault_data['password_salt'])
            encrypted_vault_key = base64.b64decode(vault_data['encrypted_vault_key'])

            # Derive key from password
            password_derived_key = self._derive_key(password, password_salt)

            # Try to decrypt vault key
            vault_key = self._decrypt(encrypted_vault_key, password_derived_key)

            self._vault_key = vault_key
            self._is_unlocked = True
            return True

        except Exception:
            return False

    def unlock_with_recovery_key(self, recovery_key: str, vault_data: Dict) -> bool:
        """
        Unlock vault using recovery key.

        Args:
            recovery_key: User's recovery key
            vault_data: Stored vault configuration from DB

        Returns:
            True if unlocked successfully, False if wrong recovery key
        """
        try:
            # Verify recovery key hash first
            expected_hash = vault_data.get('recovery_key_hash', '')
            actual_hash = self._hash_recovery_key(recovery_key)

            if not secrets.compare_digest(expected_hash, actual_hash):
                return False

            recovery_salt = base64.b64decode(vault_data['recovery_salt'])
            encrypted_vault_key = base64.b64decode(vault_data['encrypted_vault_key_recovery'])

            # Derive key from recovery key
            recovery_key_bytes = self._recovery_key_to_bytes(recovery_key)
            recovery_derived_key = self._derive_key(
                base64.b64encode(recovery_key_bytes).decode('utf-8'),
                recovery_salt
            )

            # Try to decrypt vault key
            vault_key = self._decrypt(encrypted_vault_key, recovery_derived_key)

            self._vault_key = vault_key
            self._is_unlocked = True
            return True

        except Exception:
            return False

    def change_password(self, new_password: str, vault_data: Dict) -> Dict:
        """
        Change password while vault is unlocked.
        Re-encrypts vault key with new password but keeps same vault key.

        Args:
            new_password: New password
            vault_data: Current vault configuration

        Returns:
            Updated vault_data to store in DB
        """
        if not self._is_unlocked:
            raise UserVaultLockedError("Vault must be unlocked to change password")

        # Generate new password salt
        new_password_salt = secrets.token_bytes(self.SALT_LENGTH)

        # Derive key from new password
        new_password_derived_key = self._derive_key(new_password, new_password_salt)

        # Encrypt vault key with new password-derived key
        new_encrypted_vault_key = self._encrypt(self._vault_key, new_password_derived_key)

        # Keep recovery key encryption unchanged
        updated_vault_data = vault_data.copy()
        updated_vault_data['password_salt'] = base64.b64encode(new_password_salt).decode('utf-8')
        updated_vault_data['encrypted_vault_key'] = base64.b64encode(new_encrypted_vault_key).decode('utf-8')

        return updated_vault_data

    def lock(self):
        """Lock the vault, clearing the key from memory."""
        self._vault_key = None
        self._is_unlocked = False

    def _require_unlocked(self):
        """Raise exception if vault is locked."""
        if not self._is_unlocked:
            raise UserVaultLockedError("User vault is locked")

    # Encryption methods

    def encrypt_data(self, plaintext: str) -> bytes:
        """Encrypt a string."""
        self._require_unlocked()
        return self._encrypt(plaintext.encode('utf-8'), self._vault_key)

    def decrypt_data(self, ciphertext: bytes) -> str:
        """Decrypt to a string."""
        self._require_unlocked()
        return self._decrypt(ciphertext, self._vault_key).decode('utf-8')

    def encrypt_bytes(self, data: bytes) -> bytes:
        """Encrypt raw bytes (for documents)."""
        self._require_unlocked()
        return self._encrypt(data, self._vault_key)

    def decrypt_bytes(self, ciphertext: bytes) -> bytes:
        """Decrypt to raw bytes."""
        self._require_unlocked()
        return self._decrypt(ciphertext, self._vault_key)

    def encrypt_json(self, data: dict) -> bytes:
        """Encrypt a JSON-serializable object."""
        self._require_unlocked()
        json_str = json.dumps(data, ensure_ascii=False)
        return self._encrypt(json_str.encode('utf-8'), self._vault_key)

    def decrypt_json(self, ciphertext: bytes) -> dict:
        """Decrypt to a JSON object."""
        self._require_unlocked()
        json_str = self._decrypt(ciphertext, self._vault_key).decode('utf-8')
        return json.loads(json_str)

    def encrypt_number(self, value: float) -> bytes:
        """Encrypt a numeric value."""
        return self.encrypt_data(str(value))

    def decrypt_number(self, ciphertext: bytes) -> float:
        """Decrypt a numeric value."""
        return float(self.decrypt_data(ciphertext))


# Session storage for unlocked vaults (in-memory, per-process)
_user_vault_sessions: Dict[int, UserVault] = {}


def get_user_vault(user_id: int) -> Optional[UserVault]:
    """Get an unlocked user vault from session, or None if not unlocked."""
    return _user_vault_sessions.get(user_id)


def set_user_vault_session(user_id: int, vault: UserVault):
    """Store an unlocked vault in the session."""
    _user_vault_sessions[user_id] = vault


def clear_user_vault_session(user_id: int):
    """Clear a user's vault from session (on logout)."""
    if user_id in _user_vault_sessions:
        _user_vault_sessions[user_id].lock()
        del _user_vault_sessions[user_id]


def is_user_vault_unlocked(user_id: int) -> bool:
    """Check if a user's vault is currently unlocked."""
    vault = _user_vault_sessions.get(user_id)
    return vault is not None and vault.is_unlocked
