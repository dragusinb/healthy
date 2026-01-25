"""
Biomarker Name Normalization Service

Maps various test name variants to canonical names for grouping purposes.
Handles Romanian/English variations, abbreviations, and common naming differences.
"""

import re
from typing import Optional, Dict, List, Tuple

# Canonical name -> list of variants (case-insensitive matching)
# The canonical name is what will be displayed and used for grouping
BIOMARKER_MAPPINGS = {
    # Hematology
    "Hemoglobin": [
        "hemoglobin", "hemoglobina", "hemoglobină", "hgb", "hb"
    ],
    "Hematocrit": [
        "hematocrit", "htc", "ht", "hct"
    ],
    "Red Blood Cells (RBC)": [
        "eritrocite", "erythrocytes", "rbc", "red blood cells", "hematii", "hematies",
        "numar eritrocite", "eritrocite (rbc)"
    ],
    "White Blood Cells (WBC)": [
        "leucocite", "leukocytes", "wbc", "white blood cells", "numar leucocite",
        "leucocite (wbc)"
    ],
    "Platelets": [
        "trombocite", "platelets", "plt", "thrombocytes", "numar trombocite"
    ],
    "MCV": [
        "mcv", "volum eritrocitar mediu", "mean corpuscular volume"
    ],
    "MCH": [
        "mch", "hemoglobina eritrocitara medie", "mean corpuscular hemoglobin"
    ],
    "MCHC": [
        "mchc", "concentratie medie hemoglobina eritrocitara",
        "mean corpuscular hemoglobin concentration"
    ],
    "RDW": [
        "rdw", "rdw-cv", "rdw-sd", "red cell distribution width"
    ],
    "ESR": [
        "vsh", "esr", "viteza de sedimentare", "erythrocyte sedimentation rate",
        "sed rate"
    ],
    "Neutrophils": [
        "neutrofil", "neutrophils", "neut", "neutrofile"
    ],
    "Lymphocytes": [
        "limfocit", "lymphocytes", "lym", "limfocite"
    ],
    "Monocytes": [
        "monocit", "monocytes", "mono", "monocite"
    ],
    "Eosinophils": [
        "eozinofil", "eosinophils", "eos", "eozinofile"
    ],
    "Basophils": [
        "bazofil", "basophils", "baso", "bazofile"
    ],
    "Reticulocytes": [
        "reticulocit", "reticulocytes", "retic"
    ],

    # Lipid Panel
    "Total Cholesterol": [
        "colesterol total", "cholesterol total", "cholesterol", "colesterol"
    ],
    "HDL Cholesterol": [
        "hdl", "hdl-c", "hdl colesterol", "hdl cholesterol", "colesterol hdl"
    ],
    "LDL Cholesterol": [
        "ldl", "ldl-c", "ldl colesterol", "ldl cholesterol", "colesterol ldl"
    ],
    "Triglycerides": [
        "trigliceride", "triglycerides", "tg", "triglycérides"
    ],
    "VLDL Cholesterol": [
        "vldl", "vldl-c", "vldl colesterol"
    ],

    # Liver Function
    "ALT (TGP)": [
        "alt", "tgp", "alanine aminotransferase", "alat", "sgpt"
    ],
    "AST (TGO)": [
        "ast", "tgo", "aspartate aminotransferase", "asat", "sgot"
    ],
    "GGT": [
        "ggt", "gamma gt", "gamma-gt", "gama gt", "gamma glutamyl transferase"
    ],
    "Alkaline Phosphatase": [
        "fosfataza alcalina", "alkaline phosphatase", "alp", "alk phos"
    ],
    "Total Bilirubin": [
        "bilirubina totala", "bilirubin total", "total bilirubin", "bilirubina"
    ],
    "Direct Bilirubin": [
        "bilirubina directa", "direct bilirubin", "conjugated bilirubin"
    ],
    "Indirect Bilirubin": [
        "bilirubina indirecta", "indirect bilirubin", "unconjugated bilirubin"
    ],
    "Albumin": [
        "albumina", "albumin", "alb"
    ],
    "Total Protein": [
        "proteine totale", "total protein", "serum protein"
    ],

    # Kidney Function
    "Creatinine": [
        "creatinina", "creatinine", "creat", "creatinina serica", "serum creatinine"
    ],
    "Urea": [
        "uree", "urea", "uree serica", "blood urea", "bun"
    ],
    "eGFR": [
        "egfr", "rata filtrare glomerulara", "glomerular filtration rate", "gfr"
    ],
    "Uric Acid": [
        "acid uric", "uric acid", "acidum uricum"
    ],
    "Cystatin C": [
        "cistatina c", "cystatin c", "cystatin"
    ],

    # Metabolic / Glucose
    "Glucose": [
        "glucoza", "glucose", "glicemie", "glucoza serica", "serum glucose",
        "blood sugar", "zahar din sange"
    ],
    "Fasting Glucose": [
        "glucoza a jeun", "fasting glucose", "glicemie a jeun", "glucoza bazala"
    ],
    "HbA1c": [
        "hba1c", "hemoglobina glicata", "glycated hemoglobin", "a1c",
        "hemoglobina glicozilata"
    ],
    "Insulin": [
        "insulina", "insulin", "insulina serica"
    ],
    "HOMA-IR": [
        "homa-ir", "homa", "homeostatic model assessment"
    ],

    # Thyroid
    "TSH": [
        "tsh", "thyroid stimulating hormone", "tirotropina"
    ],
    "Free T4": [
        "ft4", "t4 liber", "free t4", "free thyroxine", "t4l"
    ],
    "Free T3": [
        "ft3", "t3 liber", "free t3", "free triiodothyronine", "t3l"
    ],
    "Total T4": [
        "t4 total", "total t4", "thyroxine"
    ],
    "Total T3": [
        "t3 total", "total t3", "triiodothyronine"
    ],
    "Anti-TPO": [
        "anti-tpo", "atpo", "tpo antibodies", "anticorpi anti-tpo"
    ],
    "Anti-TG": [
        "anti-tg", "atg", "thyroglobulin antibodies", "anticorpi anti-tiroglobulina"
    ],

    # Vitamins & Minerals
    "Vitamin D": [
        "vitamina d", "vitamin d", "25-oh vitamina d", "25-hidroxi vitamina d",
        "d3", "vitamina d3", "cholecalciferol"
    ],
    "Vitamin B12": [
        "vitamina b12", "vitamin b12", "b12", "cobalamina", "cobalamin"
    ],
    "Folate": [
        "acid folic", "folate", "folic acid", "vitamina b9"
    ],
    "Iron": [
        "fier", "iron", "sideremie", "fier seric", "serum iron"
    ],
    "Ferritin": [
        "feritina", "ferritin", "feritină"
    ],
    "TIBC": [
        "tibc", "capacitate totala de legare a fierului",
        "total iron binding capacity"
    ],
    "Transferrin Saturation": [
        "saturatie transferina", "transferrin saturation", "tsat"
    ],
    "Calcium": [
        "calciu", "calcium", "ca", "calciu seric", "calciu total"
    ],
    "Magnesium": [
        "magneziu", "magnesium", "mg", "magneziu seric"
    ],
    "Potassium": [
        "potasiu", "potassium", "k", "kaliu"
    ],
    "Sodium": [
        "sodiu", "sodium", "na", "natriu"
    ],
    "Phosphorus": [
        "fosfor", "phosphorus", "p", "fosfat"
    ],
    "Zinc": [
        "zinc", "zn"
    ],

    # Cardiac Markers
    "CRP": [
        "crp", "proteina c reactiva", "c-reactive protein", "pcr"
    ],
    "hs-CRP": [
        "hs-crp", "crp inalt sensibil", "high sensitivity crp"
    ],
    "Homocysteine": [
        "homocisteina", "homocysteine", "hcy"
    ],
    "BNP": [
        "bnp", "brain natriuretic peptide", "peptida natriuretica"
    ],
    "NT-proBNP": [
        "nt-probnp", "proBNP"
    ],
    "Troponin": [
        "troponina", "troponin", "troponina i", "troponin i"
    ],
    "D-Dimer": [
        "d-dimer", "d-dimeri", "dimeri d"
    ],
    "Fibrinogen": [
        "fibrinogen", "fibrinogenul"
    ],

    # Other Common Tests
    "PSA": [
        "psa", "antigen prostatic specific", "prostate specific antigen"
    ],
    "Free PSA": [
        "psa liber", "free psa"
    ],
    "Procalcitonin": [
        "procalcitonina", "procalcitonin", "pct"
    ],
    "Lactate Dehydrogenase": [
        "ldh", "lactat dehidrogenaza", "lactate dehydrogenase"
    ],
    "Amylase": [
        "amilaza", "amylase"
    ],
    "Lipase": [
        "lipaza", "lipase"
    ],
    "CK (Creatine Kinase)": [
        "ck", "cpk", "creatine kinase", "creatin kinaza"
    ],
}


