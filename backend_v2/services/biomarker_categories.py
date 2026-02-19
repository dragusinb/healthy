"""
Biomarker category definitions and utilities.
Mirrors the frontend CATEGORIES for consistent categorization.
"""

BIOMARKER_CATEGORIES = {
    "hematology": {
        "name": "Blood & Hematology",
        "keywords": [
            "hemoglobin", "hematocrit", "rbc", "wbc", "platelets", "mcv", "mch",
            "mchc", "rdw", "reticulocytes", "leucocite", "eritrocite", "trombocite",
            "hematies", "vsh", "esr", "neutrofil", "limfocit", "monocit", "eozinofil",
            "bazofil", "htc", "hgb"
        ]
    },
    "lipids": {
        "name": "Lipid Profile",
        "keywords": [
            "cholesterol", "colesterol", "ldl", "hdl", "triglycerides",
            "trigliceride", "lipoprotein", "apolipoprotein", "lipid"
        ]
    },
    "liver": {
        "name": "Liver Function",
        "keywords": [
            "alt", "ast", "alp", "ggt", "bilirubin", "bilirubina", "albumin",
            "albumina", "tgp", "tgo", "gama", "hepat", "ficat"
        ]
    },
    "kidney": {
        "name": "Kidney Function",
        "keywords": [
            "creatinin", "creatinine", "bun", "urea", "egfr", "cystatin",
            "uric", "acid uric", "rinichi", "renal"
        ]
    },
    "metabolic": {
        "name": "Metabolic & Diabetes",
        "keywords": [
            "glucose", "glucoza", "glicemie", "hba1c", "hemoglobina glicata",
            "insulin", "insulina", "glyc"
        ]
    },
    "thyroid": {
        "name": "Thyroid",
        "keywords": ["tsh", "t3", "t4", "ft3", "ft4", "tiroid", "thyroid"]
    },
    "vitamins": {
        "name": "Vitamins & Minerals",
        "keywords": [
            "vitamin", "vitamina", "fier", "iron", "ferritin", "feritina",
            "zinc", "magneziu", "magnesium", "calciu", "calcium", "potasiu",
            "potassium", "sodiu", "sodium", "fosfor", "b12", "d3", "folat", "folic"
        ]
    },
    "other": {
        "name": "Other Tests",
        "keywords": []
    }
}


def get_category_keywords(category: str) -> list:
    """Get keywords for a specific category.

    Args:
        category: Category key (e.g., 'hematology', 'lipids')

    Returns:
        List of keywords for matching biomarkers
    """
    cat = BIOMARKER_CATEGORIES.get(category.lower())
    if cat:
        return cat["keywords"]
    return []


def get_all_categories() -> list:
    """Get list of all valid category keys."""
    return list(BIOMARKER_CATEGORIES.keys())


def categorize_biomarker(biomarker_name: str) -> str:
    """Categorize a biomarker by its name.

    Args:
        biomarker_name: The biomarker name to categorize

    Returns:
        Category key (e.g., 'hematology', 'lipids', 'other')
    """
    name_lower = biomarker_name.lower()
    for cat_key, cat_data in BIOMARKER_CATEGORIES.items():
        if cat_key == "other":
            continue
        if any(kw in name_lower for kw in cat_data["keywords"]):
            return cat_key
    return "other"
