"""
Vault API endpoints for managing the encryption vault.

These endpoints allow administrators to:
- Initialize the vault (first-time setup)
- Unlock the vault after server restart
- Lock the vault
- Check vault status
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

try:
    from backend_v2.services.vault import vault, VaultError, VaultNotInitializedError, VaultLockedError
    from backend_v2.routers.documents import get_current_user
    from backend_v2.models import User
except ImportError:
    from services.vault import vault, VaultError, VaultNotInitializedError, VaultLockedError
    from routers.documents import get_current_user
    from models import User

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


@router.get("/status", response_model=VaultStatusResponse)
async def get_vault_status():
    """
    Check the current status of the vault.

    Returns whether the vault is configured and unlocked.
    This endpoint is public (no auth required) so the frontend
    can show the unlock page when needed.
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
async def initialize_vault(
    request: VaultPasswordRequest,
    current_user: User = Depends(require_admin)
):
    """
    Initialize the vault with a master password (first-time setup).

    This can only be done once. The master password must be at least 16 characters.
    After initialization, the vault is automatically unlocked.

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
async def unlock_vault(request: VaultPasswordRequest):
    """
    Unlock the vault with the master password.

    This must be called after every server restart to enable access
    to encrypted data. The frontend should show an unlock prompt
    when the vault is locked.

    Note: This endpoint does not require authentication since the
    system cannot verify users while the vault is locked.
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
