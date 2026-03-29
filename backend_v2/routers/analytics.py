"""Visitor analytics router — self-hosted page-view tracking."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, cast, Date, and_
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from typing import Optional
import hashlib
import re

try:
    from backend_v2.database import get_db
    from backend_v2.models import PageView, User
    from backend_v2.routers.documents import get_current_user
except ImportError:
    from database import get_db
    from models import PageView, User
    from routers.documents import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def require_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


_MOBILE_RE = re.compile(
    r"(android|iphone|ipod|ipad|mobile|opera mini|opera mobi|blackberry|"
    r"windows phone|iemobile|webos|symbian|palm|kindle|silk)",
    re.IGNORECASE,
)


def _is_mobile(ua: str) -> bool:
    if not ua:
        return False
    return bool(_MOBILE_RE.search(ua))


def _hash_ip(ip: str) -> str:
    """SHA-256 hash of the raw IP — never store the real address."""
    if not ip:
        return ""
    return hashlib.sha256(ip.encode()).hexdigest()


def _extract_domain(referrer: str) -> str:
    """Pull the bare domain from a referrer URL; empty → 'direct'."""
    if not referrer:
        return "direct"
    # Strip protocol
    ref = referrer.split("//", 1)[-1]
    # Strip path
    domain = ref.split("/", 1)[0].split("?", 1)[0].lower()
    # Strip www.
    if domain.startswith("www."):
        domain = domain[4:]
    # If it's our own domain, treat as direct
    if domain in ("analize.online", "localhost", "127.0.0.1"):
        return "direct"
    return domain or "direct"


def _period_to_delta(period: str) -> timedelta:
    mapping = {
        "today": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
    }
    return mapping.get(period, timedelta(days=7))


# In-memory rate-limit store (session_id -> list of timestamps)
# Kept simple; not shared across workers, but good enough for a single-process deploy.
_rate_buckets: dict[str, list[float]] = {}
_RATE_LIMIT = 100  # max pageviews per session per hour
_RATE_WINDOW = 3600  # seconds


def _check_rate_limit(session_id: str) -> bool:
    """Return True if the request is allowed."""
    import time

    now = time.time()
    bucket = _rate_buckets.get(session_id, [])

    # Purge old entries
    bucket = [t for t in bucket if now - t < _RATE_WINDOW]

    if len(bucket) >= _RATE_LIMIT:
        _rate_buckets[session_id] = bucket
        return False

    bucket.append(now)
    _rate_buckets[session_id] = bucket

    # Lazy cleanup: if too many sessions tracked, drop oldest half
    if len(_rate_buckets) > 10_000:
        keys = sorted(_rate_buckets, key=lambda k: _rate_buckets[k][-1] if _rate_buckets[k] else 0)
        for k in keys[: len(keys) // 2]:
            del _rate_buckets[k]

    return True


# ---------------------------------------------------------------------------
# Public tracking endpoint
# ---------------------------------------------------------------------------

class PageViewIn(BaseModel):
    page: str
    referrer: Optional[str] = None
    session_id: str
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    screen_width: Optional[int] = None


@router.post("/pageview", status_code=204)
def track_pageview(data: PageViewIn, request: Request, db: Session = Depends(get_db)):
    """Record a single page view. Fire-and-forget from the frontend."""
    if not data.session_id or not data.page:
        return Response(status_code=204)

    # Rate limit
    if not _check_rate_limit(data.session_id):
        return Response(status_code=204)  # silently drop

    ua = request.headers.get("user-agent", "")
    client_ip = request.headers.get("x-forwarded-for", "")
    if not client_ip and request.client:
        client_ip = request.client.host
    # x-forwarded-for may contain multiple IPs; take the first
    client_ip = client_ip.split(",")[0].strip() if client_ip else ""

    pv = PageView(
        session_id=data.session_id[:64],
        page=data.page[:500],
        referrer=data.referrer[:1000] if data.referrer else None,
        utm_source=data.utm_source[:200] if data.utm_source else None,
        utm_medium=data.utm_medium[:200] if data.utm_medium else None,
        utm_campaign=data.utm_campaign[:200] if data.utm_campaign else None,
        user_agent=ua[:500] if ua else None,
        ip_hash=_hash_ip(client_ip),
        screen_width=data.screen_width,
        is_mobile=_is_mobile(ua),
    )
    db.add(pv)
    db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Admin dashboard endpoints
# ---------------------------------------------------------------------------

# Funnel page sequence — order matters
FUNNEL_PAGES = [
    ("/", "home"),
    ("/pricing", "pricing"),
    ("/login", "login_page"),
    ("/register", "registered"),
    ("/dashboard", "dashboard"),
    ("/accounts", "linked_accounts"),
    ("/documents", "documents"),
    ("/health-reports", "health_reports"),
]


@router.get("/dashboard")
def analytics_dashboard(
    period: str = "7d",
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    delta = _period_to_delta(period)
    cutoff = datetime.now(timezone.utc) - delta

    # --- visitors ---
    # Use ip_hash for unique counting — it's stable across sessions/tabs/localStorage clears.
    # session_id (now persistent via localStorage) is used as fallback identifier.
    total_pv = db.query(func.count(PageView.id)).filter(PageView.created_at >= cutoff).scalar() or 0

    # Count unique visitors by ip_hash (most reliable), fall back to session_id for empty ip_hash
    unique_by_ip = db.query(func.count(distinct(PageView.ip_hash))).filter(
        PageView.created_at >= cutoff, PageView.ip_hash != "", PageView.ip_hash.isnot(None)
    ).scalar() or 0
    # Count sessions with no ip_hash (shouldn't happen, but be safe)
    unique_no_ip = db.query(func.count(distinct(PageView.session_id))).filter(
        PageView.created_at >= cutoff, ((PageView.ip_hash == "") | (PageView.ip_hash.is_(None)))
    ).scalar() or 0
    unique_sessions = unique_by_ip + unique_no_ip

    # Returning = ip_hashes with pageviews BOTH before and after cutoff
    returning_sessions = 0
    if unique_sessions:
        ips_before = db.query(PageView.ip_hash).filter(
            PageView.created_at < cutoff, PageView.ip_hash != "", PageView.ip_hash.isnot(None)
        ).distinct().subquery()
        returning_sessions = (
            db.query(func.count(distinct(PageView.ip_hash)))
            .filter(
                PageView.created_at >= cutoff,
                PageView.ip_hash != "",
                PageView.ip_hash.isnot(None),
                PageView.ip_hash.in_(ips_before.select()),
            )
            .scalar() or 0
        )

    # By day
    day_rows = (
        db.query(
            func.date(PageView.created_at).label("day"),
            func.count(PageView.id).label("pageviews"),
            func.count(distinct(PageView.ip_hash)).label("visitors"),
        )
        .filter(PageView.created_at >= cutoff, PageView.ip_hash != "", PageView.ip_hash.isnot(None))
        .group_by(func.date(PageView.created_at))
        .order_by(func.date(PageView.created_at))
        .all()
    )
    by_day = [{"date": str(r.day), "visitors": r.visitors, "pageviews": r.pageviews} for r in day_rows]

    # --- top pages ---
    page_rows = (
        db.query(
            PageView.page,
            func.count(PageView.id).label("views"),
            func.count(distinct(PageView.ip_hash)).label("unique"),
        )
        .filter(PageView.created_at >= cutoff)
        .group_by(PageView.page)
        .order_by(func.count(PageView.id).desc())
        .limit(20)
        .all()
    )
    top_pages = [{"page": r.page, "views": r.views, "unique": r.unique} for r in page_rows]

    # --- funnel ---
    funnel = {}
    for page_path, funnel_key in FUNNEL_PAGES:
        cnt = (
            db.query(func.count(distinct(PageView.ip_hash)))
            .filter(PageView.created_at >= cutoff, PageView.page.like(f"{page_path}%"))
            .scalar() or 0
        )
        funnel[funnel_key] = cnt

    # --- sources ---
    # We need to process referrers in Python (domain extraction)
    ref_rows = (
        db.query(PageView.referrer, func.count(distinct(PageView.ip_hash)).label("visitors"))
        .filter(PageView.created_at >= cutoff)
        .group_by(PageView.referrer)
        .all()
    )
    source_map: dict[str, int] = {}
    for r in ref_rows:
        domain = _extract_domain(r.referrer)
        source_map[domain] = source_map.get(domain, 0) + r.visitors
    sources = sorted(
        [{"source": k, "visitors": v} for k, v in source_map.items()],
        key=lambda x: x["visitors"],
        reverse=True,
    )

    # --- devices ---
    mobile_count = db.query(func.count(distinct(PageView.ip_hash))).filter(
        PageView.created_at >= cutoff, PageView.is_mobile == True,
        PageView.ip_hash != "", PageView.ip_hash.isnot(None)
    ).scalar() or 0
    desktop_count = max(0, unique_by_ip - mobile_count)

    return {
        "period": period,
        "visitors": {
            "total": total_pv,
            "unique": unique_sessions,
            "returning": returning_sessions,
            "by_day": by_day,
        },
        "top_pages": top_pages,
        "funnel": funnel,
        "sources": sources,
        "devices": {
            "mobile": mobile_count,
            "desktop": desktop_count,
        },
    }


@router.get("/live")
def analytics_live(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Return visitors active in the last 5 minutes."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    active = db.query(func.count(distinct(PageView.ip_hash))).filter(
        PageView.created_at >= cutoff, PageView.ip_hash != "", PageView.ip_hash.isnot(None)
    ).scalar() or 0
    pages = (
        db.query(PageView.page, func.count(PageView.id).label("views"))
        .filter(PageView.created_at >= cutoff)
        .group_by(PageView.page)
        .order_by(func.count(PageView.id).desc())
        .limit(10)
        .all()
    )
    return {
        "active_visitors": active,
        "pages": [{"page": r.page, "views": r.views} for r in pages],
    }
