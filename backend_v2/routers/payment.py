"""
Payment webhook handling for Netopia IPN.
"""
import os
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import logging

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, Subscription, PaymentHistory
    from backend_v2.services.subscription_service import SubscriptionService, PRICING
    from backend_v2.services.netopia_service import get_netopia_service
    from backend_v2.routers.documents import get_current_user
except ImportError:
    from database import get_db
    from models import User, Subscription, PaymentHistory
    from services.subscription_service import SubscriptionService, PRICING
    from services.netopia_service import get_netopia_service
    from routers.documents import get_current_user

# Check if we're in production mode (strict by default)
IS_PRODUCTION = os.getenv("ENVIRONMENT", "production") == "production"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payment", tags=["payment"])


@router.post("/ipn")
async def netopia_ipn(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Netopia Instant Payment Notification (IPN).

    This endpoint receives encrypted payment status updates from Netopia.
    """
    try:
        # Get form data
        form_data = await request.form()
        env_key = form_data.get("env_key", "")
        data = form_data.get("data", "")

        if not env_key or not data:
            logger.error("IPN received without env_key or data")
            return Response(
                content=get_netopia_service().create_ipn_response(1, 1, "Missing parameters"),
                media_type="application/xml"
            )

        # Decrypt and parse the IPN
        netopia = get_netopia_service()
        payment_data = netopia.decrypt_ipn(env_key, data)

        if "error" in payment_data:
            logger.error(f"IPN decryption error: {payment_data['error']}")
            return Response(
                content=netopia.create_ipn_response(2, 2, "Decryption failed"),
                media_type="application/xml"
            )

        logger.info(f"IPN received: order={payment_data.get('order_id')}, status={payment_data.get('status')}")

        # Extract payment info
        order_id = payment_data.get("order_id", "")
        status = payment_data.get("status", "unknown")
        user_id = payment_data.get("user_id")
        plan_type = payment_data.get("plan_type")

        if not user_id:
            logger.error(f"IPN missing user_id: {order_id}")
            return Response(
                content=netopia.create_ipn_response(3, 1, "Missing user_id"),
                media_type="application/xml"
            )

        # Process based on status
        try:
            user_id = int(user_id)
            subscription_service = SubscriptionService(db)

            if status in ["confirmed", "paid"]:
                # Payment successful - upgrade subscription
                tier = "premium"
                if plan_type == "family_monthly":
                    tier = "family"

                billing_cycle = "yearly" if plan_type == "premium_yearly" else "monthly"

                subscription_service.upgrade_to_tier(
                    user_id=user_id,
                    tier=tier,
                    billing_cycle=billing_cycle,
                    stripe_subscription_id=order_id  # Store order_id for reference
                )

                # Record payment history (skip if duplicate order_id)
                existing_payment = db.query(PaymentHistory).filter(
                    PaymentHistory.order_id == order_id
                ).first()
                if not existing_payment:
                    # Generate invoice number: ANZ-YYYY-NNNNN
                    year = datetime.now(timezone.utc).year
                    last_payment = db.query(PaymentHistory).order_by(
                        PaymentHistory.id.desc()
                    ).first()
                    next_seq = (last_payment.id + 1) if last_payment else 1
                    invoice_number = f"ANZ-{year}-{next_seq:05d}"

                    # Calculate period
                    now = datetime.now(timezone.utc)
                    if billing_cycle == "yearly":
                        period_end = now + timedelta(days=365)
                    else:
                        period_end = now + timedelta(days=30)

                    payment = PaymentHistory(
                        user_id=user_id,
                        order_id=order_id,
                        invoice_number=invoice_number,
                        plan_type=plan_type,
                        tier=tier,
                        amount=PRICING.get(plan_type, 0),
                        currency="RON",
                        status="confirmed",
                        paid_at=now,
                        period_start=now,
                        period_end=period_end,
                    )
                    db.add(payment)
                    db.commit()

                logger.info(f"Subscription upgraded: user={user_id}, tier={tier}, order={order_id}")

            elif status == "pending":
                # Payment pending - log but don't change subscription
                logger.info(f"Payment pending: user={user_id}, order={order_id}")

            elif status in ["canceled", "refunded"]:
                # Payment cancelled or refunded - downgrade to free
                subscription_service.downgrade_to_free(user_id)

                # Update payment history status
                existing_payment = db.query(PaymentHistory).filter(
                    PaymentHistory.order_id == order_id
                ).first()
                if existing_payment:
                    existing_payment.status = status
                    db.commit()

                logger.info(f"Subscription downgraded (payment {status}): user={user_id}, order={order_id}")

            # Return success response
            return Response(
                content=netopia.create_ipn_response(0),
                media_type="application/xml"
            )

        except Exception as e:
            logger.error(f"IPN processing error: {e}")
            return Response(
                content=netopia.create_ipn_response(4, 2, str(e)),
                media_type="application/xml"
            )

    except Exception as e:
        logger.error(f"IPN handler error: {e}")
        return Response(
            content=get_netopia_service().create_ipn_response(5, 2, "Internal error"),
            media_type="application/xml"
        )


@router.get("/verify/{order_id}")
def verify_payment(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify payment status by order ID.

    This is used by the frontend after redirect to check if payment was successful.
    Requires authentication to prevent order enumeration attacks.
    """
    # Look for subscription with this order_id - MUST belong to current user
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == order_id,
        Subscription.user_id == current_user.id  # Security: only show user's own orders
    ).first()

    if subscription and subscription.tier != "free" and subscription.status == "active":
        return {
            "status": "success",
            "tier": subscription.tier,
            "message": "Payment confirmed"
        }

    return {
        "status": "pending",
        "message": "Payment not yet confirmed or failed"
    }


@router.post("/simulate-success")
def simulate_payment_success(
    user_id: int,
    plan_type: str = "premium_monthly",
    db: Session = Depends(get_db)
):
    """
    Simulate a successful payment (for development/testing only).

    This endpoint is disabled by default - only available when ENVIRONMENT=development or ENVIRONMENT=test.
    """
    # Security: Only allow in explicit dev/test environments (deny by default)
    if IS_PRODUCTION:
        raise HTTPException(status_code=403, detail="Not available in production")

    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    subscription_service = SubscriptionService(db)

    tier = "premium"
    if plan_type == "family_monthly":
        tier = "family"

    billing_cycle = "yearly" if plan_type == "premium_yearly" else "monthly"

    subscription_service.upgrade_to_tier(
        user_id=user_id,
        tier=tier,
        billing_cycle=billing_cycle,
        stripe_subscription_id=f"test-{datetime.now(timezone.utc).timestamp()}"
    )

    return {
        "status": "success",
        "message": f"Simulated {tier} subscription for user {user_id}",
        "tier": tier,
        "billing_cycle": billing_cycle,
    }
