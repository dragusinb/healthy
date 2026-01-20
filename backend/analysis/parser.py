import re

class RangeEvaluator:
    @staticmethod
    def parse_value(val_str: str) -> float:
        """Extracts the first float found in a string."""
        match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
        if match:
            return float(match.group())
        return None

    @staticmethod
    def evaluate(value: str, ref_range: str) -> str:
        """
        Determines if a value is LOW, HIGH, or NORMAL based on the reference range.
        Returns: 'LOW', 'HIGH', 'NORMAL', or 'UNKNOWN'
        """
        if not value or not ref_range:
            return "UNKNOWN"

        clean_val = value.lower().strip()
        clean_ref = ref_range.lower().strip()

        # 1. Qualitative Checks
        # If range is "negativ" and value is "negativ" -> NORMAL
        qualitative_map = {
            "negativ": ["negativ", "absent", "nedetectabil", "nonreactiv"],
            "pozitiv": ["pozitiv", "prezent", "reactiv"]
        }
        
        # Check if reference expects a qualitative result
        for expected_status, keywords in qualitative_map.items():
            if expected_status in clean_ref:
                # If the value matches any keyword associated with this status, it's normal (if ref is that status)
                # But usually ref is "Negativ". So if val is "Negativ" -> Normal.
                if clean_val in keywords:
                    return "NORMAL"
                # If ref is Negativ and val is Pozitiv -> HIGH (Bad)
                if expected_status == "negativ" and any(k in clean_val for k in qualitative_map["pozitiv"]):
                    return "HIGH"

        # 2. Quantitative Checks
        try:
            val_num = RangeEvaluator.parse_value(clean_val)
            if val_num is None:
                return "UNKNOWN"

            # CASE A: Interval "[ min - max ]" or "min - max"
            # Regex to find two numbers separated by dash/hyphen
            range_match = re.search(r"\[?\s*(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*\]?", clean_ref)
            if range_match:
                min_ref = float(range_match.group(1))
                max_ref = float(range_match.group(2))
                
                if val_num < min_ref: return "LOW"
                if val_num > max_ref: return "HIGH"
                return "NORMAL"

            # CASE B: Inequality "< max" or "<= max"
            if clean_ref.startswith("<"):
                max_ref = RangeEvaluator.parse_value(clean_ref)
                if max_ref is not None:
                    if val_num >= max_ref and "=" not in clean_ref: return "HIGH"
                    if val_num > max_ref: return "HIGH"
                    return "NORMAL"
            
            # CASE C: Inequality "> min" or ">= min"
            if clean_ref.startswith(">"):
                min_ref = RangeEvaluator.parse_value(clean_ref)
                if min_ref is not None:
                    if val_num <= min_ref and "=" not in clean_ref: return "LOW"
                    if val_num < min_ref: return "LOW"
                    return "NORMAL"

        except Exception as e:
            print(f"Error parsing '{value}' vs '{ref_range}': {e}")
            return "UNKNOWN"
            
        return "UNKNOWN"
