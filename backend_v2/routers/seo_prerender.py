"""SEO dynamic rendering — inject proper meta tags for crawler bots.

Google recommends "dynamic rendering" for SPAs: detect bot user-agents and
serve HTML with real meta tags + content snippets so the page is indexable
without waiting for JS execution.

This router handles requests from Nginx for bot user-agents, reads the
frontend index.html, and injects route-specific meta tags + visible content.
"""
import os
import re
import json
import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

try:
    from backend_v2.database import get_db
    from backend_v2.models import BlogArticle
except ImportError:
    from database import get_db
    from models import BlogArticle

logger = logging.getLogger(__name__)
router = APIRouter(tags=["seo"])

BASE_URL = "https://analize.online"

# Load biomarker reference data once
_biomarkers: dict[str, dict] = {}
try:
    _json_path = os.path.normpath(os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend_v2", "src", "data", "biomarkers-reference.json"
    ))
    with open(_json_path, "r", encoding="utf-8") as f:
        for b in json.load(f):
            _biomarkers[b["slug"]] = b
    logger.info(f"SEO prerender: loaded {len(_biomarkers)} biomarkers")
except Exception as e:
    logger.warning(f"SEO prerender: could not load biomarkers: {e}")

# Static page meta (Romanian primary, English fallback)
STATIC_META = {
    "/": {
        "title": "Analize.Online — Toate analizele tale medicale într-un singur loc",
        "description": "Prima platformă din România care agregă analizele medicale de la Regina Maria, Synevo, MedLife și Sanador. Interpretare AI cu 6 specialiști virtuali. Criptare AES-256 per utilizator.",
    },
    "/pricing": {
        "title": "Prețuri — Analize.Online | De la 0 RON/lună",
        "description": "Planuri de abonament Analize.Online: Gratuit (1 furnizor, 2 analize AI/lună), Premium (29 RON/lună, furnizori nelimitați, 30 analize AI), Familie (49 RON/lună, până la 5 membri).",
    },
    "/blog": {
        "title": "Blog Sănătate — Sfaturi, rețete și ghiduri medicale | Analize.Online",
        "description": "Articole despre sănătate, nutriție, rețete românești sănătoase, ghiduri biomarkeri și sfaturi de la specialiști AI. Blog medical actualizat săptămânal.",
    },
    "/biomarker": {
        "title": "Ghid Biomarkeri — Valori normale și interpretare | Analize.Online",
        "description": "Ghid complet biomarkeri: hemoglobină, colesterol, glicemie, TGO, TGP, TSH și alții. Valori normale, interpretare rezultate, cauze valori crescute sau scăzute.",
    },
    "/analyzer": {
        "title": "Analizator Gratuit Analize Medicale | Analize.Online",
        "description": "Încarcă rezultatele analizelor tale medicale (text sau PDF) și primești interpretare AI gratuită. Fără cont necesar. Identifică valorile anormale instant.",
    },
    "/despre-noi": {
        "title": "Despre noi — Echipa Analize.Online",
        "description": "Află povestea Analize.Online: misiunea noastră, echipa din spate și viziunea pentru digitalizarea sănătății în România.",
    },
    "/contact": {
        "title": "Contact — Analize.Online",
        "description": "Contactează echipa Analize.Online pentru întrebări, sugestii sau parteneriate. Email: contact@analize.online.",
    },
    "/disclaimer-medical": {
        "title": "Disclaimer Medical — Analize.Online",
        "description": "Analize.Online oferă informații orientative, nu diagnostic medical. Consultă întotdeauna un medic specialist pentru interpretarea rezultatelor analizelor.",
    },
    "/terms": {
        "title": "Termeni și condiții — Analize.Online",
        "description": "Termeni și condiții de utilizare a platformei Analize.Online.",
    },
    "/privacy": {
        "title": "Politica de confidențialitate — Analize.Online",
        "description": "Politica de confidențialitate și protecția datelor personale pe Analize.Online. Conform GDPR.",
    },
    "/login": {
        "title": "Autentificare — Analize.Online",
        "description": "Conectează-te la contul tău Analize.Online pentru a vedea analizele medicale, biomarkerii și rapoartele AI de sănătate.",
    },
    "/demo": {
        "title": "Demo — Analize.Online",
        "description": "Vezi cum funcționează platforma Analize.Online. Demo interactiv cu date exemple.",
    },
}


