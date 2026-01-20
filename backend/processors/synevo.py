import re
import datetime
import pdfplumber
from typing import List, Dict, Any

from backend.analysis.validator import BiomarkerValidator
from backend.analysis.parser import RangeEvaluator
from backend.processors.core.table_engine import HeaderDrivenTableExtractor, TableConfig
from backend.processors.core.text_utils import TextCleaner

class SynevoParser:
    def __init__(self):
        self.validator = BiomarkerValidator()
        self.config = TableConfig(
            headers={
                "name": ["Denumire", "Analiza", "Test"],
                "result": ["Rezultat", "Valoare"],
                "unit": ["UM", "U.M.", "Unit"],
                "reference": ["Interval", "Referinta", "Biologic"]
            },
            row_tolerance=5,
            footer_keywords=["Medic", "Rezultat eliberat", "Pagina", "Synevo", "Laborator"]
        )
        self.extractor = HeaderDrivenTableExtractor(self.config)

    def parse(self, file_path: str) -> Dict[str, Any]:
        text = ""
        results = []
        doc_date = datetime.date.today()
        patient_name = "Pacient Synevo"

        try:
            with pdfplumber.open(file_path) as pdf:
                # 1. Metadata Extraction (from text of first page usually)
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text:
                    text = first_page_text # For simple metadata regex
                    
                    # Date
                    date_match = re.search(r"Data\s*recoltarii[:\s]+(\d{2}[./]\d{2}[./]\d{4})", text, re.IGNORECASE)
                    if date_match:
                        try:
                            date_str = date_match.group(1).replace("/", ".")
                            doc_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
                        except: pass

                    # Patient Name
                    # Look for "Nume pacient:" and "Prenume pacient:"
                    # Example: Nume pacient: Dragusin Cod de bare: ...
                    
                    nume_match = re.search(r"Nume\s*pacient[:\s]+([A-Za-z\-]+)", text, re.IGNORECASE)
                    prenume_match = re.search(r"Prenume\s*pacient[:\s]+([A-Za-z\-]+)", text, re.IGNORECASE)
                    
                    nume = nume_match.group(1) if nume_match else ""
                    prenume = prenume_match.group(1) if prenume_match else ""
                    
                    if nume or prenume:
                        patient_name = f"{nume} {prenume}".strip()
                
                # 2. Table Extraction (Iterate pages)
                for page in pdf.pages:
                    # Extract structured rows
                    extracted_rows = self.extractor.extract(page)
                    
                    for row in extracted_rows:
                        # Raw Data
                        raw_name = row["name"]
                        raw_val = row["result"]
                        raw_unit = row["unit"]
                        raw_ref = row["reference"]
                        
                        # 1. Clean Name
                        clean_name = TextCleaner.normalize_name(raw_name)
                        if len(clean_name) < 3: continue

                        # 2. Validate Name (Security/Noise Check)
                        # This efficiently filters out "Address" lines because they won't match KB
                        validation = self.validator.validate(clean_name)
                        if not validation["is_valid"]:
                            # Special handling: If validator says "NEW_PENDING", maybe log it but skip for now
                            # If "BLOCKED", definitely skip.
                            continue

                        final_name = validation.get("standardized_name") or clean_name

                        # 3. Clean Value & Unit
                        clean_val_str = TextCleaner.clean_value(raw_val)
                        # If value is empty, maybe it's a heading or noise
                        if not clean_val_str and not raw_val: continue
                        
                        # For qualitative (Text), use raw text if clean failed to find numbers
                        # But TextCleaner.clean_value strips non-numeric? 
                        # Wait, clean_value logic: re.sub(r'(\d)\s+(\d)', r'\1\2', val_str) -> replace space -> replace comma.
                        # It doesn't strip letters! So "Negativ" remains "Negativ".
                        
                        clean_unit = TextCleaner.clean_unit(raw_unit)
                        
                        # 4. Dynamic Evaluation (Flagging)
                        flags = "NORMAL"
                        eval_status = RangeEvaluator.evaluate(clean_val_str, raw_ref)
                        if eval_status in ["HIGH", "LOW"]:
                            flags = eval_status
                        
                        # 5. Add to Results
                        results.append({
                            "test_name": final_name,
                            "value": clean_val_str,
                            "unit": clean_unit,
                            "reference_range": raw_ref,
                            "category": "General", # Could try to infer category later
                            "flags": flags
                        })

        except Exception as e:
            print(f"PDF Reading Error: {e}")
            return {"error": str(e)}

        return {
            "provider": "Synevo",
            "patient_name": patient_name,
            "collection_date": doc_date,
            "results": results
        }
