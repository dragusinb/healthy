from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, timedelta, timezone

try:
    from backend_v2.database import get_db
    from backend_v2.models import User, Medication, MedicationLog
    from backend_v2.routers.documents import get_current_user
except ImportError:
    from database import get_db
    from models import User, Medication, MedicationLog
    from routers.documents import get_current_user


router = APIRouter(prefix="/medications", tags=["medications"])


class MedicationCreate(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: str = "daily"
    time_of_day: Optional[str] = None
    notes: Optional[str] = None
    source: str = "manual"


class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    time_of_day: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class MedicationLogCreate(BaseModel):
    medication_id: int
    time_slot: Optional[str] = None


@router.get("")
def list_medications(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's medications with today's adherence status."""
    query = db.query(Medication).filter(Medication.user_id == current_user.id)
    if active_only:
        query = query.filter(Medication.is_active == True)

    medications = query.order_by(Medication.created_at.desc()).all()
    today = date.today().isoformat()

    result = []
    for med in medications:
        # Check if taken today
        today_logs = [l for l in med.logs if l.date == today]

        result.append({
            "id": med.id,
            "name": med.name,
            "dosage": med.dosage,
            "frequency": med.frequency,
            "time_of_day": med.time_of_day,
            "notes": med.notes,
            "is_active": med.is_active,
            "source": med.source,
            "taken_today": len(today_logs) > 0,
            "today_logs": [{"id": l.id, "taken_at": l.taken_at.isoformat(), "time_slot": l.time_slot} for l in today_logs],
            "created_at": med.created_at.isoformat()
        })

    return result


@router.post("")
def create_medication(
    med: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new medication/supplement."""
    medication = Medication(
        user_id=current_user.id,
        name=med.name,
        dosage=med.dosage,
        frequency=med.frequency,
        time_of_day=med.time_of_day,
        notes=med.notes,
        source=med.source
    )
    db.add(medication)
    db.commit()
    db.refresh(medication)

    return {
        "id": medication.id,
        "name": medication.name,
        "dosage": medication.dosage,
        "frequency": medication.frequency,
        "time_of_day": medication.time_of_day,
        "notes": medication.notes,
        "is_active": medication.is_active,
        "source": medication.source,
        "taken_today": False,
        "today_logs": [],
        "created_at": medication.created_at.isoformat()
    }


@router.put("/{medication_id}")
def update_medication(
    medication_id: int,
    med: MedicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a medication."""
    medication = db.query(Medication).filter(
        Medication.id == medication_id,
        Medication.user_id == current_user.id
    ).first()

    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")

    for field, value in med.dict(exclude_unset=True).items():
        setattr(medication, field, value)

    db.commit()
    db.refresh(medication)

    return {"message": "Updated", "id": medication.id}


@router.delete("/{medication_id}")
def delete_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a medication and its logs."""
    medication = db.query(Medication).filter(
        Medication.id == medication_id,
        Medication.user_id == current_user.id
    ).first()

    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")

    db.delete(medication)
    db.commit()

    return {"message": "Deleted"}


@router.post("/log")
def log_medication_taken(
    log: MedicationLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log that a medication was taken."""
    medication = db.query(Medication).filter(
        Medication.id == log.medication_id,
        Medication.user_id == current_user.id
    ).first()

    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")

    today = date.today().isoformat()

    med_log = MedicationLog(
        medication_id=medication.id,
        user_id=current_user.id,
        date=today,
        time_slot=log.time_slot
    )
    db.add(med_log)
    db.commit()

    return {"message": "Logged", "date": today}


@router.delete("/log/{log_id}")
def undo_medication_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Undo a medication log entry."""
    log_entry = db.query(MedicationLog).filter(
        MedicationLog.id == log_id,
        MedicationLog.user_id == current_user.id
    ).first()

    if not log_entry:
        raise HTTPException(status_code=404, detail="Log not found")

    db.delete(log_entry)
    db.commit()

    return {"message": "Undone"}


@router.get("/adherence")
def get_adherence_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get medication adherence statistics."""
    start_date = (date.today() - timedelta(days=days)).isoformat()
    today = date.today().isoformat()

    # Get active medications
    medications = db.query(Medication).filter(
        Medication.user_id == current_user.id,
        Medication.is_active == True
    ).all()

    if not medications:
        return {"streak": 0, "adherence_pct": 0, "total_meds": 0, "daily_data": []}

    # Get logs for the period
    logs = db.query(MedicationLog).filter(
        MedicationLog.user_id == current_user.id,
        MedicationLog.date >= start_date,
        MedicationLog.date <= today
    ).all()

    # Group logs by date
    logs_by_date = {}
    for log in logs:
        if log.date not in logs_by_date:
            logs_by_date[log.date] = set()
        logs_by_date[log.date].add(log.medication_id)

    # Calculate streak (consecutive days all meds taken)
    streak = 0
    check_date = date.today()
    med_ids = {m.id for m in medications}

    while True:
        date_str = check_date.isoformat()
        taken = logs_by_date.get(date_str, set())
        if med_ids.issubset(taken):
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
        if streak > days:
            break

    # Calculate overall adherence
    total_expected = len(medications) * days
    total_taken = len(logs)
    adherence_pct = round((total_taken / total_expected) * 100) if total_expected > 0 else 0

    # Daily data for chart
    daily_data = []
    for i in range(min(days, 14)):
        d = date.today() - timedelta(days=i)
        d_str = d.isoformat()
        taken_count = len(logs_by_date.get(d_str, set()))
        daily_data.append({
            "date": d_str,
            "taken": taken_count,
            "total": len(medications),
            "complete": taken_count >= len(medications)
        })

    daily_data.reverse()

    return {
        "streak": streak,
        "adherence_pct": min(100, adherence_pct),
        "total_meds": len(medications),
        "daily_data": daily_data
    }
