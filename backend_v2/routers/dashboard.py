from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, date

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, Document, TestResult, HealthReport
    from backend_v2.routers.documents import get_current_user
    from backend_v2.services.biomarker_normalizer import (
        normalize_biomarker_name, get_canonical_name, group_biomarkers
    )
    from backend_v2.services.vault import vault
except ImportError:
    from database import get_db
    from models import User, Document, TestResult, HealthReport
    from routers.documents import get_current_user
    from services.biomarker_normalizer import (
        normalize_biomarker_name, get_canonical_name, group_biomarkers
    )
    from services.vault import vault


def get_biomarker_value(result: TestResult) -> tuple:
    """
    Get biomarker value and numeric_value, preferring vault-encrypted if available.
    Returns (value, numeric_value)
    """
    value = None
    numeric_value = None

    if vault.is_unlocked:
        try:
            if result.value_enc:
                value = vault.decrypt_data(result.value_enc)
            if result.numeric_value_enc:
                numeric_value = vault.decrypt_number(result.numeric_value_enc)
        except Exception:
            pass  # Fall back to legacy

    # Fall back to legacy unencrypted fields
    if value is None:
        value = result.value
    if numeric_value is None:
        numeric_value = result.numeric_value

    return value, numeric_value

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc_count = len(current_user.documents)

    # Count unique biomarkers by canonical name (not total records)
    # This matches what's shown on the Biomarkers page
    results = db.query(TestResult).join(Document)\
        .filter(Document.user_id == current_user.id)\
        .all()

    unique_biomarkers = set()
    for r in results:
        # Use stored canonical_name if available, fallback to runtime normalization
        if r.canonical_name:
            unique_biomarkers.add(r.canonical_name)
        else:
            canonical, _ = normalize_biomarker_name(r.test_name)
            unique_biomarkers.add(canonical)

    return {
        "documents_count": doc_count,
        "biomarkers_count": len(unique_biomarkers),
    }

