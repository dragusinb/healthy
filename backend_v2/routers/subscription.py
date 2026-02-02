"""
Subscription management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os

try:
    from backend_v2.database import get_db
    from backend_v2.routers.documents import get_current_user
    from backend_v2.models import User, Subscription, UsageTracker, FamilyGroup, FamilyMember
    from backend_v2.services.subscription_service import SubscriptionService, TIER_LIMITS, PRICING
    from backend_v2.services.netopia_service import get_netopia_service
except ImportError:
    from database import get_db
    from routers.documents import get_current_user
    from models import User, Subscription, UsageTracker, FamilyGroup, FamilyMember
    from services.subscription_service import SubscriptionService, TIER_LIMITS, PRICING
    from services.netopia_service import get_netopia_service

router = APIRouter(prefix="/subscription", tags=["subscription"])

# App URLs
APP_URL = os.getenv("APP_URL", "https://analize.online")


class CheckoutRequest(BaseModel):
    plan_type: str  # premium_monthly, premium_yearly, family_monthly
    billing_info: Optional[dict] = None


class SubscriptionStatusResponse(BaseModel):
    tier: str
    status: str
    billing_cycle: Optional[str] = None
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False


class UsageResponse(BaseModel):
    documents: int
    documents_limit: int
    documents_percent: int
    providers: int
    providers_limit: int
    providers_percent: int
    ai_analyses_this_month: int
    ai_analyses_limit: int
    ai_analyses_percent: int
    month_start: str


class FeaturesResponse(BaseModel):
    pdf_export: bool
    share_reports: bool
    historical_comparison: bool
    priority_sync: bool
    all_specialists: bool


@router.get("/status")
def get_subscription_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current subscription status, usage, and features."""
    service = SubscriptionService(db)
    return service.get_subscription_status(current_user.id)


