"""Lifestyle & Wellbeing API router.

Provides nutrition and exercise recommendations based on user's biomarkers.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json
from datetime import datetime, timedelta

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, HealthReport
    from backend_v2.routers.documents import get_current_user
    from backend_v2.routers.health import (
        get_user_biomarkers, get_user_profile,
        get_report_content, save_report_content
    )
    from backend_v2.services.health_agents import LifestyleAnalysisService
    from backend_v2.services.vault_helper import get_vault_helper
    from backend_v2.services.subscription_service import SubscriptionService
    from backend_v2.services.audit_service import AuditService
except ImportError:
    from database import get_db
    from models import User, HealthReport
    from routers.documents import get_current_user
    from routers.health import (
        get_user_biomarkers, get_user_profile,
        get_report_content, save_report_content
    )
    from services.health_agents import LifestyleAnalysisService
    from services.vault_helper import get_vault_helper
    from services.subscription_service import SubscriptionService
    from services.audit_service import AuditService

router = APIRouter(prefix="/lifestyle", tags=["lifestyle"])


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

    try:
        service = LifestyleAnalysisService(language=user_language, profile=user_profile)
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

    if not nutrition_report and not exercise_report:
        return {"has_report": False}

    result = {"has_report": True}

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
