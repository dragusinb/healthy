
# Medical Knowledge Base for Biomarker Contextualization
# Sources: Mayo Clinic, Mount Sinai, LabCorp, Synevo/ReginaMaria Reference Ranges

BIOMARKER_KNOWLEDGE = {
    "Borrelia burgdorferi": {
        "display_name": "Borrelia burgdorferi IgG/IgM",
        "description": "Detection of antibodies against Borrelia burgdorferi, the causative agent of Lyme disease.",
        "unit": "Qualitative",
        "category": "Serology"
    },
    "Antigen Streptococ betahemolitic grup A": {
        "display_name": "Strep A Antigen",
        "description": "Rapid test for Group A Streptococcus bacteria.",
        "unit": "Qualitative",
        "category": "Microbiology"
    },
    "SPR Antigen Streptococ betahemolitic grup A": {
        "display_name": "Strep A Antigen",
        "description": "Rapid test for Group A Streptococcus bacteria.",
        "unit": "Qualitative",
        "category": "Microbiology"
    },
     "Antigen Streptococ betahemolitic grup C": {
        "display_name": "Strep C Antigen",
        "description": "Rapid test for Group C Streptococcus bacteria.",
        "unit": "Qualitative",
        "category": "Microbiology"
    },
     "Antigen Streptococ betahemolitic grup G": {
        "display_name": "Strep G Antigen",
        "description": "Rapid test for Group G Streptococcus bacteria.",
        "unit": "Qualitative",
        "category": "Microbiology"
    },
    "UREE SERICA": {
        "display_name": "Serum Urea",
        "description": "Urea is a waste product formed in the liver when protein is metabolized. It is released into the blood and filtered out by the kidneys. High levels may indicate kidney issues or dehydration.",
        "unit": "mg/dL",
        "min_safe": 13,
        "max_safe": 43,
        "category": "Biochemistry"
    },
    "GLUCOZA SERICA": {
        "display_name": "Serum Glucose",
        "description": "Glucose is the main source of energy for the body's cells. Levels are regulated by insulin and glucagon. High levels can indicate diabetes or pre-diabetes.",
        "unit": "mg/dL",
        "min_safe": 70,
        "max_safe": 105,
        "category": "Biochemistry"
    },
    "CHOLESTEROL TOTAL": {
        "display_name": "Total Cholesterol",
        "description": "Cholesterol is a waxy substance found in your blood. Your body needs cholesterol to build healthy cells, but high levels of cholesterol can increase your risk of heart disease.",
        "unit": "mg/dL",
        "min_safe": 0,
        "max_safe": 200,
        "category": "Lipid Panel"
    },
    "HDL CHOLESTEROL": {
        "display_name": "HDL Cholesterol",
        "description": "High-density lipoprotein (HDL) includes cholesterol that is being transported from the body's tissues to the liver. Often called 'good' cholesterol.",
        "unit": "mg/dL",
        "min_safe": 40,
        "max_safe": 60, # Higher is better generally, but this is a standard range
        "category": "Lipid Panel"
    },
    "LDL CHOLESTEROL": {
        "display_name": "LDL Cholesterol",
        "description": "Low-density lipoprotein (LDL) transports cholesterol to your body's cells. Often called 'bad' cholesterol because it can build up in your artery walls.",
        "unit": "mg/dL",
        "min_safe": 0,
        "max_safe": 100, # Optimal
        "category": "Lipid Panel"
    },
    "TRIGLICERIDE": {
        "display_name": "Triglycerides",
        "description": "Triglycerides are a type of fat (lipid) found in your blood. High triglycerides can contribute to hardening of the arteries or thickening of the artery walls.",
        "unit": "mg/dL",
        "min_safe": 0,
        "max_safe": 150,
        "category": "Lipid Panel"
    },
    "CREATININA SERICA": {
        "display_name": "Serum Creatinine",
        "description": "Creatinine is a waste product from the normal breakdown of muscle tissue. It is filtered from the blood by the kidneys. Levels measure kidney function.",
        "unit": "mg/dL",
        "min_safe": 0.6,
        "max_safe": 1.2,
        "category": "Biochemistry"
    },
    "HEMOGLOBINA": {
        "display_name": "Hemoglobin",
        "description": "Hemoglobin is a protein in your red blood cells that carries oxygen to your body's organs and tissues and transports carbon dioxide from your organs and tissues back to your lungs.",
        "unit": "g/dL",
        "min_safe": 12, # General adult range, varies by sex
        "max_safe": 17,
        "category": "Hematology"
    },
    "HEMATOCRIT": {
        "display_name": "Hematocrit",
        "description": "Hematocrit represents the percentage of red blood cells in your blood. It is a key indicator of anemia or dehydration.",
        "unit": "%",
        "min_safe": 36,
        "max_safe": 50,
        "category": "Hematology"
    },
    "LEUCOCITE": {
        "display_name": "WBC (Leukocytes)",
        "description": "White blood cells are an important part of the immune system. They help fight infections and diseases.",
        "unit": "mii/µL",
        "min_safe": 4,
        "max_safe": 10,
        "category": "Hematology"
    },
    "TROMBOCITE": {
        "display_name": "Platelets",
        "description": "Platelets are colorless blood cells that help blood clot. They stop bleeding by clumping and forming plugs in blood vessel injuries.",
        "unit": "mii/µL",
        "min_safe": 150,
        "max_safe": 450,
        "category": "Hematology"
    },
    "VSH": {
        "display_name": "ESR (Sedimentation Rate)",
        "description": "Erythrocyte sedimentation rate (ESR) is a blood test that can reveal inflammatory activity in your body.",
        "unit": "mm/h",
        "min_safe": 0,
        "max_safe": 20, # General < 50y
        "category": "Inflammation"
    },
    "CALCIU SERIC TOTAL": {
        "display_name": "Serum Calcium",
        "description": "Calcium is essential for healthy bones and teeth. It is also essential for the normal functioning of nerves, cells, and muscle.",
        "unit": "mg/dL",
        "min_safe": 8.5,
        "max_safe": 10.5,
        "category": "Minerals"
    },
    "MAGNEZIU SERIC": {
        "display_name": "Serum Magnesium",
        "description": "Magnesium is a mineral that supports muscle and nerve function and energy production.",
        "unit": "mg/dL",
        "min_safe": 1.7,
        "max_safe": 2.2,
        "category": "Minerals"
    },
    "SIDEREMIE": {
        "display_name": "Serum Iron",
        "description": "Measures the amount of circulating iron in the blood. Iron is essential for the production of healthy red blood cells.",
        "unit": "µg/dL",
        "min_safe": 60,
        "max_safe": 170,
        "category": "Minerals"
    },
    "TGO": {
        "display_name": "AST (TGO)",
        "description": "Aspartate aminotransferase (AST) is an enzyme found in the liver and other tissues. High levels may indicate liver damage.",
        "unit": "U/L",
        "min_safe": 0,
        "max_safe": 40,
        "category": "Liver Function"
    },
    "TGP": {
        "display_name": "ALT (TGP)",
        "description": "Alanine aminotransferase (ALT) is an enzyme found mostly in the liver. It is a more specific indicator of liver inflammation than AST.",
        "unit": "U/L",
        "min_safe": 0,
        "max_safe": 41, # Men, slightly lower for women
        "category": "Liver Function"
    },
     "HOMOCISTEINA": {
        "display_name": "Homocysteine",
        "description": "Homocysteine is an amino acid. High levels are linked to early development of heart disease and can indicate vitamin deficiencies (B12, Folate).",
        "unit": "µmol/L",
        "min_safe": 0,
        "max_safe": 15,
        "category": "Biochemistry"
    }
}

def get_biomarker_info(name):
    """Normalize name and return knowledge if matches."""
    # Simple normalization: Upper, remove * etc (already done in parser)
    # Could imply fuzzy matching here if needed.
    
    clean_name = name.upper().strip()
    
    # Try exact match first
    if clean_name in BIOMARKER_KNOWLEDGE:
        return BIOMARKER_KNOWLEDGE[clean_name]

    # Try partial match (e.g. "GLUCOZA" inside "GLUCOZA SERICA")
    # This acts as a fallback but we prefer exact keys.
    for key, info in BIOMARKER_KNOWLEDGE.items():
        if key in clean_name and len(clean_name) < len(key) + 10:
             return info
             
    return None
