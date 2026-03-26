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

## WRITING STYLE
- Warm, conversational Romanian (tu form, not dumneavoastră)
- Click-worthy titles that deliver real value (not empty clickbait)
- 1500-2500 words per article (LONG-FORM, in-depth)
- Practical, actionable advice with specific numbers and examples
- Reference Romanian context: foods (ciorbă, sarmale, mici, cozonac), stores (Mega Image, Kaufland, piața), Romanian habits and culture

## ARTICLE STRUCTURE (MANDATORY)
Every article MUST follow this rich structure:

1. **Opening hook** — a compelling first paragraph that makes the reader want to continue. Use a surprising stat, a relatable scenario, or a provocative question.

2. **Context/Problem** — why this topic matters. Include a real statistic or data point.

3. **Main content** — 3-5 substantial sections, each with:
   - An H2 heading (descriptive, keyword-rich)
   - 2-4 paragraphs of detailed content
   - At least one visual element (see HTML ELEMENTS below)

4. **Key takeaway box** — a summary of the most important points

5. **CTA paragraph** — naturally leading to Analize.Online

## HTML ELEMENTS (USE THESE for rich visual articles)

Use these HTML patterns to create visually rich articles. Use ALL of them across the article:

**Highlighted info box (blue):**
<div style="background: linear-gradient(135deg, #eff6ff, #dbeafe); border-left: 4px solid #3b82f6; border-radius: 12px; padding: 20px; margin: 24px 0;">
<p style="font-weight: 700; color: #1e40af; margin-bottom: 8px;">💡 Știai că...</p>
<p style="color: #1e3a5f; margin: 0;">Content here</p>
</div>

**Warning/important box (amber):**
<div style="background: linear-gradient(135deg, #fffbeb, #fef3c7); border-left: 4px solid #f59e0b; border-radius: 12px; padding: 20px; margin: 24px 0;">
<p style="font-weight: 700; color: #92400e; margin-bottom: 8px;">⚠️ Important</p>
<p style="color: #78350f; margin: 0;">Content here</p>
</div>

**Recipe/tip card (green):**
<div style="background: linear-gradient(135deg, #ecfdf5, #d1fae5); border: 1px solid #a7f3d0; border-radius: 16px; padding: 24px; margin: 24px 0;">
<p style="font-weight: 700; font-size: 18px; color: #065f46; margin-bottom: 12px;">🍽️ Recipe/Tip Title</p>
<p style="color: #064e3b;">Content here</p>
</div>

**Key stat/number highlight:**
<div style="text-align: center; padding: 32px; margin: 24px 0;">
<p style="font-size: 48px; font-weight: 800; color: #0d9488; margin: 0; line-height: 1;">72%</p>
<p style="color: #64748b; font-size: 16px; margin-top: 8px;">din românii adulți nu-și verifică colesterolul anual</p>
</div>

**Comparison table:**
<div style="overflow-x: auto; margin: 24px 0;">
<table style="width: 100%; border-collapse: collapse; border-radius: 12px; overflow: hidden;">
<thead><tr style="background: #0f172a; color: white;">
<th style="padding: 12px 16px; text-align: left;">Column</th>
</tr></thead>
<tbody><tr style="border-bottom: 1px solid #e2e8f0;">
<td style="padding: 12px 16px;">Data</td>
</tr></tbody>
</table>
</div>

**Image with Unsplash (MANDATORY — include 2-3 per article):**
<figure style="margin: 32px 0;">
<img src="https://images.unsplash.com/photo-XXXXX?w=800&h=400&fit=crop&auto=format" alt="descriptive alt text" style="width: 100%; border-radius: 16px; object-fit: cover; max-height: 400px;" loading="lazy" />
<figcaption style="text-align: center; color: #94a3b8; font-size: 14px; margin-top: 8px;">Caption text</figcaption>
</figure>

Use REAL Unsplash photo IDs for the images. Pick from these based on topic:
- Health/medical: photo-1576091160399-112ba8d25d1d, photo-1559757148-5c350d0d3c56, photo-1579684385127-1ef15d508118
- Romanian food/cooking: photo-1556909114-f6e7ad7d3136, photo-1547592180-85f173990554, photo-1466637574441-749b8f19452f
- Vegetables/healthy food: photo-1512621776951-a57141f2eefd, photo-1498837167922-ddd27525d352, photo-1490645935967-10de6ba17061
- Fitness/exercise: photo-1517836357463-d25dfeac3438, photo-1571019614242-c5c5dee9f50b, photo-1534438327276-14e5300c3a48
- Lab/blood tests: photo-1579684385127-1ef15d508118, photo-1582719508461-905c673771fd, photo-1631549916768-4f7d9acf91c2
- Grocery/shopping: photo-1542838132-92c53300491e, photo-1604719312566-8912e9227c6a, photo-1488459716781-31db52582fe9

