"""
Vault API endpoints for managing the encryption vault.

These endpoints allow administrators to:
- Initialize the vault (first-time setup)
- Unlock the vault after server restart
- Lock the vault
- Check vault status
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from backend_v2.services.vault import vault, VaultError, VaultNotInitializedError, VaultLockedError
    from backend_v2.services.user_vault import get_user_vault
    from backend_v2.services.reencryption_service import reencrypt_all_user_data
    from backend_v2.routers.documents import get_current_user
    from backend_v2.models import User
    from backend_v2.database import get_db
    from backend_v2.auth.rate_limiter import check_vault_unlock_rate_limit, reset_vault_unlock_rate_limit
except ImportError:
    from services.vault import vault, VaultError, VaultNotInitializedError, VaultLockedError
    from services.user_vault import get_user_vault
    from services.reencryption_service import reencrypt_all_user_data
    from routers.documents import get_current_user
    from models import User
    from database import get_db
    from auth.rate_limiter import check_vault_unlock_rate_limit, reset_vault_unlock_rate_limit

router = APIRouter(prefix="/admin/vault", tags=["vault"])


class VaultPasswordRequest(BaseModel):
    master_password: str = Field(..., min_length=16, description="Master password (minimum 16 characters)")


class VaultStatusResponse(BaseModel):
    is_unlocked: bool
    is_configured: bool
    message: str


class VaultInitResponse(BaseModel):
    success: bool
    message: str


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require the current user to be an admin."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


class VaultReadyResponse(BaseModel):
    ready: bool


@router.get("/status")
async def get_vault_status_public() -> VaultReadyResponse:
    """
    Check if the system is ready for login.

    Returns minimal info - just whether the vault is ready.
    This endpoint is public (no auth required) so the frontend
    can show the unlock page when needed.
    """
    is_ready = vault.is_configured and vault.is_unlocked
    return VaultReadyResponse(ready=is_ready)


@router.get("/status/detailed", response_model=VaultStatusResponse)
async def get_vault_status_detailed(current_user: User = Depends(require_admin)):
    """
    Get detailed vault status. Requires admin authentication.

    Returns whether the vault is configured and unlocked with a descriptive message.
    """
    is_configured = vault.is_configured
    is_unlocked = vault.is_unlocked

    if not is_configured:
        message = "Vault not initialized. Please run initialization."
    elif not is_unlocked:
        message = "Vault is locked. Please unlock to access the system."
    else:
        message = "Vault is unlocked and operational."

    return VaultStatusResponse(
        is_unlocked=is_unlocked,
        is_configured=is_configured,
        message=message
    )


@router.post("/initialize", response_model=VaultInitResponse)
async def initialize_vault(request: VaultPasswordRequest):
    """
    Initialize the vault with a master password (first-time setup).

    This can only be done once. The master password must be at least 16 characters.
    After initialization, the vault is automatically unlocked.

    NOTE: This endpoint is intentionally public when vault is not configured,
    since authentication cannot work without the vault being initialized.
    Once configured, this endpoint will reject further initialization attempts.

    WARNING: If you forget the master password, all encrypted data becomes
    permanently inaccessible. There is no recovery mechanism.
    """
    if vault.is_configured:
        raise HTTPException(
            status_code=400,
            detail="Vault is already initialized. Use unlock endpoint instead."
        )

    try:
        vault.initialize(request.master_password)
        return VaultInitResponse(
            success=True,
            message="Vault initialized and unlocked successfully."
        )
    except VaultError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/unlock", response_model=VaultInitResponse)
async def unlock_vault(
    request: VaultPasswordRequest,
    http_request: Request,
    _: None = Depends(check_vault_unlock_rate_limit)
):
    """
    Unlock the vault with the master password.

    This must be called after every server restart to enable access
    to encrypted data. The frontend should show an unlock prompt
    when the vault is locked.

    Note: This endpoint does not require authentication since the
    system cannot verify users while the vault is locked.
    Rate limited to prevent brute force attacks on the master password.
    """
    if not vault.is_configured:
        raise HTTPException(
            status_code=400,
            detail="Vault not initialized. Please initialize first."
        )

    if vault.is_unlocked:
        return VaultInitResponse(
            success=True,
            message="Vault is already unlocked."
        )

    try:
        success = vault.unlock(request.master_password)
        if success:
            # Reset rate limit on successful unlock
            reset_vault_unlock_rate_limit(http_request)
            return VaultInitResponse(
                success=True,
                message="Vault unlocked successfully."
            )
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid master password."
            )
    except VaultNotInitializedError:
        raise HTTPException(
            status_code=400,
            detail="Vault not initialized. Please initialize first."
        )
    except VaultError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lock", response_model=VaultInitResponse)
async def lock_vault(current_user: User = Depends(require_admin)):
    """
    Lock the vault, clearing all encryption keys from memory.

    After locking, all encrypted data becomes inaccessible until
    the vault is unlocked again with the master password.

    Use this for maintenance or security purposes.
    """
    vault.lock()
    return VaultInitResponse(
        success=True,
        message="Vault locked. All encryption keys cleared from memory."
    )


class ReencryptRequest(BaseModel):
    user_id: int = Field(..., description="User ID to re-encrypt data for")
    delete_plaintext: bool = Field(True, description="Delete plaintext data after encryption")


@router.post("/reencrypt-user")
async def reencrypt_user_data(
    request: ReencryptRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Re-encrypt all data for a specific user from plaintext sources.

    This endpoint:
    1. Reads user's documents from unencrypted file_path
    2. Reads biomarkers from plaintext value columns
    3. Encrypts everything with the user's per-user vault
    4. Optionally deletes/clears plaintext data

    Prerequisites:
    - User must have a vault set up (vault_data in users table)
    - User's vault must be unlocked (they must be logged in)

    Use this when:
    - A user's data was encrypted with the wrong key
    - Migration failed and needs to be re-run
    """
    # Get the target user
    target_user = db.query(User).filter(User.id == request.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user has a vault
    if not target_user.vault_data:
        raise HTTPException(
            status_code=400,
            detail="User does not have a vault set up. They need to log in first."
        )

    # Get user's unlocked vault from session
    user_vault = get_user_vault(request.user_id)
    if not user_vault or not user_vault.is_unlocked:
        raise HTTPException(
            status_code=400,
            detail="User's vault is not unlocked. The user needs to be logged in."
        )

    # Run re-encryption
    stats = reencrypt_all_user_data(
        db=db,
        user=target_user,
        user_vault=user_vault,
        delete_plaintext=request.delete_plaintext
    )

    return {
        "success": stats.get("success", False),
        "stats": stats,
        "message": "Re-encryption completed" if stats.get("success") else "Re-encryption completed with errors"
    }
