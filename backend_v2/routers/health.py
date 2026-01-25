"""Health Reports API router."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json
from datetime import datetime
from typing import Optional

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
    """Get list of available specialist analyses."""
    return {
        specialty: {
            "name": config["name"],
            "focus": config["focus"]
        }
        for specialty, config in SpecialistAgent.SPECIALISTS.items()
    }


@router.post("/analyze/{specialty}")
def run_specialist_analysis(
    specialty: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run analysis for a specific medical specialty."""
    if specialty not in SpecialistAgent.SPECIALISTS:
        raise HTTPException(status_code=400, detail=f"Unknown specialty: {specialty}")

    biomarkers = get_user_biomarkers(db, current_user.id)

    if not biomarkers:
        raise HTTPException(status_code=400, detail="No biomarkers available for analysis")

    # Get user's language preference (default to Romanian)
    user_language = current_user.language if current_user.language else "ro"

    # Get user's profile for context
    user_profile = get_user_profile(current_user)

    try:
        service = HealthAnalysisService(language=user_language, profile=user_profile)
        analysis = service.run_specialist_analysis(specialty, biomarkers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Save report
    report = HealthReport(
        user_id=current_user.id,
        report_type=specialty,
        title=f"{specialty.title()} Analysis",
        summary=analysis.get("summary", ""),
        findings=json.dumps(analysis.get("key_findings", [])),
        recommendations=json.dumps(analysis.get("recommendations", [])),
        risk_level=analysis.get("risk_level", "normal"),
        biomarkers_analyzed=len(analysis.get("key_findings", []))
    )
    db.add(report)
    db.commit()

    return analysis


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

    # Save gap analysis to database
    report = HealthReport(
        user_id=current_user.id,
        report_type="gap_analysis",
        title="Recommended Health Screenings",
        summary=analysis.get("summary", ""),
        findings=json.dumps(analysis.get("recommended_tests", [])),
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
    """Get the latest gap analysis report."""
    report = db.query(HealthReport)\
        .filter(HealthReport.user_id == current_user.id)\
        .filter(HealthReport.report_type == "gap_analysis")\
        .order_by(desc(HealthReport.created_at))\
        .first()

    if not report:
        return {"has_report": False}

    return {
        "has_report": True,
        "id": report.id,
        "summary": report.summary,
        "recommended_tests": json.loads(report.findings) if report.findings else [],
        "created_at": report.created_at.isoformat() if report.created_at else None
    }
