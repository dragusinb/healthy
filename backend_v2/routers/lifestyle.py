"""Lifestyle & Wellbeing API router.

Provides nutrition and exercise recommendations based on user's biomarkers.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
import json
import hashlib
from datetime import datetime, timedelta

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, HealthReport, FoodPreference
    from backend_v2.routers.documents import get_current_user
    from backend_v2.routers.health import (
        get_user_biomarkers, get_user_profile,
        get_report_content, save_report_content
    )
    from backend_v2.services.health_agents import LifestyleAnalysisService, NutritionAgent, format_profile_context
    from backend_v2.services.vault_helper import get_vault_helper
    from backend_v2.services.subscription_service import SubscriptionService
    from backend_v2.services.audit_service import AuditService
except ImportError:
    from database import get_db
    from models import User, HealthReport, FoodPreference
    from routers.documents import get_current_user
    from routers.health import (
        get_user_biomarkers, get_user_profile,
        get_report_content, save_report_content
    )
    from services.health_agents import LifestyleAnalysisService, NutritionAgent, format_profile_context
    from services.vault_helper import get_vault_helper
    from services.subscription_service import SubscriptionService
    from services.audit_service import AuditService


class FoodPreferenceRequest(BaseModel):
    food_name: str
    preference: str  # "liked" or "disliked"
    source: str = "meal_plan"


def _hash_food_name(name: str) -> str:
    """Create SHA-256 hash of normalized food name for dedup lookup."""
    return hashlib.sha256(name.strip().lower().encode("utf-8")).hexdigest()


def _get_food_name(pref: FoodPreference, user_id: int) -> str:
    """Decrypt food name from preference, with plaintext fallback."""
    if pref.food_name_enc:
        vault = get_vault_helper(user_id)
        if vault.is_available:
            try:
                return vault.decrypt_data(pref.food_name_enc)
            except Exception:
                pass
    return pref.food_name or ""


def _get_user_food_preferences(db: Session, user_id: int) -> dict:
    """Get all food preferences for a user as {food_name_lower: preference}."""
    prefs = db.query(FoodPreference).filter(FoodPreference.user_id == user_id).all()
    result = {}
    for p in prefs:
        name = _get_food_name(p, user_id)
        if name:
            result[name.lower()] = p.preference
    return result


def _get_food_pref_lists(db: Session, user_id: int) -> dict:
    """Get food preferences grouped into liked/disliked lists."""
    prefs = db.query(FoodPreference).filter(FoodPreference.user_id == user_id).all()
    liked = []
    disliked = []
    for p in prefs:
        name = _get_food_name(p, user_id)
        if name:
            if p.preference == "liked":
                liked.append(name)
            elif p.preference == "disliked":
                disliked.append(name)
    return {"liked": liked, "disliked": disliked}

def _extract_previous_foods(db: Session, user_id: int, limit: int = 3) -> list:
    """Extract all food items from the last N nutrition reports for variety."""
    reports = db.query(HealthReport)\
        .filter(HealthReport.user_id == user_id, HealthReport.report_type == "nutrition")\
        .order_by(desc(HealthReport.created_at))\
        .limit(limit).all()

    foods = set()
    for report in reports:
        data = _get_lifestyle_report_content(report, user_id)
        for day in data.get("meal_plan", []):
            for meal in day.get("meals", []):
                for item in meal.get("items", []):
                    foods.add(item.lower())
    return list(foods)


router = APIRouter(prefix="/lifestyle", tags=["lifestyle"])


@router.get("/food-preferences")
def get_food_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all food preferences for the current user."""
    prefs = db.query(FoodPreference).filter(FoodPreference.user_id == current_user.id).all()
    items = []
    for p in prefs:
        name = _get_food_name(p, current_user.id)
        if name:
            items.append({
                "food_name": name,
                "preference": p.preference,
                "source": p.source
            })
    return {"preferences": items}


