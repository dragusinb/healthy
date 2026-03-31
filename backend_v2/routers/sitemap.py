"""Dynamic XML sitemap generator for analize.online."""
import json
import os
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

try:
    from backend_v2.database import get_db
    from backend_v2.models import BlogArticle
except ImportError:
    from database import get_db
    from models import BlogArticle

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sitemap"])

BASE_URL = "https://analize.online"

# Load biomarker slugs once at import time
_biomarker_slugs: list[str] = []
try:
    _json_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend_v2", "src", "data", "biomarkers-reference.json"
    )
    # Normalise for both Windows dev and Linux prod
    _json_path = os.path.normpath(_json_path)
    if not os.path.exists(_json_path):
        # Production layout: /opt/healthy/frontend_v2/...
        _json_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "frontend_v2", "src", "data", "biomarkers-reference.json"
        )
        _json_path = os.path.normpath(_json_path)
    with open(_json_path, "r", encoding="utf-8") as f:
        _biomarker_slugs = [b["slug"] for b in json.load(f)]
    logger.info(f"Sitemap: loaded {len(_biomarker_slugs)} biomarker slugs")
except Exception as e:
    logger.warning(f"Sitemap: could not load biomarkers-reference.json: {e}")


def _url_entry(loc: str, changefreq: str, priority: float, lastmod: str | None = None) -> str:
    parts = [f"  <url>", f"    <loc>{loc}</loc>"]
    if lastmod:
        parts.append(f"    <lastmod>{lastmod}</lastmod>")
    parts.append(f"    <changefreq>{changefreq}</changefreq>")
    parts.append(f"    <priority>{priority}</priority>")
    parts.append("  </url>")
    return "\n".join(parts)


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap_xml(db: Session = Depends(get_db)):
    """Generate a dynamic XML sitemap with all indexable pages."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    urls: list[str] = []

    # Static pages
    static_pages = [
        ("/", 1.0, "weekly"),
        ("/pricing", 0.9, "monthly"),
        ("/login", 0.7, "monthly"),
        ("/blog", 0.8, "weekly"),
        ("/biomarker", 0.8, "weekly"),
        ("/analyzer", 0.9, "weekly"),
        ("/despre-noi", 0.7, "monthly"),
        ("/contact", 0.7, "monthly"),
        ("/disclaimer-medical", 0.5, "yearly"),
        ("/demo", 0.7, "monthly"),
        ("/terms", 0.3, "yearly"),
        ("/privacy", 0.3, "yearly"),
    ]
    for path, priority, freq in static_pages:
        urls.append(_url_entry(f"{BASE_URL}{path}", freq, priority, today))

    # Biomarker pages
    for slug in _biomarker_slugs:
        urls.append(_url_entry(f"{BASE_URL}/biomarker/{slug}", "monthly", 0.7))

    # Blog articles from database
    try:
        articles = (
            db.query(BlogArticle.slug, BlogArticle.published_at)
            .filter(BlogArticle.status == "published")
            .all()
        )
        for article in articles:
            lastmod = None
            if article.published_at:
                lastmod = article.published_at.strftime("%Y-%m-%d")
            urls.append(_url_entry(f"{BASE_URL}/blog/{article.slug}", "weekly", 0.6, lastmod))
    except Exception as e:
        logger.warning(f"Sitemap: could not query blog articles: {e}")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "\n".join(urls)
    xml += "\n</urlset>\n"

    return Response(content=xml, media_type="application/xml")
