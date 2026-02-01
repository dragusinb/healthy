# Per-User Encryption Vault - Implementation Plan

## Overview

This document outlines the implementation plan for per-user encryption, ensuring that sensitive user data is encrypted with keys derived from the user's password. This means that even system administrators with database access cannot read user medical data.

## Goals

1. **Zero-knowledge architecture**: Server stores encrypted data it cannot decrypt
2. **User owns their data**: Only the user's password can unlock their vault
3. **Minimal performance impact**: Efficient encryption/decryption operations
4. **Secure key management**: Proper key derivation and storage
5. **Password change support**: Allow password changes without re-encrypting all data

## Data Classification

### Sensitive Data (Requires Encryption)
| Data Type | Table | Fields |
|-----------|-------|--------|
| Provider Credentials | `linked_accounts` | `username`, `password` |
| Medical Documents | `documents` | PDF file content (filesystem) |
| Biomarker Values | `biomarkers` | `value`, `numeric_value`, `flags` |
| Health Reports | `health_reports` | `content` (JSON with AI analysis) |
| Patient Profile | `user_profiles` | `full_name`, `date_of_birth`, `cnp_prefix` |

### Non-Sensitive Data (No Encryption Needed)
- User email (needed for login)
- User settings/preferences
- Document metadata (provider, date - no personal info)
- Biomarker names (test types, not values)
- Sync job status/logs

## Cryptographic Design

### Key Hierarchy

```
User Password
      |
      v
  [PBKDF2/Argon2] + Salt (stored in DB)
      |
      v
Password-Derived Key (PDK) - never stored
      |
      v
  [AES-256-GCM Decrypt]
      |
      v
Vault Key (VK) - stored encrypted in DB
      |
      v
  [AES-256-GCM Encrypt/Decrypt]
      |
      v
User's Sensitive Data
```

### Why Two Levels?

1. **Password changes**: When user changes password, only need to re-encrypt the Vault Key with new PDK, not all data
2. **Session efficiency**: Vault Key can be held in memory during session
3. **Future features**: Can support recovery keys, trusted devices, etc.

## Implementation Steps

### Phase 1: Database Schema Changes

Add new columns and tables:

```sql
-- User vault metadata
ALTER TABLE users ADD COLUMN vault_salt BYTEA;  -- Salt for key derivation
ALTER TABLE users ADD COLUMN vault_key_encrypted BYTEA;  -- Encrypted vault key
ALTER TABLE users ADD COLUMN vault_version INTEGER DEFAULT 1;  -- For future migrations

-- Mark encrypted fields (add _encrypted suffix during migration)
ALTER TABLE linked_accounts ADD COLUMN username_encrypted BYTEA;
ALTER TABLE linked_accounts ADD COLUMN password_encrypted BYTEA;

ALTER TABLE biomarkers ADD COLUMN value_encrypted BYTEA;
ALTER TABLE biomarkers ADD COLUMN numeric_value_encrypted BYTEA;

ALTER TABLE health_reports ADD COLUMN content_encrypted BYTEA;

ALTER TABLE user_profiles ADD COLUMN full_name_encrypted BYTEA;
ALTER TABLE user_profiles ADD COLUMN date_of_birth_encrypted BYTEA;
ALTER TABLE user_profiles ADD COLUMN cnp_prefix_encrypted BYTEA;
```

### Phase 2: Encryption Service

Create `backend_v2/services/encryption_vault.py`:

