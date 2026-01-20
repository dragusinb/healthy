import re
from typing import Dict, Tuple, Optional

class ValueNormalizer:
    """
    Handles normalization of extracted values:
    - Decimal conversion (3,14 -> 3.14)
    - Flag stripping (High, Low, *)
    - Unit normalization
    """
    
    @staticmethod
    def normalize_value(raw_value: str) -> Tuple[str, str]:
        """
        Returns (clean_value, flags).
        clean_value is suitable for storage (numbers, < > operators).
        flags is 'HIGH', 'LOW', or None.
        """
        if not raw_value:
            return "", None
            
        # 1. Strip Flags from the value string (some labs append them)
        flags = None
        clean = raw_value.strip()
        
        # Check for explicit flags often found in raw text
        # e.g. "25.4 H", "10.2 (High)"
        upper_val = clean.upper()
        if "HIGH" in upper_val or " H " in upper_val or upper_val.endswith(" H") or "*" in upper_val:
             if not flags: flags = "HIGH" # Don't overwrite if already set
             clean = clean.replace("HIGH", "").replace("High", "").replace("*", "").strip()
             if clean.endswith("H"): clean = clean[:-1].strip()
             
        if "LOW" in upper_val or " L " in upper_val or upper_val.endswith(" L"):
             if not flags: flags = "LOW"
             clean = clean.replace("LOW", "").replace("Low", "").strip()
             if clean.endswith("L"): clean = clean[:-1].strip()

        # 2. Decimal Normalization (Comma to Dot)
        # Handle "3,14" -> "3.14" only if it looks like a number
        # We need to be careful not to break text like "See comment, page 2"
        # Regex for number with comma: digit + comma + digit
        if re.search(r'\d,\d', clean):
            clean = clean.replace(',', '.')
            
        # 3. Handle extraction noise (e.g. "absent.")
        clean = clean.rstrip('.') 
        
        return clean, flags

    @staticmethod
    def normalize_unit(raw_unit: str) -> str:
        if not raw_unit:
            return ""
        
        u = raw_unit.strip()
        # Common normalizations
        u = u.replace("deg.", "deg").replace("mg/dl", "mg/dL")
        return u
