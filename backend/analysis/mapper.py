import re

class BiomarkerMapper:
    """
    Standardizes biomarker names to an International/Canonical format.
    Maps variable inputs (e.g. "Hemoglobina", "Hb") to a single standard key (e.g. "Hemoglobin").
    """
    
    # Static Knowledge Base (Seed Data)
    # Key: Canonical English Name
    # Value: List of synonyms/variants (mostly Romanian)
    MAPPING_DB = {
        "Hemoglobin": ["hemoglobina", "hb", "hemoglobin"],
        "Hematocrit": ["hematocrit", "ht", "hct"],
        "Erythrocyte Sedimentation Rate": ["vsh", "viteza de sedimentare a hematiilor", "esr"],
        "Red Blood Cells": ["numar eritrocite", "eritrocite", "rbc"],
        "White Blood Cells": ["numar leucocite", "leucocite", "wbc"],
        "Platelets": ["numar trombocite", "trombocite", "plt"],
        "MCV": ["volum eritrocitar mediu", "vem", "mcv"],
        "MCH": ["hemoglobina eritrocitara medie", "hem", "mch"],
        "MCHC": ["concentratia medie a hb. eritrocitare", "chem", "mchc"],
        "Neutrophils": ["neutrofile", "neu"],
        "Lymphocytes": ["limfocite", "lym"],
        "Monocytes": ["monocite", "mon"],
        "Eosinophils": ["eozinofile", "eos"],
        "Basophils": ["bazofile", "bas"],
        
        # Liver / Kidney
        "ALT (TGP)": ["tgp", "alaninaminotransferaza", "alt", "alat"],
        "AST (TGO)": ["tgo", "aspartataminotransferaza", "ast", "asat"],
        "Serum Urea": ["uree serica", "uree"],
        "Serum Creatinine": ["creatinina serica", "creatinina"],
        "Uric Acid": ["acid uric seric", "acid uric"],
        
        # Lipids
        "Total Cholesterol": ["colesterol total", "colesterol seric total", "colesterol"],
        "HDL Cholesterol": ["colesterol hdl", "hdl-colesterol", "hdl"],
        "LDL Cholesterol": ["colesterol ldl", "ldl-colesterol", "ldl"],
        "Triglycerides": ["trigliceride serice", "trigliceride"],
        
        # Diabetes
        "Glucose": ["glucoza serica", "glicemie"],
        "HbA1c": ["hemoglobina glicozilata", "hba1c"],
        
        # Thyroid
        "TSH": ["tsh", "hormon de stimulare tiroidiana"],
        "Free T4": ["ft4", "tiroxina libera"],
        
        # Vitamins/Minerals
        "Vitamin D": ["25-oh-vitamina d", "vitamina d"],
        "Vitamin B12": ["vitamina b12", "cobalamina"],
        "Iron": ["sideremie", "fier"],
        "Calcium": ["calciu seric", "calciu total", "calciu"],
        "Magnesium": ["magneziu seric", "magneziu"],
        
        # Inflammation
        "CRP": ["proteina c reactiva", "pcr", "crp"],
        "Fibrinogen": ["fibrinogen"],
        "Homocysteine": ["homocisteina"],
        
        # Urine
        "Urine pH": ["ph urinar", "ph"],
        "Urine Glucose": ["glucoza urinara"],
        "Urine Protein": ["proteine urinare"],
    }

    # Reverse Index for O(1) Lookup
    _LOOKUP = {}

    @classmethod
    def _initialize(cls):
        if cls._LOOKUP: return
        
        # 1. Load Static Knowledge Base
        for canonical, aliases in cls.MAPPING_DB.items():
            for alias in aliases:
                key = cls.normalize_key(alias)
                cls._LOOKUP[key] = canonical

        # 2. Load Dynamic Aliases from DB
        try:
            from backend.database import SessionLocal
            from backend.models import BiomarkerAlias
            
            session = SessionLocal()
            db_aliases = session.query(BiomarkerAlias).all()
            count = 0
            for row in db_aliases:
                if row.standardized_name:
                    key = cls.normalize_key(row.alias)
                    cls._LOOKUP[key] = row.standardized_name
                    count += 1
            session.close()
            print(f"[Mapper] Loaded {count} custom aliases from DB.")
        except Exception as e:
            print(f"[Mapper] Warning: Could not load DB aliases: {e}")

    @staticmethod
    def normalize_key(text: str) -> str:
        """Strip non-alphanumeric and lowercase."""
        if not text: return ""
        text = text.lower().replace("-", " ").replace(".", "")
        return " ".join(text.split())

    @classmethod
    def map_to_standard(cls, raw_name: str) -> str:
        """
        Returns Canonical Name if found, else returns raw_name.
        """
        cls._initialize()
        
        stripped = cls.normalize_key(raw_name)
        
        # 1. Exact Match
        if stripped in cls._LOOKUP:
            return cls._LOOKUP[stripped]
            
        # 2. Substring Match (Conservative)
        for alias, canonical in cls._LOOKUP.items():
            if stripped.startswith(alias):
                if len(alias) > 3 or stripped == alias:
                    return canonical
                    
        return raw_name
