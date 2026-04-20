"""Automated social media posting service for Facebook Page."""
import os
import json
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
import openai

logger = logging.getLogger(__name__)

FB_GRAPH_URL = "https://graph.facebook.com/v25.0"

POST_TOPICS = [
    {
        "type": "educational",
        "prompt": "Write an educational post about ONE specific biomarker (e.g., vitamin D, ferritin, TSH, HbA1c, triglycerides). Share a surprising fact most people don't know, explain what high/low values actually mean in daily life, and name 2-3 Romanian foods that help. Keep it genuinely interesting — teach something new.",
    },
    {
        "type": "recipe",
        "prompt": "Share a healthy Romanian recipe that happens to be great for a specific health issue. Tell the story — why this combination of ingredients works, what biomarkers it helps, maybe a personal touch ('bunica knew this instinctively'). Name the dish, 3-4 key ingredients, and the health connection.",
    },
    {
        "type": "myth_busting",
        "prompt": "Bust a common Romanian nutrition/health myth with actual science. Pick something people believe strongly (e.g., 'eggs raise cholesterol', 'you need 8 glasses of water', 'fruit juice is healthy', 'margarine is better than butter'). Explain what blood tests actually show. Be respectful but clear.",
    },
    {
        "type": "meal_plan_example",
        "prompt": "Show what a day of eating looks like for someone with a specific blood test result (e.g., low iron + normal cholesterol, or high blood sugar). Breakfast, lunch, dinner — all Romanian dishes. Explain WHY each meal was chosen based on the biomarkers. Make it feel practical, not clinical.",
    },
    {
        "type": "exercise_tip",
        "prompt": "Share how a specific type of exercise actually changes your blood test results — with real science. Pick one (walking, swimming, strength training, yoga) and explain which biomarkers improve and by how much. Include a simple routine someone can start today.",
    },
    {
        "type": "seasonal",
        "prompt": "Write about what changes in our bodies during the current season in Romania — which vitamin levels drop, what seasonal Romanian foods can help, and what to watch for in blood tests. Make it timely and practical.",
    },
    {
        "type": "did_you_know",
        "prompt": "Share a fascinating 'did you know' fact about how food affects blood chemistry. Something counterintuitive or surprising — like how coffee affects liver enzymes, or how sleep affects glucose, or how stress changes your blood test results. Make it the kind of post people want to share.",
    },
]

SYSTEM_PROMPT = """You are writing Facebook posts for a Romanian health education page. The page is run by Analize.Online, but posts should NOT feel like ads.

Write Facebook posts in ROMANIAN. Rules:
- Focus 90% on teaching something genuinely interesting/useful. Only 10% (last line) can mention the tool.
- Conversational, warm, like a knowledgeable friend sharing health tips
- Under 250 words
- Emoji: 2-3 max, natural placement
- Include a surprising fact or counterintuitive insight that makes people stop scrolling
- The last line can casually mention "Mai multe pe analize.online/nutrition-preview" but NEVER as a hard sell
- Some posts can skip the CTA entirely — pure value is fine

NEVER use hashtags. NEVER use "Click aici". NEVER use salesy language like "Încearcă acum!", "Nu rata!", "Ofertă", "Gratuit!".
Write like a smart friend who happens to know a lot about nutrition, not like a brand.

Format: plain text only (no markdown, no headers, no bullet points with dashes). Use line breaks for readability."""


def _get_fb_config() -> dict:
    return {
        "app_id": os.getenv("FB_APP_ID", ""),
        "app_secret": os.getenv("FB_APP_SECRET", ""),
        "page_id": os.getenv("FB_PAGE_ID", ""),
        "page_token": os.getenv("FB_PAGE_TOKEN", ""),
    }


def _get_today_topic() -> dict:
    day_of_year = datetime.now(timezone.utc).timetuple().tm_yday
    return POST_TOPICS[day_of_year % len(POST_TOPICS)]


def generate_post_content() -> str:
    topic = _get_today_topic()

    today = datetime.now(timezone.utc)
    month_names_ro = ["", "ianuarie", "februarie", "martie", "aprilie", "mai", "iunie",
                      "iulie", "august", "septembrie", "octombrie", "noiembrie", "decembrie"]
    season = "primăvară" if today.month in (3, 4, 5) else "vară" if today.month in (6, 7, 8) else "toamnă" if today.month in (9, 10, 11) else "iarnă"

    user_prompt = f"""{topic['prompt']}

Context: Today is {today.strftime('%A')}, {today.day} {month_names_ro[today.month]} {today.year}. Season: {season}.
Post type: {topic['type']}

Write the post now. Plain text, Romanian language."""

    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=800,
        temperature=0.9,
    )

    return response.choices[0].message.content.strip()


