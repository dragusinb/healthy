"""
Referral program API endpoints.

"Invite a friend, both get 1 month free Premium"
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import secrets
import string

try:
    from backend_v2.database import get_db
    from backend_v2.routers.documents import get_current_user
    from backend_v2.models import User, Referral, Subscription
    from backend_v2.services.subscription_service import SubscriptionService
    from backend_v2.services.email_service import get_email_service
except ImportError:
    from database import get_db
    from routers.documents import get_current_user
    from models import User, Referral, Subscription
    from services.subscription_service import SubscriptionService
    from services.email_service import get_email_service

router = APIRouter(prefix="/referral", tags=["referral"])


def generate_referral_code() -> str:
    """Generate a short, readable referral code."""
    chars = string.ascii_uppercase + string.digits
    return "AO-" + "".join(secrets.choice(chars) for _ in range(6))


class InviteRequest(BaseModel):
    email: Optional[str] = None


class ReferralCodeRequest(BaseModel):
    referral_code: str


@router.get("/my-code")
def get_my_referral_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get or create the user's referral code."""
    # Check if user already has a referral code
    existing = db.query(Referral).filter(
        Referral.referrer_id == current_user.id,
        Referral.referred_id.is_(None),
        Referral.status == "pending"
    ).first()

    if existing:
        code = existing.referral_code
    else:
        # Create a new referral entry with a unique code
        code = generate_referral_code()
        while db.query(Referral).filter(Referral.referral_code == code).first():
            code = generate_referral_code()

        referral = Referral(
            referrer_id=current_user.id,
            referral_code=code,
            status="pending"
        )
        db.add(referral)
        db.commit()

    # Count stats
    total_invited = db.query(Referral).filter(
        Referral.referrer_id == current_user.id,
        Referral.status != "pending"
    ).count()

    total_rewarded = db.query(Referral).filter(
        Referral.referrer_id == current_user.id,
        Referral.referrer_rewarded == True
    ).count()

    return {
        "referral_code": code,
        "referral_url": f"https://analize.online/register?ref={code}",
        "stats": {
            "invited": total_invited,
            "rewarded": total_rewarded
        }
    }


