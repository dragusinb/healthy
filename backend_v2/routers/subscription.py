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
    from backend_v2.models import User, Subscription, UsageTracker, FamilyGroup, FamilyMember, Document, TestResult, HealthReport
    from backend_v2.services.subscription_service import SubscriptionService, TIER_LIMITS, PRICING
    from backend_v2.services.netopia_service import get_netopia_service
    from backend_v2.services.user_vault import get_user_vault
except ImportError:
    from database import get_db
    from routers.documents import get_current_user
    from models import User, Subscription, UsageTracker, FamilyGroup, FamilyMember, Document, TestResult, HealthReport
    from services.subscription_service import SubscriptionService, TIER_LIMITS, PRICING
    from services.netopia_service import get_netopia_service
    from services.user_vault import get_user_vault

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


# =============================================================================
# Family Data Sharing Endpoints
# =============================================================================

def verify_family_access(db: Session, current_user: User, target_user_id: int) -> User:
    """
    Verify that current_user has family access to target_user_id's data.
    Returns the target user if access is granted.
    """
    if current_user.id == target_user_id:
        return current_user

    # Get current user's family membership
    current_membership = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id
    ).first()

    if not current_membership:
        raise HTTPException(status_code=403, detail="You are not in a family group")

    # Check if target user is in the same family
    target_membership = db.query(FamilyMember).filter(
        FamilyMember.user_id == target_user_id,
        FamilyMember.family_id == current_membership.family_id
    ).first()

    if not target_membership:
        raise HTTPException(status_code=403, detail="User is not in your family group")

    # Get target user
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    return target_user


def get_biomarker_value_for_family(result: TestResult, target_user_id: int) -> dict:
    """
    Get biomarker value for family viewing.
    Returns value if available, or indicates if owner needs to be logged in.
    """
    value = None
    numeric_value = None
    values_available = False

    # Try plaintext values first
    if result.value is not None:
        value = result.value
        values_available = True
    if result.numeric_value is not None:
        numeric_value = result.numeric_value
        values_available = True

    # If no plaintext, try decrypting with owner's vault
    if not values_available and (result.value_enc or result.numeric_value_enc):
        user_vault = get_user_vault(target_user_id)
        if user_vault and user_vault.is_unlocked:
            try:
                if result.value_enc:
                    value = user_vault.decrypt_data(result.value_enc)
                    values_available = True
                if result.numeric_value_enc:
                    numeric_value = user_vault.decrypt_number(result.numeric_value_enc)
                    values_available = True
            except Exception:
                pass

    return {
        "value": value,
        "numeric_value": numeric_value,
        "values_available": values_available
    }


@router.get("/family/members-with-data")
def get_family_members_with_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of family members with their data summary.
    Shows document count, biomarker count, last activity.
    """
    # Get current user's family membership
    membership = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id
    ).first()

    if not membership:
        return {"members": [], "has_family": False}

    # Get all family members
    family_members = db.query(FamilyMember).filter(
        FamilyMember.family_id == membership.family_id
    ).all()

    members_data = []
    for member in family_members:
        user = member.user
        if not user:
            continue

        # Get document count
        doc_count = db.query(Document).filter(Document.user_id == user.id).count()

        # Get biomarker count
        doc_ids = [d.id for d in db.query(Document.id).filter(Document.user_id == user.id).all()]
        biomarker_count = 0
        if doc_ids:
            biomarker_count = db.query(TestResult).filter(TestResult.document_id.in_(doc_ids)).count()

        # Get last document date
        last_doc = db.query(Document).filter(
            Document.user_id == user.id
        ).order_by(Document.document_date.desc()).first()

        # Get alerts count (HIGH/LOW biomarkers)
        alerts_count = 0
        if doc_ids:
            alerts_count = db.query(TestResult).filter(
                TestResult.document_id.in_(doc_ids),
                TestResult.flags.in_(["HIGH", "LOW"])
            ).count()

        members_data.append({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": member.role,
            "is_current_user": user.id == current_user.id,
            "document_count": doc_count,
            "biomarker_count": biomarker_count,
            "alerts_count": alerts_count,
            "last_activity": last_doc.document_date.isoformat() if last_doc and last_doc.document_date else None,
            "vault_active": get_user_vault(user.id) is not None and get_user_vault(user.id).is_unlocked
        })

    return {
        "members": members_data,
        "has_family": True,
        "family_name": membership.family.name if membership.family else None
    }


@router.get("/family/members/{user_id}/biomarkers")
def get_family_member_biomarkers(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get biomarkers for a family member.
    Shows all biomarker metadata, values shown if owner's vault is active.
    """
    target_user = verify_family_access(db, current_user, user_id)

    # Get all documents for target user
    doc_ids = [d.id for d in db.query(Document.id).filter(Document.user_id == user_id).all()]

    if not doc_ids:
        return {"biomarkers": [], "values_available": True, "owner_name": target_user.full_name or target_user.email}

    # Get all biomarkers
    results = db.query(TestResult).join(Document).filter(
        TestResult.document_id.in_(doc_ids)
    ).order_by(Document.document_date.desc()).all()

    biomarkers = []
    any_values_available = True

    for result in results:
        value_data = get_biomarker_value_for_family(result, user_id)
        if not value_data["values_available"]:
            any_values_available = False

        biomarkers.append({
            "id": result.id,
            "test_name": result.test_name,
            "canonical_name": result.canonical_name,
            "value": value_data["value"],
            "numeric_value": value_data["numeric_value"],
            "unit": result.unit,
            "reference_range": result.reference_range,
            "flags": result.flags,
            "category": result.category,
            "document_date": result.document.document_date.isoformat() if result.document and result.document.document_date else None,
            "values_available": value_data["values_available"]
        })

    return {
        "biomarkers": biomarkers,
        "values_available": any_values_available,
        "owner_name": target_user.full_name or target_user.email,
        "owner_vault_active": get_user_vault(user_id) is not None and get_user_vault(user_id).is_unlocked
    }