```python
import os
import secrets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
import base64

class UserVault:
    """Per-user encryption vault."""

    KDF_ITERATIONS = 600_000  # OWASP recommendation for PBKDF2-SHA256
    SALT_LENGTH = 32
    KEY_LENGTH = 32  # AES-256
    NONCE_LENGTH = 12  # GCM standard

    def __init__(self, user_id: int):
        self.user_id = user_id
        self._vault_key = None  # Decrypted vault key (in memory only)

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=UserVault.KEY_LENGTH,
            salt=salt,
            iterations=UserVault.KDF_ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))

    @staticmethod
    def create_vault(password: str) -> tuple[bytes, bytes, bytes]:
        """
        Create a new vault for a user.
        Returns: (salt, encrypted_vault_key, vault_key)
        """
        # Generate random salt and vault key
        salt = secrets.token_bytes(UserVault.SALT_LENGTH)
        vault_key = secrets.token_bytes(UserVault.KEY_LENGTH)

        # Derive key from password
        pdk = UserVault.derive_key(password, salt)

        # Encrypt vault key with PDK
        encrypted_vault_key = UserVault._encrypt(vault_key, pdk)

        return salt, encrypted_vault_key, vault_key

    def unlock(self, password: str, salt: bytes, encrypted_vault_key: bytes) -> bool:
        """Unlock the vault with user's password."""
        try:
            pdk = self.derive_key(password, salt)
            self._vault_key = self._decrypt(encrypted_vault_key, pdk)
            return True
        except Exception:
            return False

    def is_unlocked(self) -> bool:
        return self._vault_key is not None

    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt data with vault key."""
        if not self._vault_key:
            raise ValueError("Vault is locked")
        return self._encrypt(plaintext.encode('utf-8'), self._vault_key)

    def decrypt(self, ciphertext: bytes) -> str:
        """Decrypt data with vault key."""
        if not self._vault_key:
            raise ValueError("Vault is locked")
        return self._decrypt(ciphertext, self._vault_key).decode('utf-8')

    def encrypt_number(self, value: float) -> bytes:
        """Encrypt numeric value."""
        return self.encrypt(str(value))

    def decrypt_number(self, ciphertext: bytes) -> float:
        """Decrypt numeric value."""
        return float(self.decrypt(ciphertext))

    @staticmethod
    def _encrypt(plaintext: bytes, key: bytes) -> bytes:
        """AES-256-GCM encryption."""
        nonce = secrets.token_bytes(UserVault.NONCE_LENGTH)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext  # Prepend nonce to ciphertext

    @staticmethod
    def _decrypt(data: bytes, key: bytes) -> bytes:
        """AES-256-GCM decryption."""
        nonce = data[:UserVault.NONCE_LENGTH]
        ciphertext = data[UserVault.NONCE_LENGTH:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)

    def change_password(self, old_password: str, new_password: str,
                        salt: bytes, encrypted_vault_key: bytes) -> tuple[bytes, bytes]:
        """
        Change password - re-encrypts vault key only.
        Returns: (new_salt, new_encrypted_vault_key)
        """
        # Decrypt vault key with old password
        old_pdk = self.derive_key(old_password, salt)
        vault_key = self._decrypt(encrypted_vault_key, old_pdk)

        # Create new salt and encrypt vault key with new password
        new_salt = secrets.token_bytes(self.SALT_LENGTH)
        new_pdk = self.derive_key(new_password, new_salt)
        new_encrypted_vault_key = self._encrypt(vault_key, new_pdk)

        return new_salt, new_encrypted_vault_key

    def lock(self):
        """Clear vault key from memory."""
        self._vault_key = None
```

### Phase 3: Session Management

Store unlocked vault in session/request context:

```python
# In auth dependencies
from fastapi import Request

async def get_current_vault(request: Request, current_user: User) -> UserVault:
    """Get unlocked vault from session."""
    vault = request.state.get('vault')
    if not vault or not vault.is_unlocked():
        raise HTTPException(401, "Session expired, please login again")
    return vault

# On login - unlock vault and store in session
async def login(credentials: LoginRequest, request: Request, db: Session):
    user = authenticate_user(credentials.email, credentials.password, db)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    # Unlock user's vault
    vault = UserVault(user.id)
    if not vault.unlock(credentials.password, user.vault_salt, user.vault_key_encrypted):
        raise HTTPException(500, "Vault unlock failed")

    # Store in session (use secure session storage)
    request.state.vault = vault

    # Create access token
    token = create_access_token(user.id)
    return {"access_token": token}
```

**Important**: For stateless JWT auth, the vault key cannot be stored in the token (security risk). Options:

1. **Session-based auth**: Store vault key server-side in Redis/memory cache, keyed by session ID
2. **Re-derive on each request**: Require password in request header (poor UX)
3. **Short-lived vault token**: Separate encrypted token containing vault key, refreshed with password

