from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, Document, TestResult
    from backend_v2.routers.documents import get_current_user
    from backend_v2.services.biomarker_normalizer import (
        normalize_biomarker_name, get_canonical_name, group_biomarkers
    )
except ImportError:
    from database import get_db
    from models import User, Document, TestResult
    from routers.documents import get_current_user
    from services.biomarker_normalizer import (
        normalize_biomarker_name, get_canonical_name, group_biomarkers
    )

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc_count = len(current_user.documents)
    
    # Count biomarkers
    biomarker_count = 0
    for d in current_user.documents:
        biomarker_count += len(d.results)
        
    return {
        "documents_count": doc_count,
        "biomarkers_count": biomarker_count,
        # "alerts_count": ...
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
    data_points = []
    for r in all_results:
        result_canonical = get_canonical_name(r.test_name)

        # Match if canonical names are the same OR if original name contains the search term
        if (result_canonical == canonical_name or
            biomarker_name.lower() in r.test_name.lower() or
            r.test_name.lower() in biomarker_name.lower()):

            date_label = r.document.document_date.strftime("%Y-%m-%d") if r.document.document_date else "Unknown Date"
            data_points.append({
                "date": date_label,
                "value": r.numeric_value,
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
        biomarkers.append({
            "id": r.id,
            "name": r.test_name,
            "normalized_name": canonical_name,
            "value": r.numeric_value if r.numeric_value is not None else r.value,
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
        biomarkers.append({
            "id": r.id,
            "name": r.test_name,
            "normalized_name": canonical_name,
            "value": r.numeric_value if r.numeric_value is not None else r.value,
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
            recent.append({
                "name": canonical_name,
                "original_name": r.test_name,
                "lastValue": f"{r.numeric_value if r.numeric_value else r.value} {r.unit or ''}".strip(),
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
    """Get information about patients found in user's documents."""
    # Get distinct patient names from documents
    patient_names = db.query(Document.patient_name).filter(
        Document.user_id == current_user.id,
        Document.patient_name.isnot(None)
    ).distinct().all()

    distinct_patients = [name for (name,) in patient_names if name]

    # Count documents per patient
    patient_counts = {}
    for name in distinct_patients:
        count = db.query(Document).filter(
            Document.user_id == current_user.id,
            Document.patient_name == name
        ).count()
        patient_counts[name] = count

    # Total documents and documents without patient name
    total_docs = db.query(Document).filter(Document.user_id == current_user.id).count()
    unknown_patient_docs = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.patient_name.is_(None)
    ).count()

    return {
        "distinct_patients": distinct_patients,
        "patient_count": len(distinct_patients),
        "patient_documents": patient_counts,
        "total_documents": total_docs,
        "unknown_patient_documents": unknown_patient_docs,
        "multi_patient": len(distinct_patients) > 1
    }
