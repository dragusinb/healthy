"""
Subscription management service.

Handles tier limits, quota enforcement, and usage tracking.
"""
from datetime import datetime, timezone
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session

try:
    from backend_v2.models import User, Subscription, UsageTracker, FamilyGroup, FamilyMember, Document, LinkedAccount
except ImportError:
    from models import User, Subscription, UsageTracker, FamilyGroup, FamilyMember, Document, LinkedAccount


# Tier limits configuration
TIER_LIMITS = {
    "free": {
        "max_providers": 2,
        "max_documents": 50,
        "ai_analyses_per_month": 3,
        "specialists": ["general"],  # Only general analysis
        "priority_sync": False,
        "pdf_export": False,
        "share_reports": False,
        "historical_comparison": False,
    },
    "premium": {
        "max_providers": 999,  # Unlimited
        "max_documents": 500,
        "ai_analyses_per_month": 30,
        "specialists": ["all"],
        "priority_sync": True,
        "pdf_export": True,
        "share_reports": True,
        "historical_comparison": True,
    },
    "family": {
        # Same as premium, per member
        "max_providers": 999,
        "max_documents": 500,
        "ai_analyses_per_month": 30,
        "specialists": ["all"],
        "priority_sync": True,
        "pdf_export": True,
        "share_reports": True,
        "historical_comparison": True,
        "max_family_members": 5,
    }
}

# Pricing in RON
PRICING = {
    "premium_monthly": 5,
    "premium_yearly": 40,
    "family_monthly": 10,
}


