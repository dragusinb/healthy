"""Support ticket router for feedback button functionality."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import base64
import datetime
import logging

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, SupportTicket, SupportTicketReply, SupportTicketAttachment
    from backend_v2.routers.auth import oauth2_scheme
except ImportError:
    from database import get_db
    from models import User, SupportTicket, SupportTicketReply, SupportTicketAttachment
    from routers.auth import oauth2_scheme

router = APIRouter(prefix="/support", tags=["support"])


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current user from JWT token."""
    from jose import jwt
    try:
        from backend_v2.auth.security import SECRET_KEY, ALGORITHM
    except ImportError:
        from auth.security import SECRET_KEY, ALGORITHM

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_support_storage_path() -> str:
    """Get path to support ticket attachments storage."""
    path = "data/uploads/support"
    os.makedirs(path, exist_ok=True)
    return path


def generate_ticket_number(db: Session) -> str:
    """Generate a unique ticket number like TICK-001."""
    last_ticket = db.query(SupportTicket).order_by(SupportTicket.id.desc()).first()
    next_num = (last_ticket.id + 1) if last_ticket else 1
    return f"TICK-{next_num:04d}"


# Request/Response models
class SnapshotRequest(BaseModel):
    description: str
    page_url: str
    screenshot: Optional[str] = None  # Base64 encoded PNG


class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    subject: str
    description: str
    page_url: str
    type: str
    priority: str
    status: str
    ai_status: str
    ai_response: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    attachments_count: int

    class Config:
        from_attributes = True


class TicketDetailResponse(BaseModel):
    id: int
    ticket_number: str
    subject: str
    description: str
    page_url: str
    type: str
    priority: str
    status: str
    reporter_email: str
    reporter_name: Optional[str]
    ai_status: str
    ai_response: Optional[str]
    ai_fixed_at: Optional[datetime.datetime]
    resolved_at: Optional[datetime.datetime]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    attachments: List[dict]
    replies: List[dict]

    class Config:
        from_attributes = True


class SnapshotResponse(BaseModel):
    success: bool
    ticket_number: str
    message: str


class AdminTicketResponse(BaseModel):
    id: int
    ticket_number: str
    subject: str
    description: str
    page_url: str
    type: str
    priority: str
    status: str
    reporter_email: str
    reporter_name: Optional[str]
    ai_status: str
    ai_response: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    attachments_count: int

    class Config:
        from_attributes = True