def _normalize_text(text: str) -> str:
    """Normalize text for comparison - lowercase, remove special chars."""
    # Lowercase
    text = text.lower()
    # Remove accents (Romanian diacritics)
    text = text.replace('ă', 'a').replace('â', 'a').replace('î', 'i')
    text = text.replace('ș', 's').replace('ş', 's')
    text = text.replace('ț', 't').replace('ţ', 't')
    # Remove parentheses content for matching
    text = re.sub(r'\s*\([^)]*\)\s*', ' ', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text.strip()


# Build reverse lookup dictionary for fast matching
_VARIANT_TO_CANONICAL: Dict[str, str] = {}
for canonical, variants in BIOMARKER_MAPPINGS.items():
    for variant in variants:
        normalized = _normalize_text(variant)
        _VARIANT_TO_CANONICAL[normalized] = canonical


def normalize_biomarker_name(test_name: str) -> Tuple[str, str]:
    """
    Normalize a biomarker test name to its canonical form.

    Returns:
        Tuple of (canonical_name, display_name)
        - canonical_name: The standardized name for grouping
        - display_name: A user-friendly display name

    If no match found, returns the original name cleaned up.
    """
    if not test_name:
        return test_name, test_name

    original = test_name.strip()

    # STEP 1: Extract abbreviation from parentheses (e.g., "MCHC" from "... (MCHC)")
    # This is the most reliable identifier
    abbrev_match = re.search(r'\(([A-Za-z0-9-]+)\)\s*$', original)
    if abbrev_match:
        abbreviation = abbrev_match.group(1).lower()
        # Try to match the abbreviation directly
        if abbreviation in _VARIANT_TO_CANONICAL:
            canonical = _VARIANT_TO_CANONICAL[abbreviation]
            return canonical, canonical

    normalized = _normalize_text(original)

    # STEP 2: Try exact match of full normalized name
    if normalized in _VARIANT_TO_CANONICAL:
        canonical = _VARIANT_TO_CANONICAL[normalized]
        return canonical, canonical

    # STEP 3: Word-boundary matching - match if ALL words of a variant are in the test name
    # Sort variants by length (longest first) to match more specific names first
    sorted_variants = sorted(_VARIANT_TO_CANONICAL.items(), key=lambda x: len(x[0]), reverse=True)

    test_words = set(normalized.split())

    for variant, canonical in sorted_variants:
        variant_words = set(variant.split())
        # Only match if it's a short variant (abbreviation-like) and matches exactly as a word
        # OR if ALL words of the variant appear in the test name
        if len(variant_words) == 1 and len(variant) <= 4:
            # Short abbreviations must match as a whole word
            if variant in test_words:
                return canonical, canonical
        elif len(variant_words) >= 2:
            # Multi-word variants: all words must be present
            if variant_words.issubset(test_words):
                return canonical, canonical

    # STEP 4: Try the reverse - check if test name is contained in any variant (for very short inputs)
    if len(normalized) >= 3 and len(normalized.split()) == 1:
        for variant, canonical in sorted_variants:
            if normalized in variant.split():
                return canonical, canonical

    # No match - return original with basic cleanup
    # Capitalize first letter of each word
    cleaned = ' '.join(word.capitalize() for word in original.split())
    return cleaned, cleaned


def get_canonical_name(test_name: str) -> str:
    """Get just the canonical name for a test."""
    canonical, _ = normalize_biomarker_name(test_name)
    return canonical


def group_biomarkers(biomarkers: List[dict]) -> Dict[str, List[dict]]:
    """
    Group a list of biomarkers by their canonical name.

    Args:
        biomarkers: List of biomarker dicts with at least 'name' field

    Returns:
        Dict mapping canonical_name -> list of biomarker records
    """
    groups: Dict[str, List[dict]] = {}

    for bio in biomarkers:
        canonical = get_canonical_name(bio.get('name', ''))
        if canonical not in groups:
            groups[canonical] = []

        # Add normalized_name to the biomarker
        bio_copy = dict(bio)
        bio_copy['normalized_name'] = canonical
        groups[canonical].append(bio_copy)

    # Sort each group by date (most recent first)
    for canonical in groups:
        groups[canonical].sort(
            key=lambda x: x.get('date') or '',
            reverse=True
        )

    return groups


def get_all_canonical_names() -> List[str]:
    """Get a list of all canonical biomarker names."""
    return list(BIOMARKER_MAPPINGS.keys())


def find_similar_names(test_name: str, threshold: float = 0.6) -> List[str]:
    """
    Find canonical names that might be similar to the given test name.
    Uses simple substring matching for now.

    Returns list of (canonical_name, score) tuples.
    """
    normalized = _normalize_text(test_name)
    results = []

    for canonical, variants in BIOMARKER_MAPPINGS.items():
        # Check if any variant shares significant overlap
        for variant in variants:
            variant_norm = _normalize_text(variant)
            # Simple containment check
            if variant_norm in normalized or normalized in variant_norm:
                results.append(canonical)
                break

    return results