@router.get("/family/members/{user_id}/biomarkers-grouped")
def get_family_member_biomarkers_grouped(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get biomarkers for a family member, grouped by category.
    Shows latest value for each biomarker.
    """
    target_user = verify_family_access(db, current_user, user_id)

    # Get all documents for target user, ordered by date
    documents = db.query(Document).filter(
        Document.user_id == user_id
    ).order_by(Document.document_date.desc()).all()

    doc_ids = [d.id for d in documents]

    if not doc_ids:
        return {"categories": [], "owner_name": target_user.full_name or target_user.email}

    # Get all biomarkers
    results = db.query(TestResult).filter(
        TestResult.document_id.in_(doc_ids)
    ).all()

    # Group by canonical_name, keeping only latest
    biomarker_map = {}
    for result in results:
        key = result.canonical_name or result.test_name
        if key not in biomarker_map:
            biomarker_map[key] = result
        else:
            # Keep the one with more recent document date
            existing_doc = db.query(Document).filter(Document.id == biomarker_map[key].document_id).first()
            current_doc = db.query(Document).filter(Document.id == result.document_id).first()
            if current_doc and existing_doc:
                if current_doc.document_date and existing_doc.document_date:
                    if current_doc.document_date > existing_doc.document_date:
                        biomarker_map[key] = result

    # Group by category
    categories = {}
    for name, result in biomarker_map.items():
        cat = result.category or "General"
        if cat not in categories:
            categories[cat] = []

        value_data = get_biomarker_value_for_family(result, user_id)

        categories[cat].append({
            "id": result.id,
            "test_name": result.test_name,
            "canonical_name": result.canonical_name,
            "value": value_data["value"],
            "numeric_value": value_data["numeric_value"],
            "unit": result.unit,
            "reference_range": result.reference_range,
            "flags": result.flags,
            "document_date": result.document.document_date.isoformat() if result.document and result.document.document_date else None,
            "values_available": value_data["values_available"]
        })

    # Sort categories and biomarkers
    result_categories = []
    for cat_name in sorted(categories.keys()):
        biomarkers = sorted(categories[cat_name], key=lambda x: x["test_name"])
        result_categories.append({
            "name": cat_name,
            "biomarkers": biomarkers,
            "alerts_count": sum(1 for b in biomarkers if b["flags"] in ["HIGH", "LOW"])
        })

    return {
        "categories": result_categories,
        "owner_name": target_user.full_name or target_user.email,
        "owner_vault_active": get_user_vault(user_id) is not None and get_user_vault(user_id).is_unlocked
    }


@router.get("/family/members/{user_id}/documents")
def get_family_member_documents(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get documents for a family member.
    Documents can be listed, but downloading requires owner's vault.
    """
    target_user = verify_family_access(db, current_user, user_id)

    documents = db.query(Document).filter(
        Document.user_id == user_id
    ).order_by(Document.document_date.desc()).all()

    docs_data = []
    for doc in documents:
        # Count biomarkers in document
        biomarker_count = db.query(TestResult).filter(TestResult.document_id == doc.id).count()
        alerts_count = db.query(TestResult).filter(
            TestResult.document_id == doc.id,
            TestResult.flags.in_(["HIGH", "LOW"])
        ).count()

        docs_data.append({
            "id": doc.id,
            "filename": doc.filename,
            "provider": doc.provider,
            "document_date": doc.document_date.isoformat() if doc.document_date else None,
            "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
            "is_processed": doc.is_processed,
            "biomarker_count": biomarker_count,
            "alerts_count": alerts_count,
            "can_download": doc.file_path is not None or (
                doc.encrypted_path is not None and
                get_user_vault(user_id) is not None and
                get_user_vault(user_id).is_unlocked
            )
        })

    return {
        "documents": docs_data,
        "owner_name": target_user.full_name or target_user.email,
        "owner_vault_active": get_user_vault(user_id) is not None and get_user_vault(user_id).is_unlocked
    }


@router.get("/family/members/{user_id}/reports")
def get_family_member_reports(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get health reports for a family member.
    """
    target_user = verify_family_access(db, current_user, user_id)

    reports = db.query(HealthReport).filter(
        HealthReport.user_id == user_id
    ).order_by(HealthReport.created_at.desc()).all()

    reports_data = []
    for report in reports:
        # Try to get report content
        summary = report.summary
        findings = report.findings
        recommendations = report.recommendations

        # If encrypted, try to decrypt with owner's vault
        if not summary and report.content_enc:
            user_vault = get_user_vault(user_id)
            if user_vault and user_vault.is_unlocked:
                try:
                    content = user_vault.decrypt_json(report.content_enc)
                    summary = content.get("summary")
                    findings = content.get("findings")
                    recommendations = content.get("recommendations")
                except Exception:
                    pass

        reports_data.append({
            "id": report.id,
            "report_type": report.report_type,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "summary": summary,
            "findings": findings,
            "recommendations": recommendations,
            "has_content": summary is not None
        })

    return {
        "reports": reports_data,
        "owner_name": target_user.full_name or target_user.email,
        "owner_vault_active": get_user_vault(user_id) is not None and get_user_vault(user_id).is_unlocked
    }


@router.get("/family/members/{user_id}/evolution/{biomarker_name}")
def get_family_member_biomarker_evolution(
    user_id: int,
    biomarker_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get evolution data for a specific biomarker for a family member.
    """
    from urllib.parse import unquote
    biomarker_name = unquote(biomarker_name)

    target_user = verify_family_access(db, current_user, user_id)

    # Get all documents for target user
    doc_ids = [d.id for d in db.query(Document.id).filter(Document.user_id == user_id).all()]

    if not doc_ids:
        return {"data": [], "biomarker_name": biomarker_name, "owner_name": target_user.full_name or target_user.email}

    # Get all results for this biomarker
    results = db.query(TestResult).join(Document).filter(
        TestResult.document_id.in_(doc_ids),
        (TestResult.canonical_name == biomarker_name) | (TestResult.test_name == biomarker_name)
    ).order_by(Document.document_date.asc()).all()

    evolution_data = []
    for result in results:
        value_data = get_biomarker_value_for_family(result, user_id)

        evolution_data.append({
            "date": result.document.document_date.isoformat() if result.document and result.document.document_date else None,
            "value": value_data["numeric_value"] or value_data["value"],
            "unit": result.unit,
            "reference_range": result.reference_range,
            "flags": result.flags,
            "values_available": value_data["values_available"]
        })

    return {
        "data": evolution_data,
        "biomarker_name": biomarker_name,
        "owner_name": target_user.full_name or target_user.email,
        "owner_vault_active": get_user_vault(user_id) is not None and get_user_vault(user_id).is_unlocked
    }


@router.get("/family/health-summary")
def get_family_health_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get health summary for all family members.
    Shows alerts and recent activity.
    """
    # Get current user's family membership
    membership = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id
    ).first()

    if not membership:
        return {"summary": [], "has_family": False}

    # Get all family members
    family_members = db.query(FamilyMember).filter(
        FamilyMember.family_id == membership.family_id
    ).all()

    summary = []
    for member in family_members:
        user = member.user
        if not user:
            continue

        # Get document IDs
        doc_ids = [d.id for d in db.query(Document.id).filter(Document.user_id == user.id).all()]

        # Get alerts (HIGH/LOW)
        alerts = []
        if doc_ids:
            alert_results = db.query(TestResult).join(Document).filter(
                TestResult.document_id.in_(doc_ids),
                TestResult.flags.in_(["HIGH", "LOW"])
            ).order_by(Document.document_date.desc()).limit(5).all()

            for result in alert_results:
                value_data = get_biomarker_value_for_family(result, user.id)
                alerts.append({
                    "test_name": result.canonical_name or result.test_name,
                    "value": value_data["value"],
                    "unit": result.unit,
                    "flags": result.flags,
                    "date": result.document.document_date.isoformat() if result.document and result.document.document_date else None,
                    "values_available": value_data["values_available"]
                })

        # Get latest report
        latest_report = db.query(HealthReport).filter(
            HealthReport.user_id == user.id
        ).order_by(HealthReport.created_at.desc()).first()

        summary.append({
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": member.role,
            "is_current_user": user.id == current_user.id,
            "alerts": alerts,
            "alerts_count": len(alerts),
            "latest_report_date": latest_report.created_at.isoformat() if latest_report else None,
            "latest_report_type": latest_report.report_type if latest_report else None,
            "vault_active": get_user_vault(user.id) is not None and get_user_vault(user.id).is_unlocked
        })

    return {
        "summary": summary,
        "has_family": True,
        "family_name": membership.family.name if membership.family else None
    }
