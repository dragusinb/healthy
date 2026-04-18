"""Public lab results analyzer — no auth required, gated results."""
import hashlib
import logging
import time
from io import BytesIO
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

try:
    from backend_v2.database import get_db
    from backend_v2.services.ai_service import AIService
    from backend_v2.models import TestResult, Document, HealthReport, LeadCapture
except ImportError:
    from database import get_db
    from services.ai_service import AIService
    from models import TestResult, Document, HealthReport, LeadCapture

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analyzer"])

FREE_PREVIEW_COUNT = 5
MAX_ANALYSES_PER_IP_PER_DAY = 3
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

# ---------- In-memory rate limiter ----------
_rate_limits: dict[str, list[float]] = {}
_last_cleanup = time.time()

def _cleanup_rate_limits():
    global _last_cleanup
    now = time.time()
    if now - _last_cleanup < 3600:
        return
    cutoff = now - 86400
    to_delete = []
    for ip, timestamps in _rate_limits.items():
        _rate_limits[ip] = [t for t in timestamps if t > cutoff]
        if not _rate_limits[ip]:
            to_delete.append(ip)
    for ip in to_delete:
        del _rate_limits[ip]
    _last_cleanup = now

def _check_rate_limit(request: Request):
    _cleanup_rate_limits()
    ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
    now = time.time()
    cutoff = now - 86400
    hits = _rate_limits.get(ip_hash, [])
    hits = [t for t in hits if t > cutoff]
    if len(hits) >= MAX_ANALYSES_PER_IP_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail="Daily analysis limit reached. Create a free account for unlimited access.",
        )
    hits.append(now)
    _rate_limits[ip_hash] = hits


def _gate_results(results: list[dict], total: int) -> dict:
    """Return first FREE_PREVIEW_COUNT results in full, rest gated."""
    full = results[:FREE_PREVIEW_COUNT]
    gated = []
    for r in results[FREE_PREVIEW_COUNT:]:
        gated.append({
            "test_name": r.get("test_name", ""),
            "flags": r.get("flags", "NORMAL"),
        })
    return {
        "results": full,
        "gated_results": gated,
        "total_count": total,
        "preview_count": len(full),
        "gated_count": len(gated),
    }


def _save_lead(db: Session, email: Optional[str], source: str, request: Request):
    if not email:
        return
    ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()
    try:
        existing = db.query(LeadCapture).filter(LeadCapture.email == email).first()
        if not existing:
            lead = LeadCapture(email=email, source=source, ip_hash=ip_hash)
            db.add(lead)
            db.commit()
    except Exception as e:
        logger.warning(f"Lead capture failed: {e}")
        db.rollback()


# ---------- Endpoints ----------

class TextAnalysisRequest(BaseModel):
    text: str
    email: Optional[str] = None