class SubscriptionService:
    """Service for managing subscriptions and enforcing quotas."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_subscription(self, user_id: int) -> Subscription:
        """Get user's subscription or create a free one."""
        subscription = self.db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()

        if not subscription:
            subscription = Subscription(
                user_id=user_id,
                tier="free",
                status="active"
            )
            self.db.add(subscription)
            self.db.commit()
            self.db.refresh(subscription)

        return subscription

    def get_or_create_usage_tracker(self, user_id: int) -> UsageTracker:
        """Get user's usage tracker or create one."""
        tracker = self.db.query(UsageTracker).filter(
            UsageTracker.user_id == user_id
        ).first()

        if not tracker:
            tracker = UsageTracker(
                user_id=user_id,
                month_start=datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            )
            self.db.add(tracker)
            self.db.commit()
            self.db.refresh(tracker)

        return tracker

    def get_user_tier(self, user_id: int) -> str:
        """Get user's current subscription tier."""
        subscription = self.get_or_create_subscription(user_id)

        # Check if user is part of a family plan
        family_member = self.db.query(FamilyMember).filter(
            FamilyMember.user_id == user_id
        ).first()

        if family_member:
            # Get family owner's subscription
            family = family_member.family
            owner_subscription = self.db.query(Subscription).filter(
                Subscription.user_id == family.owner_id
            ).first()
            if owner_subscription and owner_subscription.tier == "family" and owner_subscription.status == "active":
                return "family"

        return subscription.tier if subscription.status == "active" else "free"

    def get_tier_limits(self, tier: str) -> Dict[str, Any]:
        """Get limits for a tier."""
        return TIER_LIMITS.get(tier, TIER_LIMITS["free"]).copy()

    def get_user_limits(self, user_id: int) -> Dict[str, Any]:
        """Get effective limits for a user."""
        tier = self.get_user_tier(user_id)
        return self.get_tier_limits(tier)

    def check_can_add_provider(self, user_id: int) -> Tuple[bool, str]:
        """Check if user can add another provider."""
        limits = self.get_user_limits(user_id)
        current_count = self.db.query(LinkedAccount).filter(
            LinkedAccount.user_id == user_id
        ).count()

        if current_count >= limits["max_providers"]:
            tier = self.get_user_tier(user_id)
            if tier == "free":
                return False, "Ai atins limita de 2 provideri medicali. Upgradează la Premium pentru provideri nelimitați."
            return False, f"Ai atins limita de {limits['max_providers']} provideri."

        return True, ""

    def check_can_upload_document(self, user_id: int) -> Tuple[bool, str]:
        """Check if user can upload more documents."""
        limits = self.get_user_limits(user_id)
        current_count = self.db.query(Document).filter(
            Document.user_id == user_id
        ).count()

        if current_count >= limits["max_documents"]:
            tier = self.get_user_tier(user_id)
            if tier == "free":
                return False, f"Ai atins limita de {limits['max_documents']} documente. Upgradează la Premium pentru 500 documente."
            return False, f"Ai atins limita de {limits['max_documents']} documente."

        return True, ""

    def check_can_run_analysis(self, user_id: int, specialist_type: str = "general") -> Tuple[bool, str]:
        """Check if user can run an AI analysis."""
        limits = self.get_user_limits(user_id)
        tracker = self.get_or_create_usage_tracker(user_id)

        # Reset monthly counter if needed
        self._check_and_reset_monthly_usage(tracker)

        # Check specialist access
        if limits["specialists"] != ["all"] and specialist_type not in limits["specialists"]:
            return False, f"Analizele de specialitate ({specialist_type}) sunt disponibile doar în planul Premium."

        # Check monthly limit
        if tracker.ai_analyses_this_month >= limits["ai_analyses_per_month"]:
            tier = self.get_user_tier(user_id)
            if tier == "free":
                return False, f"Ai folosit toate cele {limits['ai_analyses_per_month']} analize AI din această lună. Upgradează la Premium pentru 30 analize/lună."
            return False, f"Ai atins limita de {limits['ai_analyses_per_month']} analize AI pentru această lună."

        return True, ""

    def check_feature_access(self, user_id: int, feature: str) -> Tuple[bool, str]:
        """Check if user has access to a feature."""
        limits = self.get_user_limits(user_id)

        feature_map = {
            "pdf_export": ("pdf_export", "Exportul PDF"),
            "share_reports": ("share_reports", "Partajarea rapoartelor cu medicii"),
            "historical_comparison": ("historical_comparison", "Comparația istorică a biomarkerilor"),
            "priority_sync": ("priority_sync", "Sincronizarea prioritară"),
        }

        if feature not in feature_map:
            return True, ""

        key, name = feature_map[feature]
        if not limits.get(key, False):
            return False, f"{name} este disponibilă doar în planul Premium."

        return True, ""

    def increment_ai_usage(self, user_id: int):
        """Increment AI analysis usage counter."""
        tracker = self.get_or_create_usage_tracker(user_id)
        self._check_and_reset_monthly_usage(tracker)

        tracker.ai_analyses_this_month += 1
        tracker.total_ai_analyses += 1
        self.db.commit()

    def increment_document_count(self, user_id: int):
        """Increment document upload counter."""
        tracker = self.get_or_create_usage_tracker(user_id)
        tracker.total_documents_uploaded += 1
        self.db.commit()

    def _check_and_reset_monthly_usage(self, tracker: UsageTracker):
        """Reset monthly usage if we're in a new month."""
        now = datetime.now(timezone.utc)
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if tracker.month_start < current_month_start:
            tracker.ai_analyses_this_month = 0
            tracker.month_start = current_month_start
            self.db.commit()

    def get_usage_stats(self, user_id: int) -> Dict[str, Any]:
        """Get current usage statistics for a user."""
        limits = self.get_user_limits(user_id)
        tracker = self.get_or_create_usage_tracker(user_id)
        self._check_and_reset_monthly_usage(tracker)

        # Get actual counts
        document_count = self.db.query(Document).filter(
            Document.user_id == user_id
        ).count()

        provider_count = self.db.query(LinkedAccount).filter(
            LinkedAccount.user_id == user_id
        ).count()

        return {
            "tier": self.get_user_tier(user_id),
            "limits": limits,
            "usage": {
                "documents": document_count,
                "documents_limit": limits["max_documents"],
                "documents_percent": min(100, int(document_count / limits["max_documents"] * 100)),
                "providers": provider_count,
                "providers_limit": limits["max_providers"],
                "providers_percent": min(100, int(provider_count / limits["max_providers"] * 100)) if limits["max_providers"] < 999 else 0,
                "ai_analyses_this_month": tracker.ai_analyses_this_month,
                "ai_analyses_limit": limits["ai_analyses_per_month"],
                "ai_analyses_percent": min(100, int(tracker.ai_analyses_this_month / limits["ai_analyses_per_month"] * 100)),
                "month_start": tracker.month_start.isoformat(),
            },
            "features": {
                "pdf_export": limits.get("pdf_export", False),
                "share_reports": limits.get("share_reports", False),
                "historical_comparison": limits.get("historical_comparison", False),
                "priority_sync": limits.get("priority_sync", False),
                "all_specialists": limits.get("specialists") == ["all"],
            },
            "lifetime_stats": {
                "total_ai_analyses": tracker.total_ai_analyses,
                "total_documents_uploaded": tracker.total_documents_uploaded,
            }
        }

    def upgrade_to_tier(self, user_id: int, tier: str, billing_cycle: str = "monthly",
                        stripe_customer_id: str = None, stripe_subscription_id: str = None,
                        stripe_price_id: str = None) -> Subscription:
        """Upgrade user to a new tier."""
        subscription = self.get_or_create_subscription(user_id)

        subscription.tier = tier
        subscription.billing_cycle = billing_cycle
        subscription.status = "active"
        subscription.stripe_customer_id = stripe_customer_id
        subscription.stripe_subscription_id = stripe_subscription_id
        subscription.stripe_price_id = stripe_price_id
        subscription.current_period_start = datetime.now(timezone.utc)

        # Set period end based on billing cycle
        if billing_cycle == "yearly":
            subscription.current_period_end = subscription.current_period_start + datetime.timedelta(days=365)
        else:
            subscription.current_period_end = subscription.current_period_start + datetime.timedelta(days=30)

        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def downgrade_to_free(self, user_id: int) -> Subscription:
        """Downgrade user to free tier."""
        subscription = self.get_or_create_subscription(user_id)

        subscription.tier = "free"
        subscription.status = "active"
        subscription.stripe_subscription_id = None
        subscription.stripe_price_id = None
        subscription.current_period_start = None
        subscription.current_period_end = None
        subscription.cancel_at_period_end = False

        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def cancel_subscription(self, user_id: int) -> Subscription:
        """Mark subscription to cancel at period end."""
        subscription = self.get_or_create_subscription(user_id)
        subscription.cancel_at_period_end = True
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def get_subscription_status(self, user_id: int) -> Dict[str, Any]:
        """Get full subscription status for display."""
        subscription = self.get_or_create_subscription(user_id)
        usage = self.get_usage_stats(user_id)

        return {
            "subscription": {
                "tier": subscription.tier,
                "status": subscription.status,
                "billing_cycle": subscription.billing_cycle,
                "current_period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
                "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                "cancel_at_period_end": subscription.cancel_at_period_end,
            },
            "usage": usage["usage"],
            "limits": usage["limits"],
            "features": usage["features"],
            "pricing": PRICING,
        }