**Recommended**: Use Redis to store encrypted vault keys with session TTL:

```python
# On login
vault_session_id = secrets.token_urlsafe(32)
redis.setex(f"vault:{vault_session_id}", 3600, vault_key)  # 1 hour TTL

# Return vault_session_id in response, client sends with requests
# On each request, retrieve vault_key from Redis
```

### Phase 4: Data Migration

Migration script to encrypt existing data:

```python
# migration_encrypt_data.py
import getpass
from sqlalchemy.orm import Session
from backend_v2.models import User, LinkedAccount, Biomarker, HealthReport, UserProfile
from backend_v2.services.encryption_vault import UserVault

def migrate_user_data(db: Session, user: User, password: str):
    """Encrypt all existing data for a user."""

    # Create vault if not exists
    if not user.vault_salt:
        salt, encrypted_vault_key, vault_key = UserVault.create_vault(password)
        user.vault_salt = salt
        user.vault_key_encrypted = encrypted_vault_key
        db.commit()

    # Unlock vault
    vault = UserVault(user.id)
    vault.unlock(password, user.vault_salt, user.vault_key_encrypted)

    # Encrypt linked accounts
    for account in user.linked_accounts:
        if account.username and not account.username_encrypted:
            account.username_encrypted = vault.encrypt(account.username)
            account.username = None  # Clear plaintext
        if account.password and not account.password_encrypted:
            account.password_encrypted = vault.encrypt(account.password)
            account.password = None

    # Encrypt biomarkers
    for biomarker in db.query(Biomarker).join(Document).filter(Document.user_id == user.id).all():
        if biomarker.value and not biomarker.value_encrypted:
            biomarker.value_encrypted = vault.encrypt(biomarker.value)
            biomarker.value = "[ENCRYPTED]"  # Placeholder
        if biomarker.numeric_value and not biomarker.numeric_value_encrypted:
            biomarker.numeric_value_encrypted = vault.encrypt_number(biomarker.numeric_value)
            biomarker.numeric_value = None

    # Encrypt health reports
    for report in user.health_reports:
        if report.content and not report.content_encrypted:
            report.content_encrypted = vault.encrypt(json.dumps(report.content))
            report.content = {"encrypted": True}

    # Encrypt user profile
    if user.profile:
        profile = user.profile
        if profile.full_name and not profile.full_name_encrypted:
            profile.full_name_encrypted = vault.encrypt(profile.full_name)
            profile.full_name = "[ENCRYPTED]"
        # ... similar for other fields

    db.commit()
    print(f"Migrated user {user.email}")

def run_migration():
    """Interactive migration - requires each user's password."""
    db = SessionLocal()
    users = db.query(User).all()

    for user in users:
        print(f"\nMigrating user: {user.email}")
        password = getpass.getpass("Enter user's password (or 'skip' to skip): ")
        if password.lower() == 'skip':
            continue
        try:
            migrate_user_data(db, user, password)
        except Exception as e:
            print(f"Error migrating {user.email}: {e}")

    db.close()
```

**Migration Challenge**: We need users' passwords to migrate their data. Options:

1. **Gradual migration**: Encrypt data on next login
2. **Force password reset**: All users must reset password (creates new vault)
3. **Admin migration**: If admin knows passwords (not recommended for production)

**Recommended for MVP**: Gradual migration on login.

### Phase 5: API Layer Updates

Update all APIs that handle sensitive data:

```python
# Example: Get biomarkers
@router.get("/biomarkers")
async def get_biomarkers(
    vault: UserVault = Depends(get_current_vault),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    biomarkers = db.query(Biomarker).join(Document).filter(
        Document.user_id == current_user.id
    ).all()

    # Decrypt values before returning
    result = []
    for b in biomarkers:
        result.append({
            "id": b.id,
            "test_name": b.test_name,
            "value": vault.decrypt(b.value_encrypted) if b.value_encrypted else b.value,
            "numeric_value": vault.decrypt_number(b.numeric_value_encrypted) if b.numeric_value_encrypted else b.numeric_value,
            "unit": b.unit,
            "flags": b.flags,
            # ...
        })

    return result

# Example: Save linked account
@router.post("/linked-accounts")
async def create_linked_account(
    data: LinkedAccountCreate,
    vault: UserVault = Depends(get_current_vault),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = LinkedAccount(
        user_id=current_user.id,
        provider=data.provider,
        username_encrypted=vault.encrypt(data.username),
        password_encrypted=vault.encrypt(data.password),
    )
    db.add(account)
    db.commit()
    return {"id": account.id, "provider": account.provider}
```

