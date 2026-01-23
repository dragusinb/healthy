from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, Document, TestResult
    from backend_v2.routers.documents import get_current_user
except ImportError:
    from database import get_db
    from models import User, Document, TestResult
    from routers.documents import get_current_user

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
    # Find all results for this biomarker name across all user's documents
    results = db.query(TestResult).join(Document)\
        .filter(Document.user_id == current_user.id)\
        .filter(TestResult.test_name.ilike(f"%{biomarker_name}%"))\
        .order_by(Document.document_date)\
        .all()
        
    data_points = []
    for r in results:
        date_label = r.document.document_date.strftime("%Y-%m-%d") if r.document.document_date else "Unknown Date"
        data_points.append({
            "date": date_label,
            "value": r.numeric_value,
            "unit": r.unit,
            "ref_range": r.reference_range,
            "flags": r.flags
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
        biomarkers.append({
            "id": r.id,
            "name": r.test_name,
            "value": r.numeric_value if r.numeric_value is not None else r.value,
            "unit": r.unit,
            "range": r.reference_range,
            "date": r.document.document_date.strftime("%Y-%m-%d") if r.document.document_date else "Unknown",
            "provider": r.document.provider,
            "status": "normal" if r.flags == "NORMAL" else ("low" if r.flags == "LOW" else "high"),
            "document_id": r.document_id
        })

    return biomarkers


@router.get("/recent-biomarkers")
def get_recent_biomarkers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), limit: int = 5):
    """Get most recent unique biomarkers for dashboard display."""
    # Get distinct test names with their most recent result
    results = db.query(TestResult).join(Document)\
        .filter(Document.user_id == current_user.id)\
        .order_by(Document.document_date.desc())\
        .limit(100).all()

    # Get unique biomarkers (most recent of each)
    seen = set()
    recent = []
    for r in results:
        if r.test_name not in seen and len(recent) < limit:
            seen.add(r.test_name)
            recent.append({
                "name": r.test_name,
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
