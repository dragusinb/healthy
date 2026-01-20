import pdfplumber
import re
import datetime
import os
from typing import List, Dict, Any, Optional

class ReginaMariaParser:
    def parse(self, file_path: str) -> Dict[str, Any]:
        data = {
            "provider": "regina_maria",
            "file_path": file_path,
            "patient_name": None,
            "collection_date": None,
            "results": []
        }
        
        # --- Metadata (Date/Patient) uses simple text search as it's typically key-value ---
        # We can still use valid simple parsing for this.
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                txt = page.extract_text() or ""
                full_text += txt + "\n"
        
        # 1. Date Extraction
        # Patterns: "Data - ora recoltare: 12.08.2025" or "Data cerere: ..."
        date_pattern = r"Data.*?recoltare[:\s]+(\d{2}\.\d{2}\.\d{4})"
        match = re.search(date_pattern, full_text, re.IGNORECASE)
        if match:
            try:
                data["collection_date"] = datetime.datetime.strptime(match.group(1), "%d.%m.%Y").date()
            except: pass
            
        if not data["collection_date"]:
             match = re.search(r"Data\s*cerere[:\s]+(\d{2}\.\d{2}\.\d{4})", full_text, re.IGNORECASE)
             if match:
                 try: data["collection_date"] = datetime.datetime.strptime(match.group(1), "%d.%m.%Y").date()
                 except: pass

        # 2. Patient Name
        name_match = re.search(r"Nume[:\s]+(.*?)(?:\n|$)", full_text)
        if name_match:
             data["patient_name"] = name_match.group(1).strip()

        # --- Table Extraction using New Engine ---
        from backend.processors.core.table_engine import HeaderDrivenTableExtractor, TableConfig
        from backend.processors.core.text_utils import TextCleaner
        
        config = TableConfig(
            headers={
                "result": ["Rezultate", "Rezultat"],
                "unit": ["UM", "U.M."],
                "reference": ["Interval", "Valori", "Interval biologic"]
            },
            row_tolerance=4
        )
        
        engine = HeaderDrivenTableExtractor(config)
        
        extracted_rows = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                rows = engine.extract(page)
                extracted_rows.extend(rows)
                
        # 3. Process Extracted Rows into TestResults
        current_category = "General"
        
        for row in extracted_rows:
            raw_name = row["name"]
            raw_res = row["result"]
            raw_unit = row["unit"]
            raw_ref = row["reference"]
            
            # Heuristic: If name is ALL CAPS and result is empty, it's a category
            # Regina Maria categories: "HEMATOLOGIE", "BIOCHIMIE"
            if raw_name.isupper() and len(raw_name) > 3 and not raw_res:
                 # Check against known list or just assume?
                 # Avoid headers like "DENUMIRE ANALIZA"
                 if "DENUMIRE" not in raw_name and "ANALIZA" not in raw_name:
                     current_category = raw_name
                     continue
                     
            if not raw_res: continue
            
            # --- Cleaning ---
            test_name = TextCleaner.normalize_name(raw_name)
            # Skip if name is still internal header
            if "Total" in test_name and not raw_res: continue # totals?
            
            value = TextCleaner.clean_value(raw_res)
            unit = TextCleaner.clean_unit(raw_unit)
            
            # Handle user report: "m g / d L [0.70 - 1.20]" being all in reference? 
            # Or "15.9 µmol/L" in value?
            
            # Logic: If Unit column is empty, but Value contains letters, split
            if not unit and any(c.isalpha() for c in value):
                 # Try splitting value "15.9mg/dL"
                 split_match = re.match(r"([\d\.,]+)\s*([a-zA-Z%µ/]+.*)", value)
                 if split_match:
                     value = split_match.group(1)
                     unit = split_match.group(2)
            
            # Logic: If Reference contains units? usually harmless.
            
            # Flags logic
            flags = "NORMAL"
            
            # Only add if we have a valid value
            if value:
                data["results"].append({
                    "test_name": test_name,
                    "value": value,
                    "unit": unit,
                    "reference_range": raw_ref,
                    "category": current_category,
                    "flags": flags
                })
                
                
        return data 



if __name__ == "__main__":
    pass
