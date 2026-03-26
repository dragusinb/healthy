"""Blog article generator using OpenAI GPT-4o."""
import json
import os
import logging
from datetime import datetime, timezone
from openai import OpenAI

try:
    from backend_v2.models import BlogArticle
    from backend_v2.services.openai_tracker import track_openai_response, log_openai_call
except ImportError:
    from models import BlogArticle
    from services.openai_tracker import track_openai_response, log_openai_call

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the editorial voice of Analize.Online — Romania's first health data aggregation platform.

Your writing style:
- Warm, conversational Romanian (tu form, not dumneavoastră)
- Click-worthy titles that deliver real value (not empty clickbait)
- 800-1200 words per article
- Practical, actionable advice people can use today
- Reference specific Romanian context: foods (ciorbă, sarmale, mici, cozonac), stores (Mega Image, Kaufland, piața), habits
- Structure: Hook paragraph → Problem/Context → Main content with H2/H3 → CTA to platform

CRITICAL platform features to weave into articles naturally (don't force all in every article):
1. ALL LAB RESULTS IN ONE PLACE — connects to Regina Maria, Synevo, MedLife, Sanador automatically
2. AI SPECIALIST DOCTORS — not generic advice. Cardiologist, Endocrinologist, Hematologist etc. each give domain-specific analysis
3. REAL NUTRITION PLANS — 7-day meal plans based on YOUR actual blood work, not generic "eat healthy". Romanian recipes (ciorbă de legume, sarmale, tocăniță), with exact portions
4. GROCERY SHOPPING LISTS — the platform generates your weekly shopping list organized by category, ready for the store
5. EXERCISE PROGRAMS — 7-day workout plans adapted to your medical profile, with warm-up, main workout, cool-down, and 8-week progression
6. PER-USER ENCRYPTION — military-grade AES-256, even staff can't see your data

Output ONLY valid JSON with these fields:
{
  "title": "Romanian title (click-worthy but honest)",
  "title_en": "English title",
  "slug": "url-slug-no-diacritics",
  "excerpt": "2-3 sentence Romanian excerpt for listing page",
  "excerpt_en": "English excerpt",
  "content_html": "Full HTML article in Romanian. Use <h2>, <h3>, <p>, <ul>/<li>, <strong>, <em>. NO <h1>. Include a final CTA paragraph.",
  "content_html_en": "Full HTML article in English",
  "meta_description": "SEO meta description in Romanian, 120-155 chars",
  "meta_description_en": "SEO meta description in English, 120-155 chars",
  "tags": "comma,separated,tags,in,romanian"
}"""

TOPIC_CATEGORIES = [
    "aggregation",
    "ai_specialists",
    "fitness_nutrition",
    "romanian_recipes",
    "grocery_lists",
    "biomarker_deep_dive",
    "seasonal_health",
]

TOPIC_PROMPTS = {
    "aggregation": [
        "De ce ai nevoie de toate analizele într-un singur loc",
        "Cum pierzi informații vitale când ai analize la 3 laboratoare diferite",
        "Cum te ajută agregarea automată a analizelor medicale să-ți monitorizezi sănătatea",
        "Ce se întâmplă cu analizele tale după ce le uiți în sertar",
    ],
    "ai_specialists": [
        "Ce vede un cardiolog AI în analizele tale (și tu nu)",
        "Diferența dintre un raport generic și unul de specialist",
        "Cum un endocrinolog AI îți poate detecta probleme cu tiroida din analize",
        "De ce ai nevoie de mai mulți specialiști care să-ți analizeze sângele",
    ],
    "fitness_nutrition": [
        "Cum influențează colesterolul tău ce ar trebui să mănânci (concret)",
        "De ce planul alimentar de pe internet nu funcționează pentru tine",
        "Cum să-ți adaptezi antrenamentul în funcție de analizele de sânge",
        "Ce exerciții sunt indicate când ai fierul scăzut sau hemoglobina mică",
    ],
    "romanian_recipes": [
        "5 rețete românești care îți scad colesterolul (da, inclusiv ciorbă)",
        "Sarmale sănătoase: cum adaptezi rețeta bunicii pentru analizele tale",
        "Mâncare românească pentru diabet: ce poți mânca fără griji",
        "Ciorbă de legume terapeutică: rețeta care îți curăță ficatul",
    ],
    "grocery_lists": [
        "Lista de cumpărături pentru o săptămână de mâncare sănătoasă (sub 200 RON)",
        "Ce să cumperi de la Mega Image când ai fierul scăzut",
        "Cum să faci cumpărăturile săptămânale în funcție de analizele tale",
        "10 alimente de bază pe care ar trebui să le ai mereu în casă",
    ],
    "biomarker_deep_dive": [
        "Hemoglobina: ghidul complet pentru români",
        "Ce înseamnă cu adevărat colesterolul LDL crescut",
        "Glicemia și hemoglobina glicată: tot ce trebuie să știi",
        "Fierul seric vs. feritina: de ce contează ambele valori",
    ],
    "seasonal_health": [
        "Ce analize ar trebui să faci primăvara",
        "Vitamina D iarna: de ce 80% din români au deficit",
        "Cum să-ți pregătești imunitatea pentru sezonul rece",
        "Analizele de vară: ce biomarkeri contează când e cald",
    ],
}


def _pick_next_topic(db) -> tuple:
    """Pick the next topic category in rotation and a specific topic."""
    import random

    # Find the last generated article's category
    last_article = (
        db.query(BlogArticle)
        .filter(BlogArticle.generated_by == "ai")
        .order_by(BlogArticle.created_at.desc())
        .first()
    )

    if last_article and last_article.topic_category in TOPIC_CATEGORIES:
        last_idx = TOPIC_CATEGORIES.index(last_article.topic_category)
        next_idx = (last_idx + 1) % len(TOPIC_CATEGORIES)
    else:
        next_idx = 0

    category = TOPIC_CATEGORIES[next_idx]

    # Get existing article titles to avoid repeats
    existing_titles = {
        a.title
        for a in db.query(BlogArticle.title)
        .filter(BlogArticle.topic_category == category)
        .all()
    }

    # Pick a topic that hasn't been used yet
    available_topics = [
        t for t in TOPIC_PROMPTS.get(category, []) if t not in existing_titles
    ]

    if not available_topics:
        # All topics used, pick randomly
        available_topics = TOPIC_PROMPTS.get(category, [])

    topic = random.choice(available_topics) if available_topics else f"Write about {category}"

    return category, topic


def _ensure_unique_slug(db, slug: str) -> str:
    """Ensure slug is unique by appending a number if needed."""
    original_slug = slug
    counter = 1
    while db.query(BlogArticle).filter(BlogArticle.slug == slug).first():
        slug = f"{original_slug}-{counter}"
        counter += 1
    return slug


def generate_blog_article(db) -> BlogArticle:
    """Generate a blog article using OpenAI and save it to the database."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    client = OpenAI(api_key=api_key)
    model = "gpt-4o"

    category, topic = _pick_next_topic(db)
    logger.info(f"Generating blog article: category={category}, topic={topic}")

    user_prompt = f"Write an article about: {topic}\nCategory: {category}"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=4000,
        )

        track_openai_response(response, model=model, purpose="blog_generation")

        raw_content = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if raw_content.startswith("```"):
            # Remove first line (```json or ```) and last line (```)
            lines = raw_content.split("\n")
            raw_content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        data = json.loads(raw_content)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {e}\nRaw: {raw_content[:500]}")
        log_openai_call(model=model, purpose="blog_generation", success=False, error_message=f"JSON parse error: {e}")
        raise ValueError(f"OpenAI returned invalid JSON: {e}")
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        log_openai_call(model=model, purpose="blog_generation", success=False, error_message=str(e))
        raise

    # Ensure unique slug
    slug = _ensure_unique_slug(db, data.get("slug", "article"))

    now = datetime.now(timezone.utc)
    article = BlogArticle(
        slug=slug,
        title=data.get("title", topic),
        title_en=data.get("title_en"),
        excerpt=data.get("excerpt"),
        excerpt_en=data.get("excerpt_en"),
        content_html=data.get("content_html", ""),
        content_html_en=data.get("content_html_en"),
        meta_description=data.get("meta_description"),
        meta_description_en=data.get("meta_description_en"),
        tags=data.get("tags"),
        topic_category=category,
        status="published",
        published_at=now,
        generated_by="ai",
    )

    db.add(article)
    db.commit()
    db.refresh(article)

    logger.info(f"Blog article generated: slug={article.slug}, title={article.title}")
    return article


def scheduled_generate_article():
    """Entry point for the scheduler to generate an article."""
    try:
        from backend_v2.database import SessionLocal
    except ImportError:
        from database import SessionLocal

    db = SessionLocal()
    try:
        article = generate_blog_article(db)
        logger.info(f"Scheduled blog article generated: {article.slug}")
    except Exception as e:
        logger.error(f"Scheduled blog generation failed: {e}")
    finally:
        db.close()
