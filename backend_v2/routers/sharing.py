from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import secrets
import json

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, HealthReport, SharedReport
    from backend_v2.routers.documents import get_current_user
    from backend_v2.services.vault_helper import get_vault_helper
except ImportError:
    from database import get_db
    from models import User, HealthReport, SharedReport
    from routers.documents import get_current_user
    from services.vault_helper import get_vault_helper


router = APIRouter(prefix="/sharing", tags=["sharing"])


class ShareRequest(BaseModel):
    report_ids: List[int] = []  # Empty = share latest general report
    expires_days: int = 7
    password: Optional[str] = None


class ShareAccessRequest(BaseModel):
    password: Optional[str] = None


@router.post("/create")
def create_share_link(
    req: ShareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a shareable link for health reports."""
    # If no report IDs specified, use latest general report
    if not req.report_ids:
        latest = db.query(HealthReport).filter(
            HealthReport.user_id == current_user.id,
            HealthReport.report_type == "general"
        ).order_by(HealthReport.created_at.desc()).first()

        if not latest:
            raise HTTPException(status_code=404, detail="No health reports found")

        # Also get all specialist reports from the same session
        reports = db.query(HealthReport).filter(
            HealthReport.user_id == current_user.id,
            HealthReport.created_at >= latest.created_at - timedelta(minutes=5),
            HealthReport.created_at <= latest.created_at + timedelta(minutes=5)
        ).all()
        req.report_ids = [r.id for r in reports]
    else:
        # Verify all reports belong to user
        for rid in req.report_ids:
            report = db.query(HealthReport).filter(
                HealthReport.id == rid,
                HealthReport.user_id == current_user.id
            ).first()
            if not report:
                raise HTTPException(status_code=404, detail=f"Report {rid} not found")

    # Generate unique token
    token = secrets.token_urlsafe(32)

    # Hash password if provided
    password_hash = None
    if req.password:
        from passlib.context import CryptContext
        pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password_hash = pwd_ctx.hash(req.password)

    expires_at = datetime.now(timezone.utc) + timedelta(days=req.expires_days)

    shared = SharedReport(
        user_id=current_user.id,
        token=token,
        report_ids=json.dumps(req.report_ids),
        password_hash=password_hash,
        expires_at=expires_at,
    )
    db.add(shared)
    db.commit()

    return {
        "token": token,
        "url": f"/shared/{token}",
        "expires_at": expires_at.isoformat(),
        "has_password": bool(password_hash),
        "report_count": len(req.report_ids)
    }


@router.get("/my-links")
def list_share_links(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's active share links."""
    links = db.query(SharedReport).filter(
        SharedReport.user_id == current_user.id,
        SharedReport.is_active == True
    ).order_by(SharedReport.created_at.desc()).all()

    return [{
        "id": link.id,
        "token": link.token,
        "url": f"/shared/{link.token}",
        "expires_at": link.expires_at.isoformat(),
        "view_count": link.view_count,
        "has_password": bool(link.password_hash),
        "created_at": link.created_at.isoformat(),
        "is_expired": link.expires_at < datetime.now(timezone.utc)
    } for link in links]


@router.delete("/{share_id}")
def revoke_share_link(
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke a share link."""
    link = db.query(SharedReport).filter(
        SharedReport.id == share_id,
        SharedReport.user_id == current_user.id
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Share link not found")

    link.is_active = False
    db.commit()

    return {"message": "Link revoked"}


@router.post("/view/{token}")
def view_shared_report(
    token: str,
    req: ShareAccessRequest = ShareAccessRequest(),
    db: Session = Depends(get_db)
):
    """View a shared report (public - no auth required)."""
    shared = db.query(SharedReport).filter(
        SharedReport.token == token,
        SharedReport.is_active == True
    ).first()

    if not shared:
        raise HTTPException(status_code=404, detail="Share link not found or expired")

    # Check expiry
    if shared.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="This share link has expired")

    # Check max views
    if shared.view_count >= shared.max_views:
        raise HTTPException(status_code=410, detail="This share link has reached its view limit")

    # Check password
    if shared.password_hash:
        if not req.password:
            return {"requires_password": True}

        from passlib.context import CryptContext
        pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        if not pwd_ctx.verify(req.password, shared.password_hash):
            raise HTTPException(status_code=401, detail="Incorrect password")

    # Get reports
    report_ids = json.loads(shared.report_ids)
    reports = db.query(HealthReport).filter(
        HealthReport.id.in_(report_ids)
    ).all()

    # Decrypt report content
    vault_helper = get_vault_helper(shared.user_id)

    result = []
    for report in reports:
        content = {}
        if vault_helper.is_available and report.content_enc:
            try:
                content = json.loads(vault_helper.decrypt_data(report.content_enc))
            except Exception:
                content = {"summary": "Content unavailable", "findings": "", "recommendations": ""}
        else:
            content = {
                "summary": report.summary or "",
                "findings": report.findings or "",
                "recommendations": report.recommendations or ""
            }

        result.append({
            "report_type": report.report_type,
            "title": report.title,
            "content": content,
            "risk_level": report.risk_level,
            "biomarkers_analyzed": report.biomarkers_analyzed,
            "created_at": report.created_at.isoformat()
        })

    # Increment view count
    shared.view_count += 1
    db.commit()

    return {
        "reports": result,
        "view_count": shared.view_count,
        "expires_at": shared.expires_at.isoformat()
    }
