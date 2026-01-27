"""Health Reports API router."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
import json
from datetime import datetime
from typing import Optional, List

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, Document, TestResult, HealthReport
    from backend_v2.routers.documents import get_current_user
    from backend_v2.services.health_agents import HealthAnalysisService, SpecialistAgent
except ImportError:
    from database import get_db
    from models import User, Document, TestResult, HealthReport
    from routers.documents import get_current_user
    from services.health_agents import HealthAnalysisService, SpecialistAgent

router = APIRouter(prefix="/health", tags=["health"])


def get_user_biomarkers(db: Session, user_id: int) -> list:
    """Get all biomarkers for a user in analysis-ready format."""
    results = db.query(TestResult).join(Document)\
        .filter(Document.user_id == user_id)\
        .order_by(Document.document_date.desc())\
        .all()

    biomarkers = []
    for r in results:
        biomarkers.append({
            "name": r.test_name,
            "value": r.numeric_value if r.numeric_value is not None else r.value,
            "unit": r.unit,
            "range": r.reference_range,
            "date": r.document.document_date.strftime("%Y-%m-%d") if r.document.document_date else "Unknown",
            "status": "normal" if r.flags == "NORMAL" else "abnormal",
            "flags": r.flags
        })

    return biomarkers


def get_user_profile(user: User) -> dict:
    """Get user profile data for AI analysis."""
    from datetime import date

    profile = {}

    if user.full_name:
        profile["full_name"] = user.full_name

    if user.date_of_birth:
        profile["date_of_birth"] = user.date_of_birth.strftime("%Y-%m-%d")
        # Calculate age
        today = date.today()
        age = today.year - user.date_of_birth.year - ((today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day))
        profile["age"] = age

    if user.gender:
        profile["gender"] = user.gender

    if user.height_cm:
        profile["height_cm"] = user.height_cm

    if user.weight_kg:
        profile["weight_kg"] = user.weight_kg

    if user.height_cm and user.weight_kg:
        height_m = user.height_cm / 100
        profile["bmi"] = round(user.weight_kg / (height_m * height_m), 1)

    if user.blood_type:
        profile["blood_type"] = user.blood_type

    if user.smoking_status:
        profile["smoking_status"] = user.smoking_status

    if user.alcohol_consumption:
        profile["alcohol_consumption"] = user.alcohol_consumption

    if user.physical_activity:
        profile["physical_activity"] = user.physical_activity

    if user.allergies:
        profile["allergies"] = json.loads(user.allergies)

    if user.chronic_conditions:
        profile["chronic_conditions"] = json.loads(user.chronic_conditions)

    if user.current_medications:
        profile["current_medications"] = json.loads(user.current_medications)

    return profile


@router.post("/analyze")
def run_health_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run a full health analysis and save the report."""
    biomarkers = get_user_biomarkers(db, current_user.id)

    if not biomarkers:
        raise HTTPException(status_code=400, detail="No biomarkers available for analysis")

    # Get user's language preference (default to Romanian)
    user_language = current_user.language if current_user.language else "ro"

    # Get user's profile for context
    user_profile = get_user_profile(current_user)

    try:
        service = HealthAnalysisService(language=user_language, profile=user_profile)
        analysis = service.run_full_analysis(biomarkers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Save general report
    general = analysis.get("general", {})
    report = HealthReport(
        user_id=current_user.id,
        report_type="general",
        title="Comprehensive Health Analysis",
        summary=general.get("summary", "Analysis complete"),
        findings=json.dumps(general.get("findings", [])),
        recommendations=json.dumps(general.get("recommendations", [])),
        risk_level=general.get("risk_level", "normal"),
        biomarkers_analyzed=len(biomarkers)
    )
    db.add(report)

    # Save specialist reports
    for specialty, specialist_data in analysis.get("specialists", {}).items():
        specialist_report = HealthReport(
            user_id=current_user.id,
            report_type=specialty,
            title=f"{specialty.title()} Analysis",
            summary=specialist_data.get("summary", ""),
            findings=json.dumps(specialist_data.get("key_findings", [])),
            recommendations=json.dumps(specialist_data.get("recommendations", [])),
            risk_level=specialist_data.get("risk_level", "normal"),
            biomarkers_analyzed=len(specialist_data.get("key_findings", []))
        )
        db.add(specialist_report)

    db.commit()

    return {
        "status": "success",
        "general": analysis.get("general"),
        "specialists": analysis.get("specialists"),
        "analyzed_at": analysis.get("analyzed_at")
    }


@router.get("/reports")
def get_reports(
    report_type: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's health reports."""
    query = db.query(HealthReport)\
        .filter(HealthReport.user_id == current_user.id)\
        .order_by(desc(HealthReport.created_at))

    if report_type:
        query = query.filter(HealthReport.report_type == report_type)

    reports = query.limit(limit).all()

    return [{
        "id": r.id,
        "report_type": r.report_type,
        "title": r.title,
        "summary": r.summary,
        "risk_level": r.risk_level,
        "biomarkers_analyzed": r.biomarkers_analyzed,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "findings": json.loads(r.findings) if r.findings else [],
        "recommendations": json.loads(r.recommendations) if r.recommendations else []
    } for r in reports]


@router.get("/reports/{report_id}")
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific health report."""
    report = db.query(HealthReport)\
        .filter(HealthReport.id == report_id)\
        .filter(HealthReport.user_id == current_user.id)\
        .first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "id": report.id,
        "report_type": report.report_type,
        "title": report.title,
        "summary": report.summary,
        "risk_level": report.risk_level,
        "biomarkers_analyzed": report.biomarkers_analyzed,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "findings": json.loads(report.findings) if report.findings else [],
        "recommendations": json.loads(report.recommendations) if report.recommendations else []
    }


@router.get("/latest")
def get_latest_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the latest general health report."""
    report = db.query(HealthReport)\
        .filter(HealthReport.user_id == current_user.id)\
        .filter(HealthReport.report_type == "general")\
        .order_by(desc(HealthReport.created_at))\
        .first()

    if not report:
        return {"has_report": False, "message": "No health analysis available. Run an analysis first."}

    return {
        "has_report": True,
        "id": report.id,
        "title": report.title,
        "summary": report.summary,
        "risk_level": report.risk_level,
        "biomarkers_analyzed": report.biomarkers_analyzed,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "findings": json.loads(report.findings) if report.findings else [],
        "recommendations": json.loads(report.recommendations) if report.recommendations else []
    }


@router.get("/specialists")
def get_available_specialists():
    """Get information about specialist analyses.

    Note: The system uses DYNAMIC specialist selection - the AI generalist
    determines which specialists to consult based on your biomarker findings.
    This endpoint returns common specialist types for reference.
    """
    # Common specialists that the AI may recommend (non-exhaustive)
    common_specialists = {
        "cardiology": {
            "name": "Cardiologist",
            "focus": "cardiovascular health, lipid profiles, and heart disease risk"
        },
        "endocrinology": {
            "name": "Endocrinologist",
            "focus": "hormones, thyroid function, diabetes, and metabolic health"
        },
        "hematology": {
            "name": "Hematologist",
            "focus": "blood cells, anemia, clotting disorders, and blood health"
        },
        "hepatology": {
            "name": "Hepatologist",
            "focus": "liver function and liver disease"
        },
        "nephrology": {
            "name": "Nephrologist",
            "focus": "kidney function and renal health"
        },
        "gastroenterology": {
            "name": "Gastroenterologist",
            "focus": "digestive system and gastrointestinal health"
        },
        "immunology": {
            "name": "Immunologist",
            "focus": "immune system function and autoimmune conditions"
        },
        "infectious_disease": {
            "name": "Infectious Disease Specialist",
            "focus": "infections, inflammation markers, and immune response"
        }
    }
    return {
        "note": "Specialists are selected dynamically by the AI based on your biomarker findings. This list shows common specialist types.",
        "specialists": common_specialists
    }


class SpecialistRequest(BaseModel):
    """Request body for manual specialist analysis."""
    specialist_name: Optional[str] = None
    focus_area: Optional[str] = None
    relevant_markers: Optional[List[str]] = None


@router.post("/analyze/{specialty}")
def run_specialist_analysis(
    specialty: str,
    request: SpecialistRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run analysis for a specific medical specialty.

    The specialist configuration can be customized via the request body,
    or sensible defaults will be used based on the specialty name.
    """
    biomarkers = get_user_biomarkers(db, current_user.id)

    if not biomarkers:
        raise HTTPException(status_code=400, detail="No biomarkers available for analysis")

    # Get user's language preference (default to Romanian)
    user_language = current_user.language if current_user.language else "ro"

    # Get user's profile for context
    user_profile = get_user_profile(current_user)

    # Use request body config or defaults
    specialist_name = (request.specialist_name if request else None) or specialty.replace("_", " ").title()
    focus_area = (request.focus_area if request else None) or f"{specialty} related health concerns"
    relevant_markers = (request.relevant_markers if request else None) or []

    try:
        service = HealthAnalysisService(language=user_language, profile=user_profile)
        analysis = service.run_specialist_analysis(
            specialty=specialty,
            biomarkers=biomarkers,
            specialist_name=specialist_name,
            focus_area=focus_area,
            relevant_markers=relevant_markers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Save report
    report = HealthReport(
        user_id=current_user.id,
        report_type=specialty,
        title=f"{specialist_name} Analysis",
        summary=analysis.get("summary", ""),
        findings=json.dumps(analysis.get("key_findings", [])),
        recommendations=json.dumps(analysis.get("recommendations", [])),
        risk_level=analysis.get("risk_level", "normal"),
        biomarkers_analyzed=len(analysis.get("key_findings", []))
    )
    db.add(report)
    db.commit()

    return analysis


def enrich_recommended_tests_with_history(recommended_tests: list, db: Session, user_id: int) -> list:
    """Enhance recommended tests with last_done info from user's test history."""
    import re

    # Get user's test history with dates for matching
    user_tests = db.query(TestResult.test_name, TestResult.canonical_name, Document.document_date)\
        .join(Document)\
        .filter(Document.user_id == user_id)\
        .order_by(Document.document_date.desc())\
        .all()

    # Build a map of test names to their most recent date
    test_dates = {}
    for test_name, canonical_name, doc_date in user_tests:
        # Use canonical name if available, otherwise normalize test name
        key = (canonical_name or test_name).lower().strip()
        if key not in test_dates and doc_date:
            test_dates[key] = doc_date

    # Also build with original names for better matching
    for test_name, canonical_name, doc_date in user_tests:
        key = test_name.lower().strip()
        if key not in test_dates and doc_date:
            test_dates[key] = doc_date

    # Enhance each recommended test with last_done info
    for test in recommended_tests:
        test_name = test.get("test_name", "").lower().strip()
        last_done = None

        # Try exact match first
        if test_name in test_dates:
            last_done = test_dates[test_name]
        else:
            # Try partial matching (test name contains or is contained in user's tests)
            for user_test, date in test_dates.items():
                # Check if key terms match
                if (test_name in user_test or
                    user_test in test_name or
                    any(word in user_test for word in test_name.split() if len(word) > 3)):
                    last_done = date
                    break

        if last_done:
            test["last_done_date"] = last_done.strftime("%Y-%m-%d")
            # Calculate months since last done
            months_ago = (datetime.now() - last_done).days // 30
            test["months_since_last"] = months_ago

            # Determine if overdue based on frequency
            frequency = test.get("frequency", "").lower()
            recommended_months = 12  # Default to annual
            if "year" in frequency:
                try:
                    # Extract number of years (e.g., "every 2 years")
                    match = re.search(r'(\d+)\s*year', frequency)
                    if match:
                        recommended_months = int(match.group(1)) * 12
                except:
                    pass
            elif "6 month" in frequency or "semi" in frequency:
                recommended_months = 6
            elif "3 month" in frequency or "quarter" in frequency:
                recommended_months = 3
            elif "month" in frequency:
                recommended_months = 1

            test["is_overdue"] = months_ago > recommended_months
            test["recommended_interval_months"] = recommended_months
        else:
            test["last_done_date"] = None
            test["months_since_last"] = None
            test["is_overdue"] = True  # Never done = overdue
            test["recommended_interval_months"] = 12

    return recommended_tests


@router.post("/gap-analysis")
def run_gap_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run gap analysis to recommend missing health screenings."""
    # Get list of existing test names
    results = db.query(TestResult.test_name).join(Document)\
        .filter(Document.user_id == current_user.id)\
        .distinct()\
        .all()

    existing_tests = [r[0] for r in results]

    # Get user's language and profile
    user_language = current_user.language if current_user.language else "ro"
    user_profile = get_user_profile(current_user)

    try:
        service = HealthAnalysisService(language=user_language, profile=user_profile)
        analysis = service.run_gap_analysis(existing_tests)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")

    # Enrich recommended tests with "last done" info
    recommended_tests = analysis.get("recommended_tests", [])
    enriched_tests = enrich_recommended_tests_with_history(recommended_tests, db, current_user.id)
    analysis["recommended_tests"] = enriched_tests

    # Save gap analysis to database (with enriched data)
    report = HealthReport(
        user_id=current_user.id,
        report_type="gap_analysis",
        title="Recommended Health Screenings",
        summary=analysis.get("summary", ""),
        findings=json.dumps(enriched_tests),
        recommendations=json.dumps([]),
        risk_level="normal",
        biomarkers_analyzed=len(existing_tests)
    )
    db.add(report)
    db.commit()

    return {
        "status": "success",
        "existing_tests_count": len(existing_tests),
        "analysis": analysis,
        "analyzed_at": datetime.now().isoformat()
    }


@router.get("/gap-analysis/latest")
def get_latest_gap_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the latest gap analysis report with 'last done' tracking."""
    report = db.query(HealthReport)\
        .filter(HealthReport.user_id == current_user.id)\
        .filter(HealthReport.report_type == "gap_analysis")\
        .order_by(desc(HealthReport.created_at))\
        .first()

    if not report:
        return {"has_report": False}

    recommended_tests = json.loads(report.findings) if report.findings else []

    # Re-enrich with current test history (may have changed since analysis was run)
    enriched_tests = enrich_recommended_tests_with_history(recommended_tests, db, current_user.id)

    return {
        "has_report": True,
        "id": report.id,
        "summary": report.summary,
        "recommended_tests": enriched_tests,
        "created_at": report.created_at.isoformat() if report.created_at else None
    }


@router.get("/history")
def get_report_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get report history grouped by analysis session.

    Reports created within the same minute are considered part of the same session.
    Returns sessions with their general report and specialist reports.
    """
    from sqlalchemy import func
    from datetime import timedelta

    # Get all general reports first (they mark analysis sessions)
    general_reports = db.query(HealthReport)\
        .filter(HealthReport.user_id == current_user.id)\
        .filter(HealthReport.report_type == "general")\
        .order_by(desc(HealthReport.created_at))\
        .limit(limit)\
        .all()

    sessions = []

    for general in general_reports:
        # Find specialist reports created within 5 minutes of this general report
        session_start = general.created_at - timedelta(minutes=1)
        session_end = general.created_at + timedelta(minutes=5)

        specialist_reports = db.query(HealthReport)\
            .filter(HealthReport.user_id == current_user.id)\
            .filter(HealthReport.report_type != "general")\
            .filter(HealthReport.report_type != "gap_analysis")\
            .filter(HealthReport.created_at >= session_start)\
            .filter(HealthReport.created_at <= session_end)\
            .all()

        sessions.append({
            "session_date": general.created_at.isoformat(),
            "general": {
                "id": general.id,
                "summary": general.summary,
                "risk_level": general.risk_level,
                "biomarkers_analyzed": general.biomarkers_analyzed,
                "findings": json.loads(general.findings) if general.findings else [],
                "recommendations": json.loads(general.recommendations) if general.recommendations else []
            },
            "specialists": [{
                "id": r.id,
                "report_type": r.report_type,
                "title": r.title,
                "summary": r.summary,
                "risk_level": r.risk_level,
                "findings": json.loads(r.findings) if r.findings else [],
                "recommendations": json.loads(r.recommendations) if r.recommendations else []
            } for r in specialist_reports]
        })

    return {"sessions": sessions, "total": len(sessions)}


@router.get("/compare/{report_id_1}/{report_id_2}")
def compare_reports(
    report_id_1: int,
    report_id_2: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare two health reports side by side."""
    report_1 = db.query(HealthReport)\
        .filter(HealthReport.id == report_id_1)\
        .filter(HealthReport.user_id == current_user.id)\
        .first()

    report_2 = db.query(HealthReport)\
        .filter(HealthReport.id == report_id_2)\
        .filter(HealthReport.user_id == current_user.id)\
        .first()

    if not report_1 or not report_2:
        raise HTTPException(status_code=404, detail="One or both reports not found")

    def format_report(r):
        return {
            "id": r.id,
            "report_type": r.report_type,
            "title": r.title,
            "summary": r.summary,
            "risk_level": r.risk_level,
            "biomarkers_analyzed": r.biomarkers_analyzed,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "findings": json.loads(r.findings) if r.findings else [],
            "recommendations": json.loads(r.recommendations) if r.recommendations else []
        }

    # Determine changes
    risk_change = None
    if report_1.risk_level != report_2.risk_level:
        risk_levels = {"normal": 0, "attention": 1, "concern": 2, "urgent": 3}
        old_level = risk_levels.get(report_1.risk_level, 0)
        new_level = risk_levels.get(report_2.risk_level, 0)
        if new_level > old_level:
            risk_change = "worsened"
        elif new_level < old_level:
            risk_change = "improved"

    return {
        "report_1": format_report(report_1),
        "report_2": format_report(report_2),
        "comparison": {
            "risk_change": risk_change,
            "days_between": (report_2.created_at - report_1.created_at).days if report_1.created_at and report_2.created_at else None,
            "biomarkers_change": report_2.biomarkers_analyzed - report_1.biomarkers_analyzed if report_1.biomarkers_analyzed and report_2.biomarkers_analyzed else None
        }
    }
