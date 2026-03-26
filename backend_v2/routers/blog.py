"""Blog API router for public SEO articles."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timezone
from typing import Optional

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
    db: Session = Depends(get_db),
):
    """Public: paginated list of published blog articles."""
    query = db.query(BlogArticle).filter(BlogArticle.status == "published")

    if tag:
        # Match tag in comma-separated tags field
        query = query.filter(BlogArticle.tags.ilike(f"%{tag}%"))

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
        "pages": (total + limit - 1) // limit if total > 0 else 0,
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

    return {"tags": [{"name": k, "count": v} for k, v in sorted(tag_counts.items(), key=lambda x: -x[1])]}


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