class UpdateTicketStatusRequest(BaseModel):
    ai_status: str  # pending, processing, fixed, skipped, escalated
    ai_response: Optional[str] = None


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require the current user to be an admin."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.post("/snapshot", response_model=SnapshotResponse)
def create_snapshot_ticket(
    request: SnapshotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a support ticket with optional screenshot."""
    try:
        # Generate ticket number
        ticket_number = generate_ticket_number(db)

        # Create ticket
        ticket = SupportTicket(
            ticket_number=ticket_number,
            subject="Feedback",
            description=request.description,
            page_url=request.page_url,
            type="feedback",
            priority="normal",
            status="open",
            reporter_id=current_user.id,
            reporter_email=current_user.email,
            reporter_name=getattr(current_user, 'full_name', None),
            ai_status="pending"
        )
        db.add(ticket)
        db.flush()  # Get ticket.id

        # Handle screenshot if provided
        if request.screenshot:
            try:
                # Remove data URL prefix if present
                screenshot_data = request.screenshot
                if screenshot_data.startswith("data:"):
                    screenshot_data = screenshot_data.split(",", 1)[1]

                # Decode base64
                image_data = base64.b64decode(screenshot_data)

                # Create directory for ticket attachments
                ticket_dir = os.path.join(get_support_storage_path(), str(ticket.id))
                os.makedirs(ticket_dir, exist_ok=True)

                # Save screenshot
                screenshot_path = os.path.join(ticket_dir, "screenshot.png")
                with open(screenshot_path, "wb") as f:
                    f.write(image_data)

                # Create attachment record
                attachment = SupportTicketAttachment(
                    ticket_id=ticket.id,
                    file_name="screenshot.png",
                    file_path=screenshot_path,
                    file_type="image/png",
                    file_size=len(image_data),
                    uploaded_by_name=current_user.email
                )
                db.add(attachment)

            except Exception as e:
                logging.warning(f"Failed to save screenshot for ticket {ticket_number}: {e}")
                # Continue without screenshot

        db.commit()

        return SnapshotResponse(
            success=True,
            ticket_number=ticket_number,
            message="Feedback submitted successfully"
        )

    except Exception as e:
        db.rollback()
        logging.error(f"Failed to create support ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.get("/tickets", response_model=List[TicketResponse])
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List support tickets for the current user."""
    tickets = db.query(SupportTicket).filter(
        SupportTicket.reporter_id == current_user.id
    ).order_by(SupportTicket.created_at.desc()).all()

    result = []
    for ticket in tickets:
        result.append(TicketResponse(
            id=ticket.id,
            ticket_number=ticket.ticket_number,
            subject=ticket.subject,
            description=ticket.description,
            page_url=ticket.page_url,
            type=ticket.type,
            priority=ticket.priority,
            status=ticket.status,
            ai_status=ticket.ai_status,
            ai_response=ticket.ai_response,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            attachments_count=len(ticket.attachments)
        ))

    return result


@router.get("/tickets/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a support ticket."""
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.reporter_id == current_user.id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return TicketDetailResponse(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        subject=ticket.subject,
        description=ticket.description,
        page_url=ticket.page_url,
        type=ticket.type,
        priority=ticket.priority,
        status=ticket.status,
        reporter_email=ticket.reporter_email,
        reporter_name=ticket.reporter_name,
        ai_status=ticket.ai_status,
        ai_response=ticket.ai_response,
        ai_fixed_at=ticket.ai_fixed_at,
        resolved_at=ticket.resolved_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        attachments=[{
            "id": a.id,
            "file_name": a.file_name,
            "file_path": a.file_path,
            "file_type": a.file_type,
            "file_size": a.file_size,
            "created_at": a.created_at.isoformat() if a.created_at else None
        } for a in ticket.attachments],
        replies=[{
            "id": r.id,
            "message": r.message,
            "author_email": r.author_email,
            "author_name": r.author_name,
            "created_at": r.created_at.isoformat() if r.created_at else None
        } for r in ticket.replies]
    )


# ============================================================================
# Admin Endpoints
# ============================================================================

@router.get("/admin/tickets", response_model=List[AdminTicketResponse])
def list_all_tickets(
    status: Optional[str] = None,
    ai_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all support tickets (admin only)."""
    query = db.query(SupportTicket).order_by(SupportTicket.created_at.desc())

    if status:
        query = query.filter(SupportTicket.status == status)
    if ai_status:
        query = query.filter(SupportTicket.ai_status == ai_status)

    tickets = query.all()

    return [AdminTicketResponse(
        id=t.id,
        ticket_number=t.ticket_number,
        subject=t.subject,
        description=t.description,
        page_url=t.page_url,
        type=t.type,
        priority=t.priority,
        status=t.status,
        reporter_email=t.reporter_email,
        reporter_name=t.reporter_name,
        ai_status=t.ai_status,
        ai_response=t.ai_response,
        created_at=t.created_at,
        updated_at=t.updated_at,
        attachments_count=len(t.attachments)
    ) for t in tickets]


@router.get("/admin/tickets/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket_admin(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get detailed information about any ticket (admin only)."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return TicketDetailResponse(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        subject=ticket.subject,
        description=ticket.description,
        page_url=ticket.page_url,
        type=ticket.type,
        priority=ticket.priority,
        status=ticket.status,
        reporter_email=ticket.reporter_email,
        reporter_name=ticket.reporter_name,
        ai_status=ticket.ai_status,
        ai_response=ticket.ai_response,
        ai_fixed_at=ticket.ai_fixed_at,
        resolved_at=ticket.resolved_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        attachments=[{
            "id": a.id,
            "file_name": a.file_name,
            "file_path": a.file_path,
            "file_type": a.file_type,
            "file_size": a.file_size,
            "created_at": a.created_at.isoformat() if a.created_at else None
        } for a in ticket.attachments],
        replies=[{
            "id": r.id,
            "message": r.message,
            "author_email": r.author_email,
            "author_name": r.author_name,
            "created_at": r.created_at.isoformat() if r.created_at else None
        } for r in ticket.replies]
    )


@router.patch("/admin/tickets/{ticket_id}/status")
def update_ticket_status(
    ticket_id: int,
    request: UpdateTicketStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update ticket AI status (admin only)."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    valid_statuses = ["pending", "processing", "fixed", "skipped", "escalated"]
    if request.ai_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    ticket.ai_status = request.ai_status
    if request.ai_response:
        ticket.ai_response = request.ai_response

    if request.ai_status == "fixed":
        ticket.ai_fixed_at = datetime.datetime.utcnow()
        ticket.status = "resolved"
        ticket.resolved_at = datetime.datetime.utcnow()
    elif request.ai_status == "skipped":
        ticket.status = "closed"

    ticket.updated_at = datetime.datetime.utcnow()
    db.commit()

    return {"success": True, "message": f"Ticket status updated to {request.ai_status}"}