**Pull quote:**
<blockquote style="border-left: 4px solid #0d9488; background: #f0fdfa; padding: 20px 24px; border-radius: 0 12px 12px 0; margin: 24px 0; font-size: 18px; font-style: italic; color: #134e4a;">
"Quote text here"
</blockquote>

**Key takeaway box (at the end, before CTA):**
<div style="background: linear-gradient(135deg, #f0fdfa, #ccfbf1); border: 2px solid #14b8a6; border-radius: 16px; padding: 24px; margin: 32px 0;">
<p style="font-weight: 700; font-size: 18px; color: #0f766e; margin-bottom: 12px;">📋 Pe scurt</p>
<ul style="color: #115e59; margin: 0; padding-left: 20px;">
<li style="margin-bottom: 8px;">Point 1</li>
<li style="margin-bottom: 8px;">Point 2</li>
<li>Point 3</li>
</ul>
</div>

## PLATFORM FEATURES (weave 2-3 into each article naturally)
1. ALL LAB RESULTS IN ONE PLACE — connects to Regina Maria, Synevo, MedLife, Sanador
2. AI SPECIALIST DOCTORS — Cardiologist, Endocrinologist, Hematologist etc. give domain-specific analysis
3. REAL NUTRITION PLANS — 7-day meal plans based on YOUR blood work with Romanian recipes and exact portions
4. GROCERY SHOPPING LISTS — weekly list organized by category, ready for the store
5. EXERCISE PROGRAMS — 7-day workout plans adapted to your medical profile with progression
6. PER-USER ENCRYPTION — AES-256, even staff can't see your data

## SEO REQUIREMENTS
- Title: include primary keyword near the beginning, 50-65 chars
- H2 headings: include secondary keywords, descriptive (not vague like "Details")
- First paragraph: must contain the primary keyword naturally
- Internal link: include at least one `<a href="https://analize.online">Analize.Online</a>` or `<a href="https://analize.online/biomarker/SLUG">biomarker name</a>` link
- Meta description: 130-155 chars, includes primary keyword and a call to action
- Alt text on all images: descriptive, includes topic keywords

## OUTPUT FORMAT
Output ONLY valid JSON:
{
  "title": "Romanian title (keyword-rich, 50-65 chars)",
  "title_en": "English title",
  "slug": "url-slug-no-diacritics-max-6-words",
  "excerpt": "2-3 compelling Romanian sentences for the listing card",
  "excerpt_en": "English excerpt",
  "content_html": "RICH HTML article in Romanian with all visual elements described above. 1500-2500 words. Must include 2-3 images, info boxes, key takeaway, tables or recipe cards as appropriate.",
  "content_html_en": "Same quality English version",
  "meta_description": "SEO meta description Romanian 130-155 chars with keyword + CTA",
  "meta_description_en": "SEO meta description English 130-155 chars",
  "tags": "comma,separated,romanian,tags,3-5"
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

    # Get existing titles to avoid repetition
    existing_titles = [
        a.title for a in db.query(BlogArticle.title).order_by(BlogArticle.created_at.desc()).limit(10).all()
    ]
    titles_context = "\n".join(f"- {t}" for t in existing_titles) if existing_titles else "None yet"

    from datetime import date
    today = date.today()
    month_names_ro = ["", "ianuarie", "februarie", "martie", "aprilie", "mai", "iunie",
                      "iulie", "august", "septembrie", "octombrie", "noiembrie", "decembrie"]
    season_map = {12: "iarnă", 1: "iarnă", 2: "iarnă", 3: "primăvară", 4: "primăvară",
                  5: "primăvară", 6: "vară", 7: "vară", 8: "vară", 9: "toamnă",
                  10: "toamnă", 11: "toamnă"}

    user_prompt = f"""Write a rich, in-depth article about: {topic}
Category: {category}
Today: {today.strftime('%d %B %Y')} (month in Romanian: {month_names_ro[today.month]})
Season in Romania: {season_map.get(today.month, 'primăvară')}

Previously published titles (write something DIFFERENT):
{titles_context}

REMEMBER: Include 2-3 Unsplash images, info boxes, a key takeaway box, and make it visually rich. 1500-2500 words minimum."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=12000,
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