@router.post("/analyzer/parse-text")
def analyze_text(
    body: TextAnalysisRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    _check_rate_limit(request)

    text = body.text.strip()
    if len(text) < 20:
        raise HTTPException(status_code=400, detail="Text too short to analyze.")

    ai = AIService()
    data = ai.parse_text_with_ai(text)

    if data.get("error"):
        raise HTTPException(status_code=422, detail=data["error"])

    results = data.get("results", [])
    metadata = data.get("metadata", {})

    _save_lead(db, body.email, "analyzer_text", request)

    return {
        "metadata": metadata,
        **_gate_results(results, len(results)),
        "message": f"Create a free account to see all {len(results)} biomarkers with AI specialist recommendations" if len(results) > FREE_PREVIEW_COUNT else None,
    }


@router.post("/analyzer/parse-pdf")
def analyze_pdf(
    request: Request,
    file: UploadFile = File(...),
    email: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    _check_rate_limit(request)

    # Validate extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Read content
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum 20 MB.")

    # Validate magic bytes
    if not content[:4] == b"%PDF":
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    # Extract text
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        ai = AIService()
        text = ai.extract_text_from_pdf(tmp_path)
        if not text or len(text.strip()) < 20:
            raise HTTPException(status_code=422, detail="Could not extract text from PDF.")
        data = ai.parse_text_with_ai(text)
    finally:
        os.unlink(tmp_path)

    if data.get("error"):
        raise HTTPException(status_code=422, detail=data["error"])

    results = data.get("results", [])
    metadata = data.get("metadata", {})

    _save_lead(db, email, "analyzer_pdf", request)

    return {
        "metadata": metadata,
        **_gate_results(results, len(results)),
        "message": f"Create a free account to see all {len(results)} biomarkers with AI specialist recommendations" if len(results) > FREE_PREVIEW_COUNT else None,
    }


# ---------- Nutrition Preview ----------
MAX_NUTRITION_PREVIEW_PER_IP_PER_DAY = 1
_nutrition_rate_limits: dict[str, list[float]] = {}
_nutrition_cache: dict[str, dict] = {}
_nutrition_cache_times: dict[str, float] = {}

def _check_nutrition_rate_limit(request: Request):
    _cleanup_rate_limits()
    ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
    now = time.time()
    cutoff = now - 86400
    hits = _nutrition_rate_limits.get(ip_hash, [])
    hits = [t for t in hits if t > cutoff]
    if len(hits) >= MAX_NUTRITION_PREVIEW_PER_IP_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail="You can generate 1 nutrition preview per day. Create a free account for weekly meal plans.",
        )
    hits.append(now)
    _nutrition_rate_limits[ip_hash] = hits


class NutritionPreviewRequest(BaseModel):
    text: str
    email: Optional[str] = None


NUTRITION_PREVIEW_SYSTEM_PROMPT = """You are an AI nutrition advisor creating a SHORT preview meal plan based on lab results.

Create a 3-day meal plan with Romanian cuisine, a shopping list, and 1 exercise day.

Respond in JSON with these fields:
- "biomarker_flags": array of {"name": string, "value": string, "status": "normal"|"high"|"low", "note": string} — top 5 most relevant biomarkers
- "meal_plan": array of 3 objects with "day" (e.g. "Ziua 1 — Luni"), "meals" array of 3 meals with "meal" (Mic dejun/Prânz/Cină), "time", "items" array, "calories", "notes"
- "shopping_list": array of {"category", "items" array}
- "exercise": object with "title" (e.g. "Program exerciții — Ziua 1"), "sections" array of {"name", "duration", "exercises" array of {"name", "sets": "3×15" or similar}}
- "summary": 2-3 sentences explaining why this plan was created for these specific biomarkers

RULES:
- Write ALL text in Romanian
- Use traditional Romanian dishes (ciorbă, sarmale, tocăniță, mămăligă, etc.)
- Include specific gram portions for every food item
- Shopping list should use Romanian product names
- Exercise program should be adapted to the biomarker findings
- Keep it concise — this is a preview, not a full plan"""


@router.post("/analyzer/nutrition-preview")
def nutrition_preview(
    body: NutritionPreviewRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    _check_nutrition_rate_limit(request)

    text = body.text.strip()
    if len(text) < 20:
        raise HTTPException(status_code=400, detail="Text too short to analyze.")

    text_hash = hashlib.sha256(text.encode()).hexdigest()[:32]
    now = time.time()
    if text_hash in _nutrition_cache and now - _nutrition_cache_times.get(text_hash, 0) < 86400:
        cached = _nutrition_cache[text_hash]
        _save_lead(db, body.email, "nutrition_preview", request)
        return cached

    ai = AIService()
    data = ai.parse_text_with_ai(text)

    if data.get("error"):
        raise HTTPException(status_code=422, detail=data["error"])

    results = data.get("results", [])
    if not results:
        raise HTTPException(status_code=422, detail="No biomarkers found in the text.")

    biomarker_text = "\n".join(
        f"- {r.get('test_name', '')}: {r.get('value', '')} {r.get('unit', '')} "
        f"(ref: {r.get('reference_range', 'N/A')}) [{r.get('flags', 'NORMAL')}]"
        for r in results
    )

    import openai
    import json as json_module
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": NUTRITION_PREVIEW_SYSTEM_PROMPT},
            {"role": "user", "content": f"Lab results:\n{biomarker_text}\n\nCreate the preview meal plan in JSON."},
        ],
        max_tokens=4000,
        temperature=0.7,
    )

    raw = response.choices[0].message.content or ""
    try:
        json_str = raw
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0]
        nutrition_data = json_module.loads(json_str)
    except (json_module.JSONDecodeError, IndexError):
        raise HTTPException(status_code=500, detail="Failed to generate nutrition plan. Please try again.")

    result = {
        "biomarker_count": len(results),
        "biomarker_flags": nutrition_data.get("biomarker_flags", []),
        "meal_plan": nutrition_data.get("meal_plan", []),
        "shopping_list": nutrition_data.get("shopping_list", []),
        "exercise": nutrition_data.get("exercise", {}),
        "summary": nutrition_data.get("summary", ""),
    }

    _nutrition_cache[text_hash] = result
    _nutrition_cache_times[text_hash] = now
    if len(_nutrition_cache) > 100:
        oldest = min(_nutrition_cache_times, key=_nutrition_cache_times.get)
        del _nutrition_cache[oldest]
        del _nutrition_cache_times[oldest]

    _save_lead(db, body.email, "nutrition_preview", request)

    return result


# ---------- Public stats ----------
_stats_cache: dict = {}
_stats_cache_time: float = 0


@router.get("/public/stats")
def public_stats(db: Session = Depends(get_db)):
    global _stats_cache, _stats_cache_time
    now = time.time()
    if _stats_cache and now - _stats_cache_time < 3600:
        return _stats_cache

    try:
        biomarkers = db.query(TestResult).count()
        documents = db.query(Document).count()
        analyses = db.query(HealthReport).count()
    except Exception:
        biomarkers = documents = analyses = 0

    # Floor to avoid looking empty
    _stats_cache = {
        "biomarkers_analyzed": max(biomarkers, 100),
        "documents_processed": max(documents, 50),
        "analyses_run": max(analyses, 25),
    }
    _stats_cache_time = now
    return _stats_cache
