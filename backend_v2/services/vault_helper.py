"""
Vault Helper - Unified interface for encryption operations.

This service provides a unified interface to both:
1. Per-user vaults (preferred, more secure)
2. Global vault (fallback for legacy data)

The helper automatically selects the appropriate vault for each operation
and provides migration utilities to move data from global vault to per-user vault.
"""

from typing import Optional, Tuple
import json

try:
    from backend_v2.services.user_vault import UserVault, get_user_vault, UserVaultLockedError
    from backend_v2.services.vault import vault as global_vault, VaultLockedError
except ImportError:
    from services.user_vault import UserVault, get_user_vault, UserVaultLockedError
    from services.vault import vault as global_vault, VaultLockedError


class VaultHelper:
    """
    Unified vault interface that supports both per-user and global vaults.

    Usage:
        helper = VaultHelper(user_id)
        encrypted = helper.encrypt_data("sensitive data")
        decrypted = helper.decrypt_data(encrypted)

    The helper will:
    - Use per-user vault if the user has one set up and unlocked
    - Fall back to global vault if per-user vault is not available
    - Raise appropriate errors if neither vault is available
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self._user_vault: Optional[UserVault] = None
        self._use_user_vault: bool = False

        # Try to get user's vault from session
        self._user_vault = get_user_vault(user_id)
        if self._user_vault and self._user_vault.is_unlocked:
            self._use_user_vault = True

    @property
    def is_available(self) -> bool:
        """Check if any vault is available for operations."""
        return self._use_user_vault or global_vault.is_unlocked

    @property
    def uses_user_vault(self) -> bool:
        """Check if per-user vault is being used."""
        return self._use_user_vault

    def _require_available(self):
        """Raise exception if no vault is available."""
        if not self.is_available:
            if self._user_vault is not None:
                raise UserVaultLockedError("User vault is locked. Please unlock your vault.")
            else:
                raise VaultLockedError("No encryption vault available.")

    # String encryption

    def encrypt_data(self, plaintext: str) -> bytes:
        """Encrypt a string."""
        self._require_available()
        if self._use_user_vault:
            return self._user_vault.encrypt_data(plaintext)
        return global_vault.encrypt_data(plaintext)

    def decrypt_data(self, ciphertext: bytes) -> str:
        """Decrypt a string."""
        self._require_available()
        if self._use_user_vault:
            try:
                return self._user_vault.decrypt_data(ciphertext)
            except Exception:
                # May be encrypted with global vault, try that
                if global_vault.is_unlocked:
                    try:
                        return global_vault.decrypt_data(ciphertext)
                    except Exception:
                        raise VaultLockedError("Data encryption key mismatch.")
                else:
                    raise VaultLockedError(
                        "Data was encrypted with legacy encryption. Please log out and back in."
                    )
        return global_vault.decrypt_data(ciphertext)

    # Credential encryption

    def encrypt_credential(self, plaintext: str) -> bytes:
        """Encrypt a credential (username/password)."""
        return self.encrypt_data(plaintext)

    def decrypt_credential(self, ciphertext: bytes) -> str:
        """Decrypt a credential."""
        return self.decrypt_data(ciphertext)

    # Document encryption

    def encrypt_document(self, content: bytes) -> bytes:
        """Encrypt document content (PDF, etc.)."""
        self._require_available()
        if self._use_user_vault:
            return self._user_vault.encrypt_bytes(content)
        return global_vault.encrypt_document(content)

    def decrypt_document(self, ciphertext: bytes) -> bytes:
        """Decrypt document content."""
        self._require_available()
        if self._use_user_vault:
            try:
                return self._user_vault.decrypt_bytes(ciphertext)
            except Exception as user_vault_error:
                # May be encrypted with global vault (legacy data)
                if global_vault.is_unlocked:
                    try:
                        return global_vault.decrypt_document(ciphertext)
                    except Exception:
                        # Neither vault could decrypt it
                        raise VaultLockedError(
                            "Document encryption key mismatch. This document may need to be re-imported."
                        )
                else:
                    # Global vault is locked and user vault failed
                    # This likely means the data was encrypted with global vault
                    raise VaultLockedError(
                        "This document was encrypted with legacy encryption. "
                        "Please contact support or try logging out and back in."
                    )
        return global_vault.decrypt_document(ciphertext)

    # JSON encryption

    def encrypt_json(self, data: dict) -> bytes:
        """Encrypt a JSON-serializable object."""
        self._require_available()
        if self._use_user_vault:
            return self._user_vault.encrypt_json(data)
        return global_vault.encrypt_json(data)

    def decrypt_json(self, ciphertext: bytes) -> dict:
        """Decrypt a JSON object."""
        self._require_available()
        if self._use_user_vault:
            try:
                return self._user_vault.decrypt_json(ciphertext)
            except Exception:
                if global_vault.is_unlocked:
                    try:
                        return global_vault.decrypt_json(ciphertext)
                    except Exception:
                        raise VaultLockedError("Data encryption key mismatch.")
                else:
                    raise VaultLockedError(
                        "Data was encrypted with legacy encryption. Please log out and back in."
                    )
        return global_vault.decrypt_json(ciphertext)

    # Number encryption

    def encrypt_number(self, value: float) -> bytes:
        """Encrypt a numeric value."""
        self._require_available()
        if self._use_user_vault:
            return self._user_vault.encrypt_number(value)
        return global_vault.encrypt_number(value)

    def decrypt_number(self, ciphertext: bytes) -> float:
        """Decrypt a numeric value."""
        self._require_available()
        if self._use_user_vault:
            try:
                return self._user_vault.decrypt_number(ciphertext)
            except Exception:
                if global_vault.is_unlocked:
                    return global_vault.decrypt_number(ciphertext)
                raise
        return global_vault.decrypt_number(ciphertext)


def get_vault_helper(user_id: int) -> VaultHelper:
    """Get a vault helper for the specified user."""
    return VaultHelper(user_id)


def migrate_to_user_vault(user_id: int, old_data: bytes, user_vault: UserVault) -> bytes:
    """
    Migrate data from global vault to per-user vault.

    Args:
        user_id: User ID
        old_data: Data encrypted with global vault
        user_vault: User's unlocked vault

    Returns:
        Data re-encrypted with user's vault
    """
    if not global_vault.is_unlocked:
        raise VaultLockedError("Global vault must be unlocked for migration")

    if not user_vault.is_unlocked:
        raise UserVaultLockedError("User vault must be unlocked for migration")

    # Decrypt with global vault
    decrypted = global_vault.decrypt_data(old_data.decode() if isinstance(old_data, bytes) else old_data)

    # Re-encrypt with user vault
    return user_vault.encrypt_data(decrypted)