@router.post("/food-preferences")
def set_food_preference(
    body: FoodPreferenceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set/toggle a food preference. Same preference = remove (toggle off)."""
    if body.preference not in ("liked", "disliked"):
        raise HTTPException(status_code=400, detail="preference must be 'liked' or 'disliked'")

    name_hash = _hash_food_name(body.food_name)

    existing = db.query(FoodPreference).filter(
        FoodPreference.user_id == current_user.id,
        FoodPreference.food_name_hash == name_hash
    ).first()

    if existing:
        if existing.preference == body.preference:
            # Same preference clicked again → toggle off (remove)
            db.delete(existing)
            db.commit()
            return {"action": "removed", "food_name": body.food_name}
        else:
            # Different preference → update
            existing.preference = body.preference
            existing.source = body.source
            db.commit()
            return {"action": "updated", "food_name": body.food_name, "preference": body.preference}
    else:
        # New preference
        vault = get_vault_helper(current_user.id)
        pref = FoodPreference(
            user_id=current_user.id,
            food_name_hash=name_hash,
            food_name=body.food_name.strip(),
            preference=body.preference,
            source=body.source
        )
        if vault.is_available:
            pref.food_name_enc = vault.encrypt_data(body.food_name.strip())
        db.add(pref)
        db.commit()
        return {"action": "created", "food_name": body.food_name, "preference": body.preference}


@router.post("/analyze")
def run_lifestyle_analysis(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run full lifestyle analysis (nutrition + exercise) and save reports."""
    audit = AuditService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Check subscription quota (counts as 1 analysis despite 2 AI calls)
    subscription_service = SubscriptionService(db)
    can_analyze, message = subscription_service.check_can_run_analysis(current_user.id, "general")
    if not can_analyze:
        audit.log_action(
            user_id=current_user.id,
            action="analyze_lifestyle",
            resource_type="report",
            details={"reason": "quota_exceeded"},
            ip_address=ip_address,
            user_agent=user_agent,
            status="blocked"
        )
        raise HTTPException(status_code=403, detail=message)

    biomarkers = get_user_biomarkers(db, current_user.id)
    if not biomarkers:
        raise HTTPException(status_code=400, detail="No biomarkers available for analysis")

    user_language = current_user.language if current_user.language else "ro"
    user_profile = get_user_profile(current_user)

    # Get food preferences for AI context
    food_prefs = _get_food_pref_lists(db, current_user.id)

    try:
        service = LifestyleAnalysisService(language=user_language, profile=user_profile, food_preferences=food_prefs)
        analysis = service.run_full_lifestyle_analysis(biomarkers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lifestyle analysis failed: {str(e)}")

    # Save nutrition report
    nutrition_data = analysis.get("nutrition", {})
    nutrition_report = HealthReport(
        user_id=current_user.id,
        report_type="nutrition",
        title="Nutrition Recommendations",
        risk_level="normal",
        biomarkers_analyzed=len(biomarkers)
    )
    vault_helper = get_vault_helper(current_user.id)
    if vault_helper.is_available:
        # Store full data encrypted
        nutrition_report.content_enc = vault_helper.encrypt_json(nutrition_data)
    else:
        # No vault - store full JSON in summary field so we can parse it back
        nutrition_report.summary = json.dumps(nutrition_data)
    db.add(nutrition_report)

    # Save exercise report
    exercise_data = analysis.get("exercise", {})
    exercise_report = HealthReport(
        user_id=current_user.id,
        report_type="exercise",
        title="Exercise Recommendations",
        risk_level="normal",
        biomarkers_analyzed=len(biomarkers)
    )
    if vault_helper.is_available:
        exercise_report.content_enc = vault_helper.encrypt_json(exercise_data)
    else:
        exercise_report.summary = json.dumps(exercise_data)
    db.add(exercise_report)

    db.commit()

    # Increment AI usage counter ONCE (not twice)
    subscription_service.increment_ai_usage(current_user.id)

    # Log successful analysis
    audit.log_action(
        user_id=current_user.id,
        action="analyze_lifestyle",
        resource_type="report",
        resource_id=nutrition_report.id,
        details={
            "biomarkers_analyzed": len(biomarkers),
            "nutrition_report_id": nutrition_report.id,
            "exercise_report_id": exercise_report.id
        },
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )

    audit.track_usage(current_user.id, "ai_analyses_run", 1)
    audit.track_usage(current_user.id, "reports_generated", 2)

    return {
        "status": "success",
        "nutrition": nutrition_data,
        "exercise": exercise_data,
        "analyzed_at": analysis.get("analyzed_at")
    }


@router.post("/new-menu")
def regenerate_menu(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Regenerate only the nutrition/meal plan with new, different foods."""
    audit = AuditService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Check subscription quota (counts as 1 analysis)
    subscription_service = SubscriptionService(db)
    can_analyze, message = subscription_service.check_can_run_analysis(current_user.id, "general")
    if not can_analyze:
        audit.log_action(
            user_id=current_user.id,
            action="new_menu",
            resource_type="report",
            details={"reason": "quota_exceeded"},
            ip_address=ip_address,
            user_agent=user_agent,
            status="blocked"
        )
        raise HTTPException(status_code=403, detail=message)

    biomarkers = get_user_biomarkers(db, current_user.id)
    if not biomarkers:
        raise HTTPException(status_code=400, detail="No biomarkers available for analysis")

    user_language = current_user.language if current_user.language else "ro"
    user_profile = get_user_profile(current_user)

    # Get food preferences
    food_prefs = _get_food_pref_lists(db, current_user.id)

    # Get previously used foods for variety
    previous_foods = _extract_previous_foods(db, current_user.id, limit=3)

    previous_foods_context = ""
    if previous_foods:
        foods_list = "\n".join(f"- {f}" for f in previous_foods[:100])  # Cap at 100 items
        previous_foods_context = f"PREVIOUS MEAL PLANS (DO NOT repeat these — create entirely new meals):\n{foods_list}"

    try:
        service = LifestyleAnalysisService(language=user_language, profile=user_profile, food_preferences=food_prefs)
        profile_context = format_profile_context(user_profile) if user_profile else ""
        food_pref_context = service._format_food_pref_context()

        nutrition_agent = NutritionAgent(language=user_language)
        nutrition_data = nutrition_agent.analyze(biomarkers, profile_context, food_pref_context, previous_foods_context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Menu generation failed: {str(e)}")

    # Save as new nutrition report
    nutrition_report = HealthReport(
        user_id=current_user.id,
        report_type="nutrition",
        title="Nutrition Recommendations",
        risk_level="normal",
        biomarkers_analyzed=len(biomarkers)
    )
    vault_helper = get_vault_helper(current_user.id)
    if vault_helper.is_available:
        nutrition_report.content_enc = vault_helper.encrypt_json(nutrition_data)
    else:
        nutrition_report.summary = json.dumps(nutrition_data)
    db.add(nutrition_report)
    db.commit()

    # Increment AI usage counter
    subscription_service.increment_ai_usage(current_user.id)

    audit.log_action(
        user_id=current_user.id,
        action="new_menu",
        resource_type="report",
        resource_id=nutrition_report.id,
        details={
            "biomarkers_analyzed": len(biomarkers),
            "previous_foods_count": len(previous_foods),
            "nutrition_report_id": nutrition_report.id
        },
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )

    audit.track_usage(current_user.id, "ai_analyses_run", 1)
    audit.track_usage(current_user.id, "reports_generated", 1)

    return {
        "status": "success",
        "nutrition": nutrition_data,
        "created_at": datetime.now().isoformat()
    }


def _get_lifestyle_report_content(report: HealthReport, user_id: int) -> dict:
    """Get full lifestyle report content, preferring vault-encrypted."""
    # Try vault-encrypted full data first
    if report.content_enc and user_id:
        vault_helper = get_vault_helper(user_id)
        if vault_helper.is_available:
            try:
                return vault_helper.decrypt_json(report.content_enc)
            except Exception:
                pass

    # Try JSON stored in summary field (non-vault fallback)
    if report.summary:
        try:
            return json.loads(report.summary)
        except (json.JSONDecodeError, TypeError):
            pass

    # Last resort: return basic structure with summary text
    return {"summary": report.summary or ""}


@router.get("/latest")
def get_latest_lifestyle(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the latest nutrition and exercise reports."""
    nutrition_report = db.query(HealthReport)\
        .filter(HealthReport.user_id == current_user.id)\
        .filter(HealthReport.report_type == "nutrition")\
        .order_by(desc(HealthReport.created_at))\
        .first()

    exercise_report = db.query(HealthReport)\
        .filter(HealthReport.user_id == current_user.id)\
        .filter(HealthReport.report_type == "exercise")\
        .order_by(desc(HealthReport.created_at))\
        .first()

    # Always include food preferences
    food_prefs = _get_user_food_preferences(db, current_user.id)

    if not nutrition_report and not exercise_report:
        return {"has_report": False, "food_preferences": food_prefs}

    result = {"has_report": True, "food_preferences": food_prefs}

    if nutrition_report:
        result["nutrition"] = _get_lifestyle_report_content(nutrition_report, current_user.id)
        result["nutrition_id"] = nutrition_report.id
        result["created_at"] = nutrition_report.created_at.isoformat() if nutrition_report.created_at else None

    if exercise_report:
        result["exercise"] = _get_lifestyle_report_content(exercise_report, current_user.id)
        result["exercise_id"] = exercise_report.id
        if not result.get("created_at"):
            result["created_at"] = exercise_report.created_at.isoformat() if exercise_report.created_at else None

    return result


@router.get("/reports")
def get_lifestyle_reports(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated history of lifestyle reports grouped by session."""
    # Get nutrition reports as session anchors
    nutrition_reports = db.query(HealthReport)\
        .filter(HealthReport.user_id == current_user.id)\
        .filter(HealthReport.report_type == "nutrition")\
        .order_by(desc(HealthReport.created_at))\
        .limit(limit)\
        .all()

    sessions = []
    for nutrition in nutrition_reports:
        # Find matching exercise report (created within 5 minutes)
        session_start = nutrition.created_at - timedelta(minutes=1)
        session_end = nutrition.created_at + timedelta(minutes=5)

        exercise = db.query(HealthReport)\
            .filter(HealthReport.user_id == current_user.id)\
            .filter(HealthReport.report_type == "exercise")\
            .filter(HealthReport.created_at >= session_start)\
            .filter(HealthReport.created_at <= session_end)\
            .first()

        session = {
            "created_at": nutrition.created_at.isoformat(),
            "biomarkers_analyzed": nutrition.biomarkers_analyzed,
            "nutrition": _get_lifestyle_report_content(nutrition, current_user.id),
        }
        if exercise:
            session["exercise"] = _get_lifestyle_report_content(exercise, current_user.id)

        sessions.append(session)

    return {"sessions": sessions, "total": len(sessions)}
