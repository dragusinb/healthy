from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db, engine, Base
from backend.models import Document, TestResult, Provider
from backend.data.biomarkers import get_biomarker_info

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Healthy - Medical Records Analyzer")

origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow ALL temporarily for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Healthy Backend API is running"}

@app.get("/documents")
def get_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.document_date.desc()).all()
    # Serialize manually or use Pydantic (keeping it simple for now)
    return [{
        "id": d.id,
        "filename": d.filename,
        "date": d.document_date.isoformat() if d.document_date else None,
        "provider": d.provider.name if d.provider else "Unknown",
        "category": d.category
    } for d in docs]

from fastapi.responses import FileResponse
import os

@app.get("/documents/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return {"error": "Document not found"}
    
    if not os.path.exists(doc.file_path):
        return {"error": "File not found on server"}
    
    return FileResponse(doc.file_path, filename=doc.filename, media_type='application/pdf')

@app.get("/documents/{doc_id}")
def get_document_details(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return {"error": "Document not found"}
    
    results = db.query(TestResult).filter(TestResult.document_id == doc_id).all()
    
    return {
        "id": doc.id,
        "filename": doc.filename,
        "date": doc.document_date.isoformat() if doc.document_date else None,
        "provider": doc.provider.name if doc.provider else "Unknown",
        "category": doc.category,
        "results": [{
            "id": r.id,
            "test_name": r.test_name,
            "value": r.value,
            "unit": r.unit,
            "reference_range": r.reference_range,
            "flags": r.flags,
            "category": r.category or "General"
        } for r in results]
    }

from backend.ai.interpreter import MedicalInterpreter

interpreter = MedicalInterpreter()

@app.get("/results")
def get_results(db: Session = Depends(get_db)):
    # Flatten results for timeline
    results = db.query(TestResult).join(Document).order_by(Document.document_date).all()
    return [{
        "id": r.id,
        "test_name": r.test_name,
        "value": r.value,
        "unit": r.unit,
        "date": r.document.document_date.isoformat(),
        "provider": r.document.provider.name,
        "flags": r.flags,
        "reference_range": r.reference_range,
        "category": r.category or "General"
    } for r in results]

@app.get("/insights")
def get_insights(db: Session = Depends(get_db)):
    results = db.query(TestResult).join(Document).order_by(Document.document_date).all()
    
    # Use standard TrendAnalyzer for consistency
    from backend.analysis.trends import TrendAnalyzer
    trends = TrendAnalyzer.calculate_trends(results)
    
    # Filter: Only show trends that need attention
    attention_trends = [t for t in trends if t.get("is_attention_needed")]
    
    # Simple logic to get latest doc summary
    latest_doc = db.query(Document).order_by(Document.document_date.desc()).first()
    summary = "No documents found."
    if latest_doc:
        doc_results = db.query(TestResult).filter(TestResult.document_id == latest_doc.id).all()
        summary = interpreter.summarize_latest(latest_doc, doc_results)
        
    return {
        "trends": attention_trends[:5], # Top 5 critical trends
        "latest_summary": summary
    }

@app.get("/biomarker-info")
def get_biomarker_details(name: str):
    info = get_biomarker_info(name)
    if not info:
        # Return empty structure rather than 404 to avoid frontend errors on unknown markers
        return {
            "display_name": name,
            "description": "No description available for this biomarker in our database yet.",
            "has_info": False
        }
    return {**info, "has_info": True}

@app.get("/analysis/summary")
def get_analysis_summary(db: Session = Depends(get_db)):
    # 1. Get all results sorted by date
    results = db.query(TestResult).join(Document).order_by(Document.document_date).all()
    
    # 2. Key Alerts (High/Low from latest sorted)
    # Get latest 100 results to scan for alerts
    latest_results = results[-100:] if len(results) > 100 else results
    alerts = []
    for r in latest_results:
        if r.flags in ["HIGH", "LOW"]:
            # Check if alert already exists for this test (dedup logic if needed, but simple list ok for now)
            alerts.append({
                "test_name": r.test_name,
                "value": r.value,
                "flag": r.flags,
                "date": r.document.document_date.isoformat(),
                "unit": r.unit
            })
    
    # User Rule: "ordered chronlogically, always newest first"
    # Parse date to ensure correct sorting, then reverse
    alerts.sort(key=lambda x: x["date"], reverse=True)

    # 3. Trends
    from backend.analysis.trends import TrendAnalyzer
    trends = TrendAnalyzer.calculate_trends(results)
    
    # 4. Global Counts
    counts = {
        "total_documents": db.query(Document).count(),
        "total_tests": len(results),
        "abnormal_findings": len([r for r in results if r.flags in ["HIGH", "LOW"]])
    }

    # 5. Doctor Advice
    from backend.analysis.advisor import MedicalAdvisor
    doctor_advice = MedicalAdvisor.generate_advice(alerts)

    return {
        "counts": counts,
        "alerts": alerts[:10], # Top 10 recent alerts
        "trends": trends[:5],   # Top 5 biggest changes
        "advice": doctor_advice
    }
