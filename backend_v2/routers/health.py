"""Health Reports API router."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
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
    from backend_v2.services.vault_helper import get_vault_helper
    from backend_v2.services.notification_service import notify_analysis_complete
    from backend_v2.services.subscription_service import SubscriptionService
    from backend_v2.services.audit_service import AuditService
except ImportError:
    from database import get_db
    from models import User, Document, TestResult, HealthReport
    from routers.documents import get_current_user
    from services.health_agents import HealthAnalysisService, SpecialistAgent
    from services.vault_helper import get_vault_helper
    from services.notification_service import notify_analysis_complete
    from services.subscription_service import SubscriptionService
    from services.audit_service import AuditService


def get_report_content(report: HealthReport, user_id: int = None) -> dict:
    """Get report content, preferring vault-encrypted if available.

    Args:
        report: HealthReport object
        user_id: User ID for per-user vault decryption
    """
    if report.content_enc and user_id:
        vault_helper = get_vault_helper(user_id)
        if vault_helper.is_available:
            try:
                content = vault_helper.decrypt_json(report.content_enc)
                summary = content.get("summary", "")
                findings = content.get("findings", [])
                recommendations = content.get("recommendations", [])

                # Handle case where findings/recommendations were stored as JSON strings
                # (from migration) instead of parsed lists
                if isinstance(findings, str):
                    try:
                        findings = json.loads(findings)
                    except (json.JSONDecodeError, TypeError):
                        findings = []
                if isinstance(recommendations, str):
                    try:
                        recommendations = json.loads(recommendations)
                    except (json.JSONDecodeError, TypeError):
                        recommendations = []

                return {
                    "summary": summary,
                    "findings": findings if isinstance(findings, list) else [],
                    "recommendations": recommendations if isinstance(recommendations, list) else []
                }
            except Exception:
                pass  # Fall back to legacy

    # Fall back to legacy unencrypted fields
    return {
        "summary": report.summary or "",
        "findings": json.loads(report.findings) if report.findings else [],
        "recommendations": json.loads(report.recommendations) if report.recommendations else []
    }


def save_report_content(report: HealthReport, summary: str, findings: list, recommendations: list, user_id: int = None):
    """Save report content, using vault encryption if available.

    Args:
        report: HealthReport object
        summary: Report summary text
        findings: List of findings
        recommendations: List of recommendations
        user_id: User ID for per-user vault encryption
    """
    encrypted = False
    if user_id:
        vault_helper = get_vault_helper(user_id)
        if vault_helper.is_available:
            content = {
                "summary": summary,
                "findings": findings,
                "recommendations": recommendations
            }
            report.content_enc = vault_helper.encrypt_json(content)
            # Clear legacy fields
            report.summary = None
            report.findings = None
            report.recommendations = None
            encrypted = True

    if not encrypted:
        # Fall back to legacy storage
        report.summary = summary
        report.findings = json.dumps(findings)
        report.recommendations = json.dumps(recommendations)

router = APIRouter(prefix="/health", tags=["health"])


def get_user_biomarkers(db: Session, user_id: int) -> list:
    """Get all biomarkers for a user in analysis-ready format."""
    results = db.query(TestResult).join(Document)\
        .filter(Document.user_id == user_id)\
        .order_by(Document.document_date.desc())\
        .all()

    # Get vault helper for this user
    vault_helper = get_vault_helper(user_id)

    biomarkers = []
    for r in results:
        # Get values, preferring vault-encrypted
        value = None
        numeric_value = None

        if vault_helper.is_available:
            try:
                if r.value_enc:
                    value = vault_helper.decrypt_data(r.value_enc)
                if r.numeric_value_enc:
                    numeric_value = vault_helper.decrypt_number(r.numeric_value_enc)
            except Exception:
                pass

        # Fall back to legacy
        if value is None:
            value = r.value
        if numeric_value is None:
            numeric_value = r.numeric_value

        biomarkers.append({
            "name": r.test_name,
            "value": numeric_value if numeric_value is not None else value,
            "unit": r.unit,
            "range": r.reference_range,
            "date": r.document.document_date.strftime("%Y-%m-%d") if r.document.document_date else "Unknown",
            "status": "normal" if r.flags == "NORMAL" else "abnormal",
            "flags": r.flags
        })

    return biomarkers


def get_user_profile(user: User, user_id: int = None) -> dict:
    """Get user profile data for AI analysis, using vault-encrypted fields when available.

    Args:
        user: User object
        user_id: User ID for per-user vault decryption (defaults to user.id if not provided)
    """
    from datetime import date

    profile = {}

    # Use provided user_id or fall back to user.id
    uid = user_id if user_id else user.id
    vault_helper = get_vault_helper(uid)

    # Try vault-encrypted fields first
    full_name = None
    date_of_birth_str = None
    gender = None
    blood_type = None
    height_cm = None
    weight_kg = None
    allergies = None
    chronic_conditions = None
    current_medications = None

    if vault_helper.is_available:
        try:
            if user.full_name_enc:
                full_name = vault_helper.decrypt_data(user.full_name_enc)
            if user.date_of_birth_enc:
                date_of_birth_str = vault_helper.decrypt_data(user.date_of_birth_enc)
            if user.gender_enc:
                gender = vault_helper.decrypt_data(user.gender_enc)
            if user.blood_type_enc:
                blood_type = vault_helper.decrypt_data(user.blood_type_enc)
            if user.profile_data_enc:
                profile_data = vault_helper.decrypt_json(user.profile_data_enc)
                height_cm = profile_data.get("height_cm")
                weight_kg = profile_data.get("weight_kg")
            if user.health_context_enc:
                health_context = vault_helper.decrypt_json(user.health_context_enc)
                allergies_raw = health_context.get("allergies")
                chronic_raw = health_context.get("chronic_conditions")
                meds_raw = health_context.get("current_medications")
                allergies = json.loads(allergies_raw) if isinstance(allergies_raw, str) else allergies_raw
                chronic_conditions = json.loads(chronic_raw) if isinstance(chronic_raw, str) else chronic_raw
                current_medications = json.loads(meds_raw) if isinstance(meds_raw, str) else meds_raw
        except Exception:
            pass

    # Fall back to legacy fields
    if full_name is None:
        full_name = user.full_name
    if date_of_birth_str is None and user.date_of_birth:
        date_of_birth_str = user.date_of_birth.strftime("%Y-%m-%d")
    if gender is None:
        gender = user.gender
    if blood_type is None:
        blood_type = user.blood_type
    if height_cm is None:
        height_cm = user.height_cm
    if weight_kg is None:
        weight_kg = user.weight_kg
    if allergies is None:
        allergies = json.loads(user.allergies) if user.allergies else None
    if chronic_conditions is None:
        chronic_conditions = json.loads(user.chronic_conditions) if user.chronic_conditions else None
    if current_medications is None:
        current_medications = json.loads(user.current_medications) if user.current_medications else None

    # Build profile dict
    if full_name:
        profile["full_name"] = full_name

    if date_of_birth_str:
        profile["date_of_birth"] = date_of_birth_str
        try:
            dob = datetime.strptime(date_of_birth_str, "%Y-%m-%d").date()
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            profile["age"] = age
        except Exception:
            pass

    if gender:
        profile["gender"] = gender

    if height_cm:
        profile["height_cm"] = height_cm

    if weight_kg:
        profile["weight_kg"] = weight_kg

    if height_cm and weight_kg:
        height_m = height_cm / 100
        profile["bmi"] = round(weight_kg / (height_m * height_m), 1)

    if blood_type:
        profile["blood_type"] = blood_type

    if user.smoking_status:
        profile["smoking_status"] = user.smoking_status

    if user.alcohol_consumption:
        profile["alcohol_consumption"] = user.alcohol_consumption

    if user.physical_activity:
        profile["physical_activity"] = user.physical_activity

    if allergies:
        profile["allergies"] = allergies

    if chronic_conditions:
        profile["chronic_conditions"] = chronic_conditions

    if current_medications:
        profile["current_medications"] = current_medications

    return profile


@router.post("/analyze")
def run_health_analysis(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run a full health analysis and save the report."""
    audit = AuditService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Check subscription quota for AI analyses
    subscription_service = SubscriptionService(db)
    can_analyze, message = subscription_service.check_can_run_analysis(current_user.id, "general")
    if not can_analyze:
        audit.log_action(
            user_id=current_user.id,
            action="analyze_health",
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
        risk_level=general.get("risk_level", "normal"),
        biomarkers_analyzed=len(biomarkers)
    )
    save_report_content(
        report,
        summary=general.get("summary", "Analysis complete"),
        findings=general.get("findings", []),
        recommendations=general.get("recommendations", []),
        user_id=current_user.id
    )
    db.add(report)

    # Save specialist reports
    for specialty, specialist_data in analysis.get("specialists", {}).items():
        specialist_report = HealthReport(
            user_id=current_user.id,
            report_type=specialty,
            title=f"{specialty.title()} Analysis",
            risk_level=specialist_data.get("risk_level", "normal"),
            biomarkers_analyzed=len(specialist_data.get("key_findings", []))
        )
        save_report_content(
            specialist_report,
            summary=specialist_data.get("summary", ""),
            findings=specialist_data.get("key_findings", []),
            recommendations=specialist_data.get("recommendations", []),
            user_id=current_user.id
        )
        db.add(specialist_report)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save reports: {str(e)}")

    # Increment AI usage counter
    subscription_service.increment_ai_usage(current_user.id)

    # Log successful analysis
    audit.log_action(
        user_id=current_user.id,
        action="analyze_health",
        resource_type="report",
        resource_id=report.id,
        details={
            "biomarkers_analyzed": len(biomarkers),
            "risk_level": general.get("risk_level", "normal"),
            "specialists_count": len(analysis.get("specialists", {}))
        },
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )

    # Track usage metrics
    audit.track_usage(current_user.id, "ai_analyses_run", 1)
    audit.track_usage(current_user.id, "reports_generated", 1 + len(analysis.get("specialists", {})))

    # Send notification about completed analysis
    try:
        # Determine worst risk level from all reports
        risk_levels = ["normal", "attention", "concern", "urgent"]
        worst_risk = general.get("risk_level", "normal")
        for specialty, specialist_data in analysis.get("specialists", {}).items():
            spec_risk = specialist_data.get("risk_level", "normal")
            if risk_levels.index(spec_risk) > risk_levels.index(worst_risk):
                worst_risk = spec_risk
        notify_analysis_complete(db, current_user.id, "general", worst_risk)
    except Exception as e:
        pass  # Don't fail the request if notification fails

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

    result = []
    for r in reports:
        content = get_report_content(r, current_user.id)
        result.append({
            "id": r.id,
            "report_type": r.report_type,
            "title": r.title,
            "summary": content["summary"],
            "risk_level": r.risk_level,
            "biomarkers_analyzed": r.biomarkers_analyzed,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "findings": content["findings"],
            "recommendations": content["recommendations"]
        })
    return result


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

    content = get_report_content(report, current_user.id)
    return {
        "id": report.id,
        "report_type": report.report_type,
        "title": report.title,
        "summary": content["summary"],
        "risk_level": report.risk_level,
        "biomarkers_analyzed": report.biomarkers_analyzed,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "findings": content["findings"],
        "recommendations": content["recommendations"]
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

    content = get_report_content(report, current_user.id)
    return {
        "has_report": True,
        "id": report.id,
        "title": report.title,
        "summary": content["summary"],
        "risk_level": report.risk_level,
        "biomarkers_analyzed": report.biomarkers_analyzed,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "findings": content["findings"],
        "recommendations": content["recommendations"]
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
    http_request: Request,
    request: SpecialistRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run analysis for a specific medical specialty.

    The specialist configuration can be customized via the request body,
    or sensible defaults will be used based on the specialty name.
    """
    audit = AuditService(db)
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")

    # Check subscription quota for specialist AI analyses
    subscription_service = SubscriptionService(db)
    can_analyze, message = subscription_service.check_can_run_analysis(current_user.id, specialty)
    if not can_analyze:
        audit.log_action(
            user_id=current_user.id,
            action="analyze_specialist",
            resource_type="report",
            details={"specialty": specialty, "reason": "quota_exceeded"},
            ip_address=ip_address,
            user_agent=user_agent,
            status="blocked"
        )
        raise HTTPException(status_code=403, detail=message)

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
        risk_level=analysis.get("risk_level", "normal"),
        biomarkers_analyzed=len(analysis.get("key_findings", []))
    )
    save_report_content(
        report,
        summary=analysis.get("summary", ""),
        findings=analysis.get("key_findings", []),
        recommendations=analysis.get("recommendations", []),
        user_id=current_user.id
    )
    db.add(report)
    db.commit()

    # Increment AI usage counter
    subscription_service.increment_ai_usage(current_user.id)

    # Log successful specialist analysis
    audit.log_action(
        user_id=current_user.id,
        action="analyze_specialist",
        resource_type="report",
        resource_id=report.id,
        details={
            "specialty": specialty,
            "risk_level": analysis.get("risk_level", "normal")
        },
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )

    # Track usage
    audit.track_usage(current_user.id, "ai_analyses_run", 1)
    audit.track_usage(current_user.id, "reports_generated", 1)

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
                except (ValueError, TypeError, AttributeError):
                    pass  # Frequency parsing failed, use default
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
    # Check subscription quota for AI analyses
    subscription_service = SubscriptionService(db)
    can_analyze, message = subscription_service.check_can_run_analysis(current_user.id, "general")
    if not can_analyze:
        raise HTTPException(status_code=403, detail=message)

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
        risk_level="normal",
        biomarkers_analyzed=len(existing_tests)
    )
    save_report_content(
        report,
        summary=analysis.get("summary", ""),
        findings=enriched_tests,
        recommendations=[],
        user_id=current_user.id
    )
    db.add(report)
    db.commit()

    # Increment AI usage counter
    subscription_service.increment_ai_usage(current_user.id)

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

    content = get_report_content(report, current_user.id)
    recommended_tests = content["findings"]

    # Re-enrich with current test history (may have changed since analysis was run)
    enriched_tests = enrich_recommended_tests_with_history(recommended_tests, db, current_user.id)

    return {
        "has_report": True,
        "id": report.id,
        "summary": content["summary"],
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
            .filter(HealthReport.report_type != "nutrition")\
            .filter(HealthReport.report_type != "exercise")\
            .filter(HealthReport.created_at >= session_start)\
            .filter(HealthReport.created_at <= session_end)\
            .all()

        general_content = get_report_content(general, current_user.id)
        specialist_items = []
        for r in specialist_reports:
            r_content = get_report_content(r, current_user.id)
            specialist_items.append({
                "id": r.id,
                "report_type": r.report_type,
                "title": r.title,
                "summary": r_content["summary"],
                "risk_level": r.risk_level,
                "findings": r_content["findings"],
                "recommendations": r_content["recommendations"]
            })

        sessions.append({
            "session_date": general.created_at.isoformat(),
            "general": {
                "id": general.id,
                "summary": general_content["summary"],
                "risk_level": general.risk_level,
                "biomarkers_analyzed": general.biomarkers_analyzed,
                "findings": general_content["findings"],
                "recommendations": general_content["recommendations"]
            },
            "specialists": specialist_items
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

    # Ensure older report is first, newer is second for consistent comparison
    if report_1.created_at and report_2.created_at and report_1.created_at > report_2.created_at:
        report_1, report_2 = report_2, report_1

    def format_report(r):
        content = get_report_content(r, current_user.id)
        return {
            "id": r.id,
            "report_type": r.report_type,
            "title": r.title,
            "summary": content["summary"],
            "risk_level": r.risk_level,
            "biomarkers_analyzed": r.biomarkers_analyzed,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "findings": content["findings"],
            "recommendations": content["recommendations"]
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
            "biomarkers_change": report_2.biomarkers_analyzed - report_1.biomarkers_analyzed if report_1.biomarkers_analyzed is not None and report_2.biomarkers_analyzed is not None else None
        }
    }


@router.get("/export-pdf")
def export_health_report_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export the latest health report session (general + specialists) as a PDF file."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm, mm
        from reportlab.lib.colors import HexColor
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, KeepTogether
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="PDF generation is not available. The 'reportlab' library is not installed on the server."
        )

    import io
    from fastapi.responses import StreamingResponse
    from datetime import timedelta

    # --- Fetch the latest general report ---
    general_report = db.query(HealthReport)\
        .filter(HealthReport.user_id == current_user.id)\
        .filter(HealthReport.report_type == "general")\
        .order_by(desc(HealthReport.created_at))\
        .first()

    if not general_report:
        raise HTTPException(status_code=404, detail="No health report found. Run a health analysis first.")

    general_content = get_report_content(general_report, current_user.id)

    # --- Fetch specialist reports from the same session (within 5 minutes) ---
    session_start = general_report.created_at - timedelta(minutes=1)
    session_end = general_report.created_at + timedelta(minutes=5)

    specialist_reports = db.query(HealthReport)\
        .filter(HealthReport.user_id == current_user.id)\
        .filter(HealthReport.report_type != "general")\
        .filter(HealthReport.report_type != "gap_analysis")\
        .filter(HealthReport.created_at >= session_start)\
        .filter(HealthReport.created_at <= session_end)\
        .all()

    # --- Fetch health score ---
    try:
        from backend_v2.services.health_score import calculate_health_score
    except ImportError:
        from services.health_score import calculate_health_score

    vault_helper = get_vault_helper(current_user.id)
    health_score_data = calculate_health_score(current_user, db, vault_helper)

    # --- Get user profile for the name ---
    user_profile = get_user_profile(current_user)
    user_name = user_profile.get("full_name", current_user.email)

    # --- Build the PDF ---
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    # Color palette
    COLOR_PRIMARY = HexColor("#1976D2")
    COLOR_DARK = HexColor("#212121")
    COLOR_SECONDARY = HexColor("#757575")
    COLOR_LIGHT_BG = HexColor("#F5F5F5")
    COLOR_GREEN = HexColor("#388E3C")
    COLOR_YELLOW = HexColor("#F9A825")
    COLOR_ORANGE = HexColor("#EF6C00")
    COLOR_RED = HexColor("#D32F2F")
    COLOR_LINE = HexColor("#E0E0E0")

    risk_colors = {
        "normal": COLOR_GREEN,
        "attention": COLOR_YELLOW,
        "concern": COLOR_ORANGE,
        "urgent": COLOR_RED,
    }

    grade_colors = {
        "excellent": COLOR_GREEN,
        "good": COLOR_GREEN,
        "fair": COLOR_YELLOW,
        "needs_attention": COLOR_ORANGE,
        "critical": COLOR_RED,
    }

    # Styles
    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=26,
        textColor=COLOR_PRIMARY,
        spaceAfter=4,
    )
    style_subtitle = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=COLOR_SECONDARY,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    style_section = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=COLOR_PRIMARY,
        spaceBefore=16,
        spaceAfter=6,
        borderPadding=(0, 0, 2, 0),
    )
    style_subsection = ParagraphStyle(
        "SubSectionHeading",
        parent=styles["Heading3"],
        fontSize=12,
        leading=15,
        textColor=COLOR_DARK,
        spaceBefore=10,
        spaceAfter=4,
    )
    style_body = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=COLOR_DARK,
        spaceAfter=6,
    )
    style_bullet = ParagraphStyle(
        "BulletItem",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=COLOR_DARK,
        leftIndent=16,
        spaceAfter=3,
        bulletIndent=6,
    )
    style_disclaimer = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=COLOR_SECONDARY,
        spaceBefore=20,
        spaceAfter=0,
    )
    style_label = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        textColor=COLOR_SECONDARY,
        spaceAfter=2,
    )
    style_score_number = ParagraphStyle(
        "ScoreNumber",
        parent=styles["Normal"],
        fontSize=36,
        leading=40,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    style_score_grade = ParagraphStyle(
        "ScoreGrade",
        parent=styles["Normal"],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    elements = []

    # --- Header ---
    report_date = general_report.created_at.strftime("%d %B %Y") if general_report.created_at else datetime.now().strftime("%d %B %Y")
    elements.append(Paragraph("Health Report", style_title))
    elements.append(Paragraph(f"analize.online  |  {report_date}", style_subtitle))
    elements.append(HRFlowable(width="100%", thickness=1, color=COLOR_LINE, spaceAfter=10))

    # --- Patient info ---
    elements.append(Paragraph(f"<b>Patient:</b> {_escape_xml(user_name)}", style_body))
    if user_profile.get("age"):
        age_gender = f"Age {user_profile['age']}"
        if user_profile.get("gender"):
            age_gender += f" | {user_profile['gender'].capitalize()}"
        elements.append(Paragraph(age_gender, style_label))
    elements.append(Spacer(1, 6))

    # --- Health Score Section ---
    elements.append(Paragraph("Health Score", style_section))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_LINE, spaceAfter=8))

    score_val = health_score_data.get("score", 0)
    grade_val = health_score_data.get("grade", "fair")
    grade_display = grade_val.replace("_", " ").title()
    score_color = grade_colors.get(grade_val, COLOR_DARK)

    score_style = ParagraphStyle("ScoreDynamic", parent=style_score_number, textColor=score_color)
    grade_style = ParagraphStyle("GradeDynamic", parent=style_score_grade, textColor=score_color)

    elements.append(Paragraph(f"<b>{score_val}</b> / 100", score_style))
    elements.append(Paragraph(grade_display, grade_style))

    # Score components table
    components = health_score_data.get("components", {})
    if components:
        comp_data = [["Component", "Score", "Detail"]]
        for key, comp in components.items():
            comp_data.append([
                comp.get("label", key),
                f"{comp.get('score', 0)}%",
                comp.get("detail", "")
            ])

        comp_table = Table(comp_data, colWidths=[5.5 * cm, 2 * cm, 9 * cm])
        comp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("BACKGROUND", (0, 1), (-1, -1), COLOR_LIGHT_BG),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_LINE),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(comp_table)
    elements.append(Spacer(1, 8))

    # --- General Analysis Section ---
    risk_level = general_report.risk_level or "normal"
    risk_color = risk_colors.get(risk_level, COLOR_DARK)

    elements.append(Paragraph("General Analysis", style_section))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_LINE, spaceAfter=8))

    risk_label = risk_level.replace("_", " ").upper()
    risk_style = ParagraphStyle("RiskLevel", parent=style_body, textColor=risk_color, fontSize=11)
    elements.append(Paragraph(f"<b>Risk Level:</b> {risk_label}", risk_style))

    if general_report.biomarkers_analyzed:
        elements.append(Paragraph(
            f"<b>Biomarkers Analyzed:</b> {general_report.biomarkers_analyzed}",
            style_body
        ))

    # Summary
    summary = general_content.get("summary", "")
    if summary:
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("<b>Summary</b>", style_subsection))
        # Split long text into paragraphs for readability
        for para in summary.split("\n"):
            para = para.strip()
            if para:
                elements.append(Paragraph(_escape_xml(para), style_body))

    # Key Findings
    findings = general_content.get("findings", [])
    if findings:
        elements.append(Paragraph("<b>Key Findings</b>", style_subsection))
        for finding in findings:
            if isinstance(finding, dict):
                text = finding.get("finding", finding.get("text", str(finding)))
            else:
                text = str(finding)
            elements.append(Paragraph(f"\u2022  {_escape_xml(text)}", style_bullet))

    # Recommendations
    recommendations = general_content.get("recommendations", [])
    if recommendations:
        elements.append(Paragraph("<b>Recommendations</b>", style_subsection))
        for rec in recommendations:
            if isinstance(rec, dict):
                text = rec.get("recommendation", rec.get("text", str(rec)))
            else:
                text = str(rec)
            elements.append(Paragraph(f"\u2022  {_escape_xml(text)}", style_bullet))

    # --- Specialist Reports ---
    if specialist_reports:
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Specialist Reports", style_section))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_LINE, spaceAfter=8))

        for spec_report in specialist_reports:
            spec_content = get_report_content(spec_report, current_user.id)
            spec_risk = spec_report.risk_level or "normal"
            spec_risk_color = risk_colors.get(spec_risk, COLOR_DARK)

            # Specialist heading with risk badge
            spec_title = spec_report.title or spec_report.report_type.replace("_", " ").title()
            spec_risk_label = spec_risk.replace("_", " ").upper()

            heading_style = ParagraphStyle("SpecHead", parent=style_subsection, fontSize=12, spaceBefore=12)
            elements.append(Paragraph(f"<b>{_escape_xml(spec_title)}</b>", heading_style))

            spec_risk_style = ParagraphStyle("SpecRisk", parent=style_label, textColor=spec_risk_color)
            elements.append(Paragraph(f"Risk: {spec_risk_label}", spec_risk_style))

            # Summary
            spec_summary = spec_content.get("summary", "")
            if spec_summary:
                for para in spec_summary.split("\n"):
                    para = para.strip()
                    if para:
                        elements.append(Paragraph(_escape_xml(para), style_body))

            # Findings
            spec_findings = spec_content.get("findings", [])
            if spec_findings:
                elements.append(Paragraph("<i>Findings:</i>", style_label))
                for finding in spec_findings:
                    if isinstance(finding, dict):
                        text = finding.get("finding", finding.get("text", str(finding)))
                    else:
                        text = str(finding)
                    elements.append(Paragraph(f"\u2022  {_escape_xml(text)}", style_bullet))

            # Recommendations
            spec_recs = spec_content.get("recommendations", [])
            if spec_recs:
                elements.append(Paragraph("<i>Recommendations:</i>", style_label))
                for rec in spec_recs:
                    if isinstance(rec, dict):
                        text = rec.get("recommendation", rec.get("text", str(rec)))
                    else:
                        text = str(rec)
                    elements.append(Paragraph(f"\u2022  {_escape_xml(text)}", style_bullet))

            elements.append(Spacer(1, 4))

    # --- Disclaimer ---
    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_LINE, spaceAfter=6))
    elements.append(Paragraph(
        "DISCLAIMER: This report is generated by an AI-based health analysis system and is intended "
        "for informational purposes only. It does not constitute medical advice, diagnosis, or treatment. "
        "Always consult a qualified healthcare professional for medical decisions. "
        "The analysis is based on the biomarkers available in your account at the time of generation.",
        style_disclaimer
    ))
    elements.append(Paragraph(
        f"Generated by analize.online on {report_date}.",
        style_disclaimer
    ))

    # Build the PDF
    doc.build(elements)
    buffer.seek(0)

    # Generate filename
    date_str = general_report.created_at.strftime("%Y-%m-%d") if general_report.created_at else datetime.now().strftime("%Y-%m-%d")
    filename = f"health_report_{date_str}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _escape_xml(text: str) -> str:
    """Escape special XML characters for ReportLab Paragraph markup."""
    if not text:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    # Also replace any stray quotes that might break attributes
    text = text.replace('"', "&quot;")
    return text
