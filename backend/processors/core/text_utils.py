import re

class TextCleaner:
    @staticmethod
    def clean_unit(unit_str: str) -> str:
        """
        Fixes fragmented units common in PDF extraction.
        E.g., "m g / d L" -> "mg/dL"
        """
        if not unit_str: return ""
        
        # 1. Collapse spaces between single letters
        # Pattern: letter + space + letter -> letter+letter
        # We process this iteratively to handle "m g" -> "mg"
        
        # Remove all spaces first? 
        # Risky if unit is "10^3 / uL". 
        # But for units like "mg/dL", "U/L", "mm/h", usually no spaces are valid.
        
        # Heuristic: If it looks like a standard unit broken up, remove spaces.
        # Check against known chars
        clean = unit_str.replace(" ", "")
        
        # Fix common symbols
        clean = clean.replace("µ", "u").replace("μ", "u") # Normalize micro
        
        return clean.strip()

    @staticmethod
    def clean_value(val_str: str) -> str:
        """
        Standardizes numeric values.
        "1 2. 5" -> "12.5"
        ",5" -> "0.5"
        """
        if not val_str: return ""
        
        # Remove internal spaces in numbers
        # "1 2 . 5" -> "12.5"
        clean = re.sub(r'(\d)\s+(\d)', r'\1\2', val_str)
        clean = clean.replace(" ", "") 
        clean = clean.replace(",", ".")
        
        # Fix leading dot
        if clean.startswith("."):
            clean = "0" + clean
            
        return clean

    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Clean test names.
        """
        if not name: return ""
        # Remove trailing/leading punctuation
        return name.strip(" .:-")