def _get_index_html() -> str:
    """Read the built frontend index.html."""
    paths = [
        os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend_v2", "dist", "index.html")),
        "/opt/healthy/frontend_v2/dist/index.html",
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
    return ""


def _inject_meta(html: str, title: str, description: str, url: str, extra_head: str = "", body_content: str = "") -> str:
    """Replace meta tags in the HTML template."""
    # Replace title
    html = re.sub(r"<title>[^<]*</title>", f"<title>{_escape(title)}</title>", html)

    # Replace meta description
    html = re.sub(
        r'<meta name="description" content="[^"]*"',
        f'<meta name="description" content="{_escape(description)}"',
        html,
    )

    # Replace OG tags
    html = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{_escape(title)}"', html)
    html = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{_escape(description)}"', html)
    html = re.sub(r'<meta property="og:url" content="[^"]*"', f'<meta property="og:url" content="{_escape(url)}"', html)

    # Replace Twitter tags
    html = re.sub(r'<meta name="twitter:title" content="[^"]*"', f'<meta name="twitter:title" content="{_escape(title)}"', html)
    html = re.sub(r'<meta name="twitter:description" content="[^"]*"', f'<meta name="twitter:description" content="{_escape(description)}"', html)

    # Replace canonical
    html = re.sub(r'<link rel="canonical" href="[^"]*"', f'<link rel="canonical" href="{_escape(url)}"', html)

    # Inject extra head content (JSON-LD, etc.)
    if extra_head:
        html = html.replace("</head>", f"{extra_head}\n</head>")

    # Inject visible content for crawlers (inside root div)
    if body_content:
        html = html.replace('<div id="root"></div>', f'<div id="root">{body_content}</div>')

    return html


def _escape(s: str) -> str:
    """Escape HTML special chars for attribute values."""
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


@router.get("/prerender/{path:path}", include_in_schema=False)
def prerender_page(path: str, db: Session = Depends(get_db)):
    """Serve pre-rendered HTML with proper meta tags for search engine crawlers.

    Called by Nginx when it detects a bot user-agent.
    """
    html = _get_index_html()
    if not html:
        return HTMLResponse(content="<html><body>Page not found</body></html>", status_code=404)

    clean_path = f"/{path}" if path else "/"
    url = f"{BASE_URL}{clean_path}" if clean_path != "/" else BASE_URL

    # Blog article
    if clean_path.startswith("/blog/") and len(clean_path) > 6:
        slug = clean_path[6:]
        article = db.query(BlogArticle).filter(
            BlogArticle.slug == slug, BlogArticle.status == "published"
        ).first()
        if article:
            title = f"{article.title} | Analize.Online"
            desc = article.meta_description or article.excerpt or ""
            json_ld = json.dumps({
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": article.title,
                "description": desc,
                "datePublished": article.published_at.isoformat() if article.published_at else None,
                "url": url,
                "inLanguage": "ro",
                "publisher": {"@type": "Organization", "name": "Analize.Online", "url": BASE_URL},
                "author": {"@type": "Organization", "name": "Analize.Online"},
            }, ensure_ascii=False)
            extra = f'<script type="application/ld+json">{json_ld}</script>'
            # Inject article content for crawlers
            body = f'<article><h1>{_escape(article.title)}</h1><p>{_escape(desc)}</p>{article.content_html or ""}</article>'
            result = _inject_meta(html, title, desc, url, extra, body)
            return HTMLResponse(content=result)

    # Biomarker page
    if clean_path.startswith("/biomarker/") and len(clean_path) > 11:
        slug = clean_path[11:]
        bio = _biomarkers.get(slug)
        if bio:
            name = bio.get("name_ro", bio.get("name_en", slug))
            title = f"{name} — Valori normale, interpretare | Analize.Online"
            desc = f"Ghid complet {name}: valori normale, cauze valori crescute sau scăzute, ce măsoară, când se recomandă testarea. Verifică-ți rezultatele gratuit."
            json_ld = json.dumps({
                "@context": "https://schema.org",
                "@type": "MedicalWebPage",
                "name": name,
                "description": desc,
                "url": url,
                "inLanguage": "ro",
                "medicalAudience": {"@type": "MedicalAudience", "audienceType": "Patient"},
            }, ensure_ascii=False)
            extra = f'<script type="application/ld+json">{json_ld}</script>'
            category = bio.get("category", "")
            body = f'<article><h1>{_escape(name)}</h1><p>{_escape(desc)}</p><p>Categorie: {_escape(category)}</p></article>'
            result = _inject_meta(html, title, desc, url, extra, body)
            return HTMLResponse(content=result)

    # Static pages
    meta = STATIC_META.get(clean_path, STATIC_META.get("/"))
    title = meta["title"]
    desc = meta["description"]
    result = _inject_meta(html, title, desc, url)
    return HTMLResponse(content=result)
