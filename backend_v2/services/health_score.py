"""
Health Score Service
Calculates a 0-100 health score based on multiple factors.
"""
import json
import logging
from datetime import datetime, date, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def calculate_health_score(user, db, vault_helper=None) -> dict:
    """
    Calculate a health score for a user based on multiple components.

    Score components:
    - Biomarkers in range (40% weight)
    - Profile completeness (10% weight)
    - Screening compliance (20% weight)
    - Lifestyle adherence (15% weight)
    - Trend direction (15% weight)

    Returns dict with total score, component scores, and insights.
    """
    try:
        from models import Document, TestResult, HealthReport
    except ImportError:
        from backend_v2.models import Document, TestResult, HealthReport

    components = {}
    insights = []

    # --- 1. Biomarkers in Range (40%) ---
    results = db.query(TestResult).join(Document)\
        .filter(Document.user_id == user.id)\
        .all()

    if results:
        total = len(results)
        normal = sum(1 for r in results if r.flags == "NORMAL")
        pct = (normal / total) * 100 if total > 0 else 0
        components["biomarkers"] = {
            "score": round(pct),
            "weight": 40,
            "label": "Biomarkers in Range",
            "detail": f"{normal}/{total} in normal range"
        }
        if pct < 80:
            insights.append("biomarkers_attention")
        elif pct == 100:
            insights.append("biomarkers_perfect")
    else:
        components["biomarkers"] = {
            "score": 0,
            "weight": 40,
            "label": "Biomarkers in Range",
            "detail": "No biomarkers yet"
        }
        insights.append("no_biomarkers")

    # --- 2. Profile Completeness (10%) ---
    profile_fields = 0
    total_fields = 6  # name, dob, gender, height, weight, blood_type

    # Check encrypted fields first, then legacy
    has_name = False
    has_dob = False
    has_gender = False
    has_blood = False
    has_height = False
    has_weight = False

    if vault_helper and vault_helper.is_available:
        try:
            if user.full_name_enc:
                val = vault_helper.decrypt_data(user.full_name_enc)
                has_name = bool(val)
            if user.date_of_birth_enc:
                val = vault_helper.decrypt_data(user.date_of_birth_enc)
                has_dob = bool(val)
            if user.gender_enc:
                val = vault_helper.decrypt_data(user.gender_enc)
                has_gender = bool(val)
            if user.blood_type_enc:
                val = vault_helper.decrypt_data(user.blood_type_enc)
                has_blood = bool(val)
            if user.profile_data_enc:
                data = json.loads(vault_helper.decrypt_data(user.profile_data_enc))
                has_height = bool(data.get("height_cm"))
                has_weight = bool(data.get("weight_kg"))
        except Exception:
            pass

    # Fallback to legacy
    if not has_name: has_name = bool(user.full_name)
    if not has_dob: has_dob = bool(user.date_of_birth)
    if not has_gender: has_gender = bool(user.gender)
    if not has_blood: has_blood = bool(user.blood_type)
    if not has_height: has_height = bool(user.height_cm)
    if not has_weight: has_weight = bool(user.weight_kg)

    profile_fields = sum([has_name, has_dob, has_gender, has_blood, has_height, has_weight])
    profile_pct = (profile_fields / total_fields) * 100
    components["profile"] = {
        "score": round(profile_pct),
        "weight": 10,
        "label": "Profile Completeness",
        "detail": f"{profile_fields}/{total_fields} fields completed"
    }
    if profile_pct < 100:
        insights.append("incomplete_profile")

    # --- 3. Screening Compliance (20%) ---
    gap_report = db.query(HealthReport)\
        .filter(HealthReport.user_id == user.id, HealthReport.report_type == "gap_analysis")\
        .order_by(HealthReport.created_at.desc())\
        .first()

    screening_score = 50  # Default if no gap analysis
    if gap_report:
        content = None
        if vault_helper and vault_helper.is_available and gap_report.content_enc:
            try:
                content = json.loads(vault_helper.decrypt_data(gap_report.content_enc))
            except Exception:
                pass

        if content:
            tests = content.get("recommended_tests", [])
            if tests:
                overdue = sum(1 for t in tests if t.get("is_overdue"))
                up_to_date = len(tests) - overdue
                screening_score = round((up_to_date / len(tests)) * 100) if tests else 100
            else:
                screening_score = 100

    components["screening"] = {
        "score": screening_score,
        "weight": 20,
        "label": "Screening Compliance",
        "detail": f"{screening_score}% up to date"
    }
    if screening_score < 60:
        insights.append("overdue_screenings")

    # --- 4. Lifestyle Adherence (15%) ---
    lifestyle_score = 50  # Neutral default
    lifestyle_fields = 0
    total_lifestyle = 3  # smoking, alcohol, activity

    if user.smoking_status:
        lifestyle_fields += 1
        if user.smoking_status == "never":
            lifestyle_score += 10
        elif user.smoking_status == "former":
            lifestyle_score += 5
        elif user.smoking_status == "current":
            lifestyle_score -= 15

    if user.alcohol_consumption:
        lifestyle_fields += 1
        if user.alcohol_consumption in ("none", "occasional"):
            lifestyle_score += 10
        elif user.alcohol_consumption == "heavy":
            lifestyle_score -= 10

    if user.physical_activity:
        lifestyle_fields += 1
        activity_scores = {"sedentary": -10, "light": 0, "moderate": 10, "active": 15, "very_active": 15}
        lifestyle_score += activity_scores.get(user.physical_activity, 0)

    lifestyle_score = max(0, min(100, lifestyle_score))

    components["lifestyle"] = {
        "score": lifestyle_score,
        "weight": 15,
        "label": "Lifestyle Factors",
        "detail": f"{lifestyle_fields}/{total_lifestyle} factors tracked"
    }

    # --- 5. Trend Direction (15%) ---
    # Compare latest biomarkers with previous ones
    trend_score = 50  # Neutral

    # Get unique biomarkers with at least 2 data points
    from collections import defaultdict
    biomarker_history = defaultdict(list)

    all_results = db.query(TestResult).join(Document)\
        .filter(Document.user_id == user.id)\
        .order_by(Document.document_date.asc())\
        .all()

    for r in all_results:
        key = r.canonical_name or r.test_name
        biomarker_history[key].append(r.flags)

    improving = 0
    worsening = 0
    stable = 0
    for key, flags in biomarker_history.items():
        if len(flags) >= 2:
            prev = flags[-2]
            current = flags[-1]
            if prev != "NORMAL" and current == "NORMAL":
                improving += 1
            elif prev == "NORMAL" and current != "NORMAL":
                worsening += 1
            else:
                stable += 1

    total_tracked = improving + worsening + stable
    if total_tracked > 0:
        trend_score = round(((improving + stable * 0.7) / total_tracked) * 100)
        trend_score = max(0, min(100, trend_score))

    components["trends"] = {
        "score": trend_score,
        "weight": 15,
        "label": "Health Trends",
        "detail": f"{improving} improving, {worsening} worsening, {stable} stable"
    }
    if worsening > improving:
        insights.append("declining_trends")
    elif improving > 0:
        insights.append("improving_trends")

    # --- Calculate Total ---
    total_score = 0
    for comp in components.values():
        total_score += comp["score"] * (comp["weight"] / 100)

    total_score = round(max(0, min(100, total_score)))

    # Determine grade
    if total_score >= 90:
        grade = "excellent"
    elif total_score >= 75:
        grade = "good"
    elif total_score >= 60:
        grade = "fair"
    elif total_score >= 40:
        grade = "needs_attention"
    else:
        grade = "critical"

    return {
        "score": total_score,
        "grade": grade,
        "components": components,
        "insights": insights,
        "has_data": bool(results)
    }