@router.get("/evolution/{biomarker_name}")
def get_evolution(biomarker_name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get evolution data for a biomarker.
    Uses normalized names to group related test variants together.
    """
    # Get the canonical name for the requested biomarker
    canonical_name = get_canonical_name(biomarker_name)

    # Get all results for this user
    all_results = db.query(TestResult).join(Document)\
        .filter(Document.user_id == current_user.id)\
        .order_by(Document.document_date)\
        .all()

    # Filter to results that match the canonical name
    # Use strict matching to avoid grouping unrelated biomarkers
    data_points = []
    search_lower = biomarker_name.lower().strip()

    for r in all_results:
        result_canonical = get_canonical_name(r.test_name)
        test_name_lower = r.test_name.lower().strip()

        # Match criteria (strict):
        # 1. Canonical names match exactly
        # 2. Original test name matches the search term exactly (case-insensitive)
        # 3. Stored canonical_name matches the search canonical name
        is_match = (
            result_canonical == canonical_name or
            test_name_lower == search_lower or
            (r.canonical_name and r.canonical_name.lower() == canonical_name.lower())
        )

        if is_match:
            date_label = r.document.document_date.strftime("%Y-%m-%d") if r.document.document_date else "Unknown Date"
            value, numeric_value = get_biomarker_value(r)
            data_points.append({
                "date": date_label,
                "value": numeric_value,
                "unit": r.unit,
                "ref_range": r.reference_range,
                "flags": r.flags,
                "original_name": r.test_name,
                "provider": r.document.provider
            })

    return data_points

@router.get("/biomarkers")
def get_all_biomarkers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), filter_out_of_range: bool = False):
    query = db.query(TestResult).join(Document)\
        .filter(Document.user_id == current_user.id)

    if filter_out_of_range:
        query = query.filter(TestResult.flags != 'NORMAL')

    results = query.order_by(Document.document_date.desc()).all()

    biomarkers = []
    for r in results:
        # Use stored canonical_name if available, fallback to runtime normalization
        if r.canonical_name:
            canonical_name = r.canonical_name
        else:
            canonical_name, _ = normalize_biomarker_name(r.test_name)
        value, numeric_value = get_biomarker_value(r)
        biomarkers.append({
            "id": r.id,
            "name": r.test_name,
            "normalized_name": canonical_name,
            "value": numeric_value if numeric_value is not None else value,
            "unit": r.unit,
            "range": r.reference_range,
            "date": r.document.document_date.strftime("%Y-%m-%d") if r.document.document_date else "Unknown",
            "provider": r.document.provider,
            "status": "normal" if r.flags == "NORMAL" else ("low" if r.flags == "LOW" else "high"),
            "document_id": r.document_id
        })

    return biomarkers


@router.get("/biomarkers-grouped")
def get_grouped_biomarkers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    filter_out_of_range: bool = False
):
    """
    Get biomarkers grouped by normalized/canonical name.
    Each group contains all historical results for that biomarker.
    """
    query = db.query(TestResult).join(Document)\
        .filter(Document.user_id == current_user.id)

    if filter_out_of_range:
        query = query.filter(TestResult.flags != 'NORMAL')

    results = query.order_by(Document.document_date.desc()).all()

    # Build flat list first
    biomarkers = []
    for r in results:
        # Use stored canonical_name if available, fallback to runtime normalization
        if r.canonical_name:
            canonical_name = r.canonical_name
        else:
            canonical_name, _ = normalize_biomarker_name(r.test_name)
        value, numeric_value = get_biomarker_value(r)
        biomarkers.append({
            "id": r.id,
            "name": r.test_name,
            "normalized_name": canonical_name,
            "value": numeric_value if numeric_value is not None else value,
            "unit": r.unit,
            "range": r.reference_range,
            "date": r.document.document_date.strftime("%Y-%m-%d") if r.document.document_date else "Unknown",
            "provider": r.document.provider,
            "status": "normal" if r.flags == "NORMAL" else ("low" if r.flags == "LOW" else "high"),
            "document_id": r.document_id
        })

    # Group by normalized name
    groups = {}
    for bio in biomarkers:
        key = bio["normalized_name"]
        if key not in groups:
            groups[key] = {
                "canonical_name": key,
                "latest": None,
                "history": [],
                "has_issues": False,
                "latest_date": None
            }

        groups[key]["history"].append(bio)

        # Track if any result has issues
        if bio["status"] != "normal":
            groups[key]["has_issues"] = True

        # Set the latest result (first one since sorted by date desc)
        if groups[key]["latest"] is None:
            groups[key]["latest"] = bio
            groups[key]["latest_date"] = bio["date"]

    # Convert to list and sort by issues first, then by date
    result = list(groups.values())
    result.sort(key=lambda x: (0 if x["has_issues"] else 1, x["latest_date"] or ""), reverse=False)
    # Re-sort: issues first, then most recent
    result.sort(key=lambda x: (0 if x["has_issues"] else 1, x["latest_date"] or "0000"), reverse=True)

    return result


@router.get("/recent-biomarkers")
def get_recent_biomarkers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), limit: int = 5):
    """Get most recent unique biomarkers for dashboard display (using normalized names)."""
    # Get distinct test names with their most recent result
    results = db.query(TestResult).join(Document)\
        .filter(Document.user_id == current_user.id)\
        .order_by(Document.document_date.desc())\
        .limit(100).all()

    # Get unique biomarkers by normalized name (most recent of each)
    seen_normalized = set()
    recent = []
    for r in results:
        canonical_name = get_canonical_name(r.test_name)
        if canonical_name not in seen_normalized and len(recent) < limit:
            seen_normalized.add(canonical_name)
            value, numeric_value = get_biomarker_value(r)
            display_value = numeric_value if numeric_value else value
            recent.append({
                "name": canonical_name,
                "original_name": r.test_name,
                "lastValue": f"{display_value} {r.unit or ''}".strip(),
                "status": "normal" if r.flags == "NORMAL" else ("low" if r.flags == "LOW" else "high"),
                "date": r.document.document_date.strftime("%b %d") if r.document.document_date else "Unknown"
            })

    return recent


@router.get("/alerts-count")
def get_alerts_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Count biomarkers that are out of normal range."""
    count = db.query(TestResult).join(Document)\
        .filter(Document.user_id == current_user.id)\
        .filter(TestResult.flags != 'NORMAL')\
        .count()
    return {"alerts_count": count}


@router.get("/patient-info")
def get_patient_info(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get information about patients found in user's documents.

    Groups patients by CNP prefix (first 7 digits of Romanian national ID) when available,
    falling back to name-based grouping. This correctly identifies same patients with
    different name formats (e.g., "Dragusin Bogdan" vs "Bogdan Dragusin").
    """
    # Get all documents with patient info
    docs_with_patient = db.query(
        Document.patient_name,
        Document.patient_cnp_prefix
    ).filter(
        Document.user_id == current_user.id
    ).all()

    # Group by CNP prefix (preferred) or name (fallback)
    # CNP prefix is the unique identifier; names may vary for same person
    patient_groups = {}  # key: cnp_prefix or name, value: {display_name, count, names_seen}

    for name, cnp_prefix in docs_with_patient:
        if cnp_prefix:
            # Group by CNP prefix
            key = f"cnp:{cnp_prefix}"
            if key not in patient_groups:
                patient_groups[key] = {
                    "display_name": name or "Unknown",
                    "count": 0,
                    "names_seen": set(),
                    "cnp_prefix": cnp_prefix
                }
            patient_groups[key]["count"] += 1
            if name:
                patient_groups[key]["names_seen"].add(name)
                # Prefer the most complete/longest name as display name
                if len(name) > len(patient_groups[key]["display_name"]):
                    patient_groups[key]["display_name"] = name
        elif name:
            # Fall back to name-based grouping (no CNP available)
            key = f"name:{name.lower().strip()}"
            if key not in patient_groups:
                patient_groups[key] = {
                    "display_name": name,
                    "count": 0,
                    "names_seen": {name},
                    "cnp_prefix": None
                }
            patient_groups[key]["count"] += 1
        # Documents without name or CNP are counted separately

    # Build response - use display names for user-facing list
    distinct_patients = [g["display_name"] for g in patient_groups.values()]
    patient_counts = {g["display_name"]: g["count"] for g in patient_groups.values()}

    # Total documents and documents without patient info
    total_docs = db.query(Document).filter(Document.user_id == current_user.id).count()
    unknown_patient_docs = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.patient_name.is_(None),
        Document.patient_cnp_prefix.is_(None)
    ).count()

    return {
        "distinct_patients": distinct_patients,
        "patient_count": len(patient_groups),
        "patient_documents": patient_counts,
        "total_documents": total_docs,
        "unknown_patient_documents": unknown_patient_docs,
        "multi_patient": len(patient_groups) > 1
    }


@router.get("/health-overview")
def get_health_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get a comprehensive health overview for the dashboard.
    Includes patient identity, tracking timeline, health status, and screening reminders.
    """
    # --- Patient Identity ---
    profile = {}
    try:
        # Try to get encrypted profile data first
        if vault.is_unlocked:
            if current_user.full_name_enc:
                profile["full_name"] = vault.decrypt_data(current_user.full_name_enc)
            if current_user.date_of_birth_enc:
                dob_str = vault.decrypt_data(current_user.date_of_birth_enc)
                if dob_str:
                    try:
                        dob = datetime.fromisoformat(dob_str.replace('Z', '+00:00'))
                        profile["date_of_birth"] = dob.date().isoformat()
                        # Calculate age
                        today = date.today()
                        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                        profile["age"] = age
                    except:
                        profile["date_of_birth"] = dob_str
            if current_user.gender_enc:
                profile["gender"] = vault.decrypt_data(current_user.gender_enc)
            if current_user.blood_type_enc:
                profile["blood_type"] = vault.decrypt_data(current_user.blood_type_enc)

        # Fallback to legacy unencrypted fields
        if not profile.get("full_name") and current_user.full_name:
            profile["full_name"] = current_user.full_name
        if not profile.get("date_of_birth") and current_user.date_of_birth:
            profile["date_of_birth"] = current_user.date_of_birth.isoformat() if hasattr(current_user.date_of_birth, 'isoformat') else str(current_user.date_of_birth)
            if not profile.get("age"):
                try:
                    dob = current_user.date_of_birth
                    if isinstance(dob, str):
                        dob = datetime.fromisoformat(dob.replace('Z', '+00:00')).date()
                    today = date.today()
                    profile["age"] = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                except:
                    pass
        # Fallback for gender and blood_type
        if not profile.get("gender") and current_user.gender:
            profile["gender"] = current_user.gender
        if not profile.get("blood_type") and current_user.blood_type:
            profile["blood_type"] = current_user.blood_type
    except Exception as e:
        pass  # Continue with partial data

    # --- Tracking Timeline ---
    timeline = {}

    # Get first and last document dates
    first_doc = db.query(Document.document_date)\
        .filter(Document.user_id == current_user.id, Document.document_date.isnot(None))\
        .order_by(Document.document_date.asc())\
        .first()

    last_doc = db.query(Document.document_date)\
        .filter(Document.user_id == current_user.id, Document.document_date.isnot(None))\
        .order_by(Document.document_date.desc())\
        .first()

    if first_doc and first_doc[0]:
        timeline["first_record_date"] = first_doc[0].isoformat()
        # Calculate tracking duration
        first_date = first_doc[0]
        if isinstance(first_date, datetime):
            first_date = first_date.date()
        days_tracking = (date.today() - first_date).days
        timeline["days_tracking"] = days_tracking
        if days_tracking >= 365:
            timeline["tracking_duration"] = f"{days_tracking // 365} years, {(days_tracking % 365) // 30} months"
        elif days_tracking >= 30:
            timeline["tracking_duration"] = f"{days_tracking // 30} months"
        else:
            timeline["tracking_duration"] = f"{days_tracking} days"

    if last_doc and last_doc[0]:
        timeline["last_record_date"] = last_doc[0].isoformat()

    # Last sync from linked accounts
    last_sync = None
    for acc in current_user.linked_accounts:
        if acc.last_sync:
            if last_sync is None or acc.last_sync > last_sync:
                last_sync = acc.last_sync
    if last_sync:
        timeline["last_sync"] = last_sync.isoformat()

    # Document count
    timeline["total_documents"] = db.query(Document).filter(Document.user_id == current_user.id).count()

    # --- Health Status ---
    health_status = {}

    # Get latest health report
    latest_report = db.query(HealthReport)\
        .filter(HealthReport.user_id == current_user.id, HealthReport.report_type == "general")\
        .order_by(HealthReport.created_at.desc())\
        .first()

    if latest_report:
        health_status["has_analysis"] = True
        health_status["last_analysis_date"] = latest_report.created_at.isoformat()

        # Decrypt report content for risk level
        if vault.is_unlocked and latest_report.content_enc:
            try:
                import json
                content = json.loads(vault.decrypt_data(latest_report.content_enc))
                health_status["risk_level"] = content.get("risk_level", "unknown")
            except:
                health_status["risk_level"] = "unknown"
        else:
            health_status["risk_level"] = "unknown"

        # Days since last analysis
        last_analysis = latest_report.created_at
        if isinstance(last_analysis, datetime):
            days_since = (datetime.now() - last_analysis).days
            health_status["days_since_analysis"] = days_since
    else:
        health_status["has_analysis"] = False

    # Alerts count (out of range biomarkers)
    alerts_count = db.query(TestResult).join(Document)\
        .filter(Document.user_id == current_user.id)\
        .filter(TestResult.flags != 'NORMAL')\
        .count()
    health_status["alerts_count"] = alerts_count

    # Unique biomarkers count
    results = db.query(TestResult).join(Document)\
        .filter(Document.user_id == current_user.id)\
        .all()
    unique_biomarkers = set()
    for r in results:
        if r.canonical_name:
            unique_biomarkers.add(r.canonical_name)
        else:
            canonical, _ = normalize_biomarker_name(r.test_name)
            unique_biomarkers.add(canonical)
    health_status["biomarkers_tracked"] = len(unique_biomarkers)

    # --- Screening Reminders ---
    reminders = []

    # Get latest gap analysis
    gap_analysis = db.query(HealthReport)\
        .filter(HealthReport.user_id == current_user.id, HealthReport.report_type == "gap_analysis")\
        .order_by(HealthReport.created_at.desc())\
        .first()

    if gap_analysis and vault.is_unlocked and gap_analysis.content_enc:
        try:
            import json
            content = json.loads(vault.decrypt_data(gap_analysis.content_enc))
            recommended = content.get("recommended_tests", [])
            for test in recommended:
                if test.get("is_overdue"):
                    reminders.append({
                        "test_name": test.get("test_name"),
                        "priority": test.get("priority", "medium"),
                        "months_overdue": test.get("months_since_last", 0) - test.get("recommended_interval_months", 12),
                        "reason": test.get("reason", "")
                    })
        except:
            pass

    # --- Latest AI Summary ---
    ai_summary = None
    if latest_report and vault.is_unlocked and latest_report.content_enc:
        try:
            import json
            content = json.loads(vault.decrypt_data(latest_report.content_enc))
            ai_summary = content.get("summary", "")
        except:
            pass
    # Fallback to legacy unencrypted field
    if not ai_summary and latest_report and latest_report.summary:
        ai_summary = latest_report.summary

    return {
        "profile": profile,
        "timeline": timeline,
        "health_status": health_status,
        "reminders": reminders[:5],  # Top 5 overdue
        "reminders_count": len(reminders),
        "ai_summary": ai_summary,  # Full AI doctor summary
        "profile_complete": bool(profile.get("full_name") and profile.get("date_of_birth") and profile.get("gender"))
    }