### Phase 6: Document File Encryption

For PDF files stored on filesystem:

```python
import os
from pathlib import Path

class EncryptedFileStorage:
    """Store files encrypted with user's vault key."""

    def __init__(self, base_path: str = "data/encrypted"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_document(self, vault: UserVault, user_id: int, doc_id: int, content: bytes) -> str:
        """Save encrypted document."""
        encrypted = vault._encrypt(content, vault._vault_key)

        # Create user directory
        user_dir = self.base_path / str(user_id)
        user_dir.mkdir(exist_ok=True)

        # Save encrypted file
        file_path = user_dir / f"{doc_id}.enc"
        file_path.write_bytes(encrypted)

        return str(file_path)

    def read_document(self, vault: UserVault, user_id: int, doc_id: int) -> bytes:
        """Read and decrypt document."""
        file_path = self.base_path / str(user_id) / f"{doc_id}.enc"
        encrypted = file_path.read_bytes()
        return vault._decrypt(encrypted, vault._vault_key)
```

## Implementation Order

1. **Week 1**: Encryption service + session management
   - Create `encryption_vault.py`
   - Set up Redis for vault session storage
   - Update login flow to create/unlock vaults

2. **Week 2**: New user encryption
   - New users get vault created on registration
   - All new data saved encrypted
   - Test full flow

3. **Week 3**: Migration system
   - Add encrypted columns to DB
   - Create migration scripts
   - Test with dev data

4. **Week 4**: Gradual migration for existing users
   - Encrypt on login
   - Update all API endpoints
   - Handle mixed encrypted/plaintext data

5. **Week 5**: Document encryption
   - Encrypt PDF files
   - Update download/view endpoints
   - Migrate existing files

6. **Week 6**: Testing & hardening
   - Security audit
   - Performance testing
   - Edge case handling

## Security Considerations

### Key Points
- Vault key NEVER logged or sent to client
- Use secure session storage (Redis with encryption at rest)
- Implement rate limiting on login to prevent brute force
- Use constant-time comparison for authentication
- Clear sensitive data from memory when possible

### Password Requirements
- Minimum 12 characters (increased from 6)
- Require complexity (upper, lower, number, symbol)
- Check against common password lists

### Recovery Considerations
- **No recovery key**: If user forgets password, data is lost
- **Optional**: Implement encrypted recovery key stored offline
- **Optional**: Allow trusted contact recovery (future feature)

## Performance Impact

### Overhead Estimates
- Key derivation: ~300ms on login (PBKDF2 600k iterations)
- AES-256-GCM encryption: ~1ms per KB
- Typical biomarker decrypt: <1ms
- Full health report decrypt: ~5ms

### Optimizations
- Cache decrypted data in request scope
- Batch decrypt operations
- Use hardware AES acceleration (available on most modern CPUs)

## Rollback Plan

If issues arise:
1. Keep plaintext columns during migration
2. Add `is_encrypted` flag to records
3. Support both modes for gradual rollout
4. Can revert by copying from encrypted to plaintext columns

## Testing Checklist

- [ ] New user registration creates vault
- [ ] Login unlocks vault correctly
- [ ] Wrong password fails to unlock
- [ ] Data saves encrypted
- [ ] Data retrieves decrypted
- [ ] Password change works
- [ ] Session expiry re-requires login
- [ ] PDF files encrypted/decrypted
- [ ] Migration script works
- [ ] Performance acceptable
- [ ] No sensitive data in logs
- [ ] Memory cleared on logout

## Future Enhancements

1. **Hardware key support** (YubiKey, FIDO2)
2. **Biometric unlock** (for mobile app)
3. **Encrypted search** (searchable encryption for biomarker names)
4. **Data export** (encrypted backup for user)
5. **Multi-device sync** (share vault key securely between devices)