@router.get("/usage")
def get_usage_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current usage statistics."""
    service = SubscriptionService(db)
    return service.get_usage_stats(current_user.id)


@router.get("/plans")
def get_available_plans():
    """Get available subscription plans with pricing."""
    netopia = get_netopia_service()
    plans = netopia.get_all_plans()

    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "currency": "RON",
                "interval": None,
                "limits": TIER_LIMITS["free"],
                "features": {
                    "providers": "2 provideri medicali",
                    "documents": "50 documente",
                    "ai_analyses": "3 analize AI/luna",
                    "specialists": "Doar analiza generala",
                },
            },
            {
                "id": "premium_monthly",
                "name": "Premium Lunar",
                "price": plans["premium_monthly"]["amount"],
                "currency": plans["premium_monthly"]["currency"],
                "interval": "monthly",
                "limits": TIER_LIMITS["premium"],
                "features": {
                    "providers": "Provideri nelimitati",
                    "documents": "500 documente",
                    "ai_analyses": "30 analize AI/luna",
                    "specialists": "Toti specialistii AI",
                    "extras": ["Export PDF", "Partajare cu medici", "Comparatii istorice", "Sincronizare prioritara"],
                },
            },
            {
                "id": "premium_yearly",
                "name": "Premium Anual",
                "price": plans["premium_yearly"]["amount"],
                "currency": plans["premium_yearly"]["currency"],
                "interval": "yearly",
                "savings": "Economisesti 20 RON",
                "limits": TIER_LIMITS["premium"],
                "features": {
                    "providers": "Provideri nelimitati",
                    "documents": "500 documente",
                    "ai_analyses": "30 analize AI/luna",
                    "specialists": "Toti specialistii AI",
                    "extras": ["Export PDF", "Partajare cu medici", "Comparatii istorice", "Sincronizare prioritara"],
                },
            },
            {
                "id": "family_monthly",
                "name": "Family",
                "price": plans["family_monthly"]["amount"],
                "currency": plans["family_monthly"]["currency"],
                "interval": "monthly",
                "limits": TIER_LIMITS["family"],
                "features": {
                    "providers": "Provideri nelimitati per membru",
                    "documents": "500 documente per membru",
                    "ai_analyses": "30 analize AI/luna per membru",
                    "specialists": "Toti specialistii AI",
                    "members": "Pana la 5 membri",
                    "extras": ["Export PDF", "Partajare cu medici", "Comparatii istorice", "Sincronizare prioritara"],
                },
            },
        ],
        "pricing": PRICING,
    }


@router.post("/checkout")
def create_checkout(
    request: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a payment checkout session."""
    valid_plans = ["premium_monthly", "premium_yearly", "family_monthly"]
    if request.plan_type not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Invalid plan type. Must be one of: {valid_plans}")

    netopia = get_netopia_service()

    try:
        payment_data = netopia.create_payment_request(
            user_id=current_user.id,
            user_email=current_user.email,
            plan_type=request.plan_type,
            return_url=f"{APP_URL}/billing?payment=complete",
            confirm_url=f"{APP_URL}/api/payment/ipn",
            billing_info=request.billing_info
        )

        return {
            "status": "success",
            "payment_url": payment_data["url"],
            "env_key": payment_data["env_key"],
            "data": payment_data["data"],
            "order_id": payment_data["order_id"],
            "amount": payment_data["amount"],
            "currency": payment_data["currency"],
            "description": payment_data["description"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create checkout: {str(e)}")


@router.post("/cancel")
def cancel_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel subscription at end of current period."""
    service = SubscriptionService(db)
    subscription = service.get_or_create_subscription(current_user.id)

    if subscription.tier == "free":
        raise HTTPException(status_code=400, detail="No active subscription to cancel")

    service.cancel_subscription(current_user.id)

    return {
        "status": "success",
        "message": "Subscription will be cancelled at the end of the current billing period",
        "cancel_at_period_end": True,
        "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None
    }


@router.post("/reactivate")
def reactivate_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reactivate a cancelled subscription."""
    service = SubscriptionService(db)
    subscription = service.get_or_create_subscription(current_user.id)

    if not subscription.cancel_at_period_end:
        raise HTTPException(status_code=400, detail="Subscription is not pending cancellation")

    subscription.cancel_at_period_end = False
    db.commit()

    return {
        "status": "success",
        "message": "Subscription reactivated",
        "cancel_at_period_end": False
    }


# =============================================================================
# Family Plan Management
# =============================================================================

class FamilyInviteRequest(BaseModel):
    email: str


@router.get("/family")
def get_family_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get family group information."""
    service = SubscriptionService(db)
    tier = service.get_user_tier(current_user.id)

    # Check if user owns a family
    family = db.query(FamilyGroup).filter(FamilyGroup.owner_id == current_user.id).first()

    # Check if user is member of a family
    membership = db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).first()

    if not family and not membership:
        return {
            "has_family": False,
            "is_owner": False,
            "tier": tier,
        }

    if family:
        # User is owner
        members = []
        for m in family.members:
            members.append({
                "id": m.id,
                "user_id": m.user_id,
                "email": m.user.email if m.user else None,
                "role": m.role,
                "joined_at": m.joined_at.isoformat() if m.joined_at else None,
            })

        return {
            "has_family": True,
            "is_owner": True,
            "family_id": family.id,
            "name": family.name,
            "invite_code": family.invite_code,
            "members": members,
            "max_members": TIER_LIMITS["family"]["max_family_members"],
            "tier": tier,
        }

    else:
        # User is member
        return {
            "has_family": True,
            "is_owner": False,
            "family_id": membership.family_id,
            "name": membership.family.name if membership.family else None,
            "role": membership.role,
            "joined_at": membership.joined_at.isoformat() if membership.joined_at else None,
            "owner_email": membership.family.owner.email if membership.family and membership.family.owner else None,
            "tier": tier,
        }


@router.post("/family/create")
def create_family_group(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a family group (requires family subscription)."""
    service = SubscriptionService(db)
    subscription = service.get_or_create_subscription(current_user.id)

    if subscription.tier != "family":
        raise HTTPException(
            status_code=403,
            detail="Family subscription required to create a family group"
        )

    # Check if already owns a family
    existing = db.query(FamilyGroup).filter(FamilyGroup.owner_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already have a family group")

    # Generate invite code
    import secrets
    invite_code = secrets.token_urlsafe(8)

    family = FamilyGroup(
        owner_id=current_user.id,
        name=f"{current_user.email.split('@')[0]}'s Family",
        invite_code=invite_code
    )
    db.add(family)
    db.commit()
    db.refresh(family)

    # Add owner as a member
    owner_member = FamilyMember(
        family_id=family.id,
        user_id=current_user.id,
        role="owner"
    )
    db.add(owner_member)
    db.commit()

    return {
        "status": "success",
        "family_id": family.id,
        "name": family.name,
        "invite_code": invite_code,
    }


@router.post("/family/join/{invite_code}")
def join_family(
    invite_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Join a family group using invite code."""
    # Check if user is already in a family
    existing = db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You are already in a family group")

    # Find family by invite code
    family = db.query(FamilyGroup).filter(FamilyGroup.invite_code == invite_code).first()
    if not family:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    # Check member limit
    member_count = db.query(FamilyMember).filter(FamilyMember.family_id == family.id).count()
    max_members = TIER_LIMITS["family"]["max_family_members"]
    if member_count >= max_members:
        raise HTTPException(status_code=400, detail=f"Family group is full (max {max_members} members)")

    # Add user to family
    member = FamilyMember(
        family_id=family.id,
        user_id=current_user.id,
        role="member"
    )
    db.add(member)
    db.commit()

    return {
        "status": "success",
        "message": f"Joined {family.name}",
        "family_id": family.id,
    }


@router.post("/family/leave")
def leave_family(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Leave a family group."""
    membership = db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=400, detail="You are not in a family group")

    if membership.role == "owner":
        raise HTTPException(
            status_code=400,
            detail="Owners cannot leave. Transfer ownership or delete the family group."
        )

    db.delete(membership)
    db.commit()

    return {"status": "success", "message": "Left family group"}


@router.delete("/family/member/{member_id}")
def remove_family_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a member from family group (owner only)."""
    # Check if user owns a family
    family = db.query(FamilyGroup).filter(FamilyGroup.owner_id == current_user.id).first()
    if not family:
        raise HTTPException(status_code=403, detail="Only family owners can remove members")

    # Find member
    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.family_id == family.id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member.role == "owner":
        raise HTTPException(status_code=400, detail="Cannot remove the owner")

    db.delete(member)
    db.commit()

    return {"status": "success", "message": "Member removed"}