@router.post("/send-invite")
def send_referral_invite(
    request: InviteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a referral invite email."""
    if not request.email:
        raise HTTPException(status_code=400, detail="Email is required")

    # Check if already invited
    existing = db.query(Referral).filter(
        Referral.referrer_id == current_user.id,
        Referral.referred_email == request.email
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="This email has already been invited")

    # Check if the email is already registered
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="This user is already registered")

    # Get or create referral code for this specific invite
    code = generate_referral_code()
    while db.query(Referral).filter(Referral.referral_code == code).first():
        code = generate_referral_code()

    referral = Referral(
        referrer_id=current_user.id,
        referral_code=code,
        referred_email=request.email,
        status="pending"
    )
    db.add(referral)
    db.commit()

    # Send invite email
    email_service = get_email_service()
    referral_url = f"https://analize.online/register?ref={code}"
    referrer_name = current_user.full_name or current_user.email.split("@")[0]
    language = current_user.language or "ro"

    if language == "ro":
        subject = f"{referrer_name} te invită pe Analize.Online - 1 lună Premium gratuită"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #0ea5e9, #06b6d4); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #f59e0b, #f97316); color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                .footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }}
                .benefit {{ padding: 8px 0; border-bottom: 1px solid #e2e8f0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin:0;">Analize.online</h1>
                    <p style="margin:5px 0 0 0; opacity:0.9;">Toate analizele tale medicale, într-un singur loc</p>
                </div>
                <div class="content">
                    <h2>Ai primit o invitație!</h2>
                    <p><strong>{referrer_name}</strong> te invită să te alături Analize.Online și primești <strong>1 lună de Premium gratuit</strong>!</p>
                    <h3>Ce primești cu Premium:</h3>
                    <div class="benefit">8+ specialiști AI (Cardiolog, Endocrinolog, etc.)</div>
                    <div class="benefit">30 analize AI pe lună</div>
                    <div class="benefit">Planuri de nutriție personalizate</div>
                    <div class="benefit">Export PDF pentru medici</div>
                    <div class="benefit">Sincronizare automată cu Regina Maria, Synevo</div>
                    <p style="text-align: center;">
                        <a href="{referral_url}" class="button">Creează cont gratuit</a>
                    </p>
                    <p style="color: #64748b; font-size: 14px; text-align: center;">Și tu, și {referrer_name} primiți 1 lună Premium gratuit!</p>
                </div>
                <div class="footer">
                    <p>Analize.online - Platforma de sănătate digitală</p>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        subject = f"{referrer_name} invites you to Analize.Online - 1 free month of Premium"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #0ea5e9, #06b6d4); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #f59e0b, #f97316); color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                .footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }}
                .benefit {{ padding: 8px 0; border-bottom: 1px solid #e2e8f0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin:0;">Analize.online</h1>
                    <p style="margin:5px 0 0 0; opacity:0.9;">All your medical tests in one place</p>
                </div>
                <div class="content">
                    <h2>You've been invited!</h2>
                    <p><strong>{referrer_name}</strong> invites you to join Analize.Online and get <strong>1 free month of Premium</strong>!</p>
                    <h3>What you get with Premium:</h3>
                    <div class="benefit">8+ AI specialists (Cardiologist, Endocrinologist, etc.)</div>
                    <div class="benefit">30 AI analyses per month</div>
                    <div class="benefit">Personalized nutrition plans</div>
                    <div class="benefit">PDF export for doctors</div>
                    <div class="benefit">Auto-sync with Regina Maria, Synevo</div>
                    <p style="text-align: center;">
                        <a href="{referral_url}" class="button">Create free account</a>
                    </p>
                    <p style="color: #64748b; font-size: 14px; text-align: center;">Both you and {referrer_name} get 1 free month of Premium!</p>
                </div>
                <div class="footer">
                    <p>Analize.online - Digital Health Platform</p>
                </div>
            </div>
        </body>
        </html>
        """

    email_service.send_email(request.email, subject, html_body)

    return {"message": "Invite sent", "referral_code": code}


@router.post("/apply")
def apply_referral_code(
    request: ReferralCodeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply a referral code for a newly registered user."""
    code = request.referral_code.strip().upper()

    # Find the referral
    referral = db.query(Referral).filter(
        Referral.referral_code == code
    ).first()

    if not referral:
        raise HTTPException(status_code=404, detail="Invalid referral code")

    if referral.referrer_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot use your own referral code")

    if referral.referred_id is not None:
        raise HTTPException(status_code=400, detail="This referral code has already been used")

    # Check if user already used a referral code
    already_referred = db.query(Referral).filter(
        Referral.referred_id == current_user.id
    ).first()
    if already_referred:
        raise HTTPException(status_code=400, detail="You have already used a referral code")

    # Apply referral
    referral.referred_id = current_user.id
    referral.status = "registered"
    referral.registered_at = datetime.now(timezone.utc)

    # Reward both users with 1 month premium
    now = datetime.now(timezone.utc)

    # Reward referred user (the new user)
    _apply_free_month(db, current_user.id, now)
    referral.referred_rewarded = True

    # Reward referrer
    _apply_free_month(db, referral.referrer_id, now)
    referral.referrer_rewarded = True

    referral.status = "rewarded"
    referral.rewarded_at = now

    db.commit()

    return {"message": "Referral applied! Both you and your friend get 1 month of Premium free."}


@router.get("/stats")
def get_referral_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get referral statistics for the current user."""
    referrals = db.query(Referral).filter(
        Referral.referrer_id == current_user.id
    ).all()

    total_sent = len([r for r in referrals if r.referred_email or r.status != "pending"])
    total_registered = len([r for r in referrals if r.status in ("registered", "rewarded")])
    total_rewarded = len([r for r in referrals if r.referrer_rewarded])
    free_months_earned = total_rewarded

    return {
        "total_sent": total_sent,
        "total_registered": total_registered,
        "total_rewarded": total_rewarded,
        "free_months_earned": free_months_earned,
        "referrals": [
            {
                "email": r.referred_email or (r.referred.email if r.referred else None),
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "registered_at": r.registered_at.isoformat() if r.registered_at else None,
                "rewarded": r.referrer_rewarded
            }
            for r in referrals if r.referred_email or r.referred_id
        ]
    }


def _apply_free_month(db: Session, user_id: int, now: datetime):
    """Give a user 1 free month of Premium."""
    sub_service = SubscriptionService(db)
    subscription = sub_service.get_or_create_subscription(user_id)

    if subscription.tier == "free":
        # Upgrade to premium for 1 month
        subscription.tier = "premium"
        subscription.billing_cycle = "monthly"
        subscription.status = "active"
        subscription.current_period_start = now
        subscription.current_period_end = now + timedelta(days=30)
        subscription.cancel_at_period_end = True  # Will auto-downgrade after 1 month
    elif subscription.tier in ("premium", "family"):
        # Extend existing subscription by 30 days
        if subscription.current_period_end:
            # Make timezone-aware if needed
            period_end = subscription.current_period_end
            if period_end.tzinfo is None:
                period_end = period_end.replace(tzinfo=timezone.utc)
            subscription.current_period_end = period_end + timedelta(days=30)
        else:
            subscription.current_period_end = now + timedelta(days=30)