def generate_post_image(topic_type: str, post_text: str) -> Optional[str]:
    """Generate an image for the post using DALL-E. Returns image URL or None."""
    image_prompts = {
        "educational": "A clean, modern flat illustration of a blood test vial next to fresh healthy foods (vegetables, fish, nuts) on a light background. Warm colors, minimal, no text.",
        "recipe": "A beautiful overhead photo-style illustration of a traditional Romanian healthy meal on a rustic wooden table. Warm lighting, appetizing, no text.",
        "myth_busting": "A clean illustration showing a magnifying glass over a food item revealing scientific molecules inside. Modern, educational feel, light background, no text.",
        "meal_plan_example": "A flat lay illustration of three healthy meals arranged neatly — breakfast bowl, lunch plate, dinner plate — with colorful fresh ingredients. Clean, modern, no text.",
        "exercise_tip": "A serene illustration of a person doing light exercise (walking/yoga) outdoors in a Romanian landscape with rolling green hills. Warm colors, peaceful, no text.",
        "seasonal": "A beautiful illustration of seasonal Romanian produce and foods arranged artfully — current season vegetables, fruits, herbs. Warm, natural colors, no text.",
        "did_you_know": "A creative illustration of a human body silhouette filled with colorful healthy foods, showing the connection between nutrition and health. Modern, clean, no text.",
    }

    prompt = image_prompts.get(topic_type, image_prompts["educational"])

    try:
        client = openai.OpenAI()
        response = client.images.generate(
            model="gpt-image-1",
            prompt=f"{prompt} Style: clean digital illustration, suitable for a health education Facebook page.",
            size="1024x1024",
            quality="low",
            n=1,
        )
        # gpt-image-1 returns base64 by default, upload to Facebook directly
        import base64
        import tempfile
        image_data = base64.b64decode(response.data[0].b64_json)
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(image_data)
        tmp.close()
        logger.info(f"Generated image for {topic_type} post: {tmp.name}")
        return tmp.name
    except Exception as e:
        logger.warning(f"Image generation failed, posting without image: {e}")
        return None


def publish_to_facebook(message: str, image_url: str = None, link: str = None) -> dict:
    config = _get_fb_config()
    if not config["page_token"] or not config["page_id"]:
        logger.error("Facebook credentials not configured")
        return {"error": "Facebook credentials not configured"}

    with httpx.Client(timeout=60) as client:
        if image_url and os.path.isfile(image_url):
            url = f"{FB_GRAPH_URL}/{config['page_id']}/photos"
            with open(image_url, "rb") as img_file:
                resp = client.post(url, data={
                    "message": message,
                    "access_token": config["page_token"],
                }, files={"source": ("post.png", img_file, "image/png")})
            try:
                os.unlink(image_url)
            except Exception:
                pass
        else:
            url = f"{FB_GRAPH_URL}/{config['page_id']}/feed"
            data = {
                "message": message,
                "access_token": config["page_token"],
            }
            if link:
                data["link"] = link
            resp = client.post(url, data=data)

    if resp.status_code == 200:
        data = resp.json()
        logger.info(f"Facebook post published: {data.get('id')}")
        return {"success": True, "post_id": data.get("id")}
    else:
        error = resp.json().get("error", {}).get("message", resp.text)
        logger.error(f"Facebook post failed: {error}")
        return {"error": error}


def generate_full_post() -> dict:
    """Generate post content + image. Returns dict with content, image_url, topic_type."""
    topic = _get_today_topic()
    content = generate_post_content()
    image_url = generate_post_image(topic["type"], content)
    return {
        "content": content,
        "image_url": image_url,
        "topic_type": topic["type"],
    }


def run_daily_social_post():
    """Scheduled job: generate and publish daily Facebook post."""
    config = _get_fb_config()
    if not config["page_token"]:
        logger.warning("Skipping daily social post — no FB_PAGE_TOKEN configured")
        return

    try:
        post = generate_full_post()
        result = publish_to_facebook(post["content"], image_url=post["image_url"])
        if result.get("success"):
            logger.info(f"Daily social post published successfully ({post['topic_type']})")
        else:
            logger.error(f"Daily social post failed: {result.get('error')}")
    except Exception as e:
        logger.error(f"Daily social post error: {e}")


def exchange_code_for_token(code: str, redirect_uri: str) -> dict:
    """Exchange OAuth code for long-lived page token."""
    config = _get_fb_config()

    with httpx.Client(timeout=30) as client:
        # Step 1: Exchange code for short-lived user token
        resp = client.get(f"{FB_GRAPH_URL}/oauth/access_token", params={
            "client_id": config["app_id"],
            "client_secret": config["app_secret"],
            "redirect_uri": redirect_uri,
            "code": code,
        })
        if resp.status_code != 200:
            return {"error": f"Token exchange failed: {resp.text}"}

        short_token = resp.json().get("access_token")

        # Step 2: Exchange for long-lived token (60 days)
        resp = client.get(f"{FB_GRAPH_URL}/oauth/access_token", params={
            "grant_type": "fb_exchange_token",
            "client_id": config["app_id"],
            "client_secret": config["app_secret"],
            "fb_exchange_token": short_token,
        })
        if resp.status_code != 200:
            return {"error": f"Long-lived token exchange failed: {resp.text}"}

        long_token = resp.json().get("access_token")

        # Step 3: Get page token (never expires if derived from long-lived user token)
        resp = client.get(f"{FB_GRAPH_URL}/me/accounts", params={
            "access_token": long_token,
        })
        if resp.status_code != 200:
            return {"error": f"Page token fetch failed: {resp.text}"}

        pages = resp.json().get("data", [])
        if not pages:
            return {"error": "No pages found. Make sure you granted page permissions."}

        page = pages[0]
        return {
            "page_id": page["id"],
            "page_name": page.get("name"),
            "page_token": page["access_token"],
            "user_token": long_token,
        }
