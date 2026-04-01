"""Blog API router for public SEO articles."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timezone
from typing import Optional
import html as html_mod

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, BlogArticle
    from backend_v2.routers.documents import get_current_user
except ImportError:
    from database import get_db
    from models import User, BlogArticle
    from routers.documents import get_current_user

router = APIRouter(prefix="/blog", tags=["blog"])


@router.get("/articles")
def list_articles(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    tag: Optional[str] = None,
    biomarker: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Public: paginated list of published blog articles."""
    query = db.query(BlogArticle).filter(BlogArticle.status == "published")

    if tag:
        # Match tag in comma-separated tags field
        query = query.filter(BlogArticle.tags.ilike(f"%{tag}%"))

    if biomarker:
        # Search for biomarker name in tags, title, or content
        query = query.filter(
            (BlogArticle.tags.ilike(f"%{biomarker}%")) |
            (BlogArticle.title.ilike(f"%{biomarker}%")) |
            (BlogArticle.content_html.ilike(f"%{biomarker}%"))
        )

    total = query.count()
    articles = (
        query.order_by(desc(BlogArticle.published_at))
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "articles": [
            {
                "slug": a.slug,
                "title": a.title,
                "title_en": a.title_en,
                "excerpt": a.excerpt,
                "excerpt_en": a.excerpt_en,
                "tags": a.tags,
                "topic_category": a.topic_category,
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "meta_description": a.meta_description,
                "meta_description_en": a.meta_description_en,
            }
            for a in articles
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": page * limit < total,
    }


@router.get("/articles/{slug}")
def get_article(slug: str, db: Session = Depends(get_db)):
    """Public: full article by slug."""
    article = (
        db.query(BlogArticle)
        .filter(BlogArticle.slug == slug, BlogArticle.status == "published")
        .first()
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return {
        "slug": article.slug,
        "title": article.title,
        "title_en": article.title_en,
        "excerpt": article.excerpt,
        "excerpt_en": article.excerpt_en,
        "content_html": article.content_html,
        "content_html_en": article.content_html_en,
        "tags": article.tags,
        "topic_category": article.topic_category,
        "meta_description": article.meta_description,
        "meta_description_en": article.meta_description_en,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "created_at": article.created_at.isoformat() if article.created_at else None,
        "generated_by": article.generated_by,
    }


@router.get("/tags")
def list_tags(db: Session = Depends(get_db)):
    """Public: all tags with article counts."""
    articles = (
        db.query(BlogArticle.tags)
        .filter(BlogArticle.status == "published", BlogArticle.tags.isnot(None))
        .all()
    )

    tag_counts = {}
    for (tags_str,) in articles:
        if tags_str:
            for tag in tags_str.split(","):
                tag = tag.strip()
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return {"tags": [{"tag": k, "count": v} for k, v in sorted(tag_counts.items(), key=lambda x: -x[1])]}


@router.get("/feed.xml", include_in_schema=False)
def blog_rss_feed(db: Session = Depends(get_db)):
    """Public RSS 2.0 feed for blog articles."""
    articles = (
        db.query(BlogArticle)
        .filter(BlogArticle.status == "published")
        .order_by(desc(BlogArticle.published_at))
        .limit(50)
        .all()
    )

    base_url = "https://analize.online"
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    items = []
    for a in articles:
        pub_date = a.published_at.strftime("%a, %d %b %Y %H:%M:%S +0000") if a.published_at else now
        item_title = html_mod.escape(a.title or "")
        item_desc = html_mod.escape(a.meta_description or a.excerpt or "")
        link = f"{base_url}/blog/{a.slug}"
        items.append(
            f"    <item>\n"
            f"      <title>{item_title}</title>\n"
            f"      <link>{link}</link>\n"
            f"      <guid isPermaLink=\"true\">{link}</guid>\n"
            f"      <description>{item_desc}</description>\n"
            f"      <pubDate>{pub_date}</pubDate>\n"
            f"    </item>"
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        '  <channel>\n'
        f'    <title>Blog Sănătate — Analize.Online</title>\n'
        f'    <link>{base_url}/blog</link>\n'
        f'    <description>Articole despre sănătate, nutriție, rețete românești sănătoase, ghiduri biomarkeri și sfaturi de la specialiști AI.</description>\n'
        f'    <language>ro</language>\n'
        f'    <lastBuildDate>{now}</lastBuildDate>\n'
        f'    <atom:link href="{base_url}/blog/feed.xml" rel="self" type="application/rss+xml" />\n'
        + "\n".join(items) + "\n"
        '  </channel>\n'
        '</rss>\n'
    )

    return Response(content=xml, media_type="application/rss+xml; charset=utf-8")


def _require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require admin access."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.post("/articles/generate")
def generate_article(
    db: Session = Depends(get_db),
    admin: User = Depends(_require_admin),
):
    """Admin only: trigger immediate article generation."""
    try:
        from backend_v2.services.blog_generator import generate_blog_article
    except ImportError:
        from services.blog_generator import generate_blog_article

    article = generate_blog_article(db)
    return {
        "status": "ok",
        "article": {
            "slug": article.slug,
            "title": article.title,
            "topic_category": article.topic_category,
            "published_at": article.published_at.isoformat() if article.published_at else None,
        },
    }
