from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import BiomarkerAlias
from backend.data.biomarkers import BIOMARKER_KNOWLEDGE
import difflib
import re

class BiomarkerValidator:
    def __init__(self, session: Session = None):
        self.session = session or SessionLocal()
        self.knowledge_base = list(BIOMARKER_KNOWLEDGE.keys())
        
        # Hardcoded blocklist for immediate filtering
        self.blocklist_patterns = [
            r"str\.", r"nr\.", r"bl\.", r"sc\.", r"et\.", r"ap\.", 
            r"sector", r"bucuresti", r"jud\.", r"cod", r"telefon", 
            r"fax", r"email", r"adresa", r"cnp", r"varsta", r"sex"
        ]

    def validate(self, raw_name: str) -> dict:
        """
        Returns:
            {
                "is_valid": bool,
                "standardized_name": str or None,
                "reason": str (ALIAS_FOUND, FUZZY_MATCH, NEW_ALIAS, BLOCKED)
            }
        """
        raw_name = raw_name.strip()
        
        # 0. Check Blocklist (Regex)
        for pattern in self.blocklist_patterns:
            if re.search(pattern, raw_name, re.IGNORECASE):
                # Auto-ignore
                self._save_alias(raw_name, None, is_ignored=True)
                return {"is_valid": False, "reason": "BLOCKED_REGEX"}

        # 1. Check DB Alias
        alias = self.session.query(BiomarkerAlias).filter(BiomarkerAlias.alias == raw_name).first()
        if alias:
            if alias.is_ignored:
                return {"is_valid": False, "reason": "IGNORED_ALIAS"}
            if alias.standardized_name:
                return {"is_valid": True, "standardized_name": alias.standardized_name, "reason": "ALIAS_FOUND"}
            else:
                # Pending alias (User hasn't approved yet)
                # Robust Mode: ALLOW it so we don't lose data.
                return {"is_valid": True, "standardized_name": raw_name, "reason": "PENDING_REVIEW"}

        # 2. Exact Match in Knowledge Base
        # normalize case
        for k in self.knowledge_base:
            if k.lower() == raw_name.lower():
                self._save_alias(raw_name, k, is_ignored=False)
                return {"is_valid": True, "standardized_name": k, "reason": "EXACT_MATCH"}

        # 3. Fuzzy Match
        # Get close matches
        matches = difflib.get_close_matches(raw_name, self.knowledge_base, n=1, cutoff=0.85)
        if matches:
            best_match = matches[0]
            # Auto-link if confidence is high (cutoff 0.85 is decently high)
            self._save_alias(raw_name, best_match, is_ignored=False)
            return {"is_valid": True, "standardized_name": best_match, "reason": "FUZZY_MATCH"}

        # 4. Unknown -> Create Pending Alias and ALLOW IT (Robust Mode)
        # We store it, and the admin can link later.
        self._save_alias(raw_name, None, is_ignored=False)
        return {"is_valid": True, "standardized_name": raw_name, "reason": "NEW_PENDING"}

    def _save_alias(self, alias, standardized, is_ignored):
        try:
            # Check existence again to be safe
            existing = self.session.query(BiomarkerAlias).filter(BiomarkerAlias.alias == alias).first()
            if not existing:
                new_alias = BiomarkerAlias(
                    alias=alias,
                    standardized_name=standardized,
                    is_ignored=is_ignored
                )
                self.session.add(new_alias)
                self.session.commit()
        except Exception as e:
            print(f"Error saving alias {alias}: {e}")
            self.session.rollback()
            
    def close(self):
        self.session.close()
