import re
import datetime
import pdfplumber
from typing import List, Dict, Any

from backend.analysis.validator import BiomarkerValidator
from backend.analysis.parser import RangeEvaluator
from backend.processors.core.table_engine import HeaderDrivenTableExtractor, TableConfig
from backend.processors.core.text_utils import TextCleaner

class UniversalTableParser:
    def __init__(self, provider_name: str, config: TableConfig):
        self.provider_name = provider_name
        self.config = config
        self.validator = BiomarkerValidator()
        self.extractor = HeaderDrivenTableExtractor(self.config)
        self.pending_name = None

    def parse(self, file_path: str) -> Dict[str, Any]:
        print(f"DEBUG: UniversalParser.parse called for {file_path}")
        text = ""
        results = []
        doc_date = datetime.date.today()
        patient_name = f"Pacient {self.provider_name.capitalize()}"

        try:
            with pdfplumber.open(file_path) as pdf:
                print(f"DEBUG: PDF Opened. Pages: {len(pdf.pages)}")
                # 1. Metadata Extraction (Header/First Page Search)
                # We search the first 20 lines of text for dates
                first_page = pdf.pages[0]
                text = first_page.extract_text() or ""
                
                # Generic Date Regex (DD.MM.YYYY or DD/MM/YYYY)
                date_match = re.search(r"(\d{2}[./-]\d{2}[./-]\d{4})", text)
                if date_match:
                    try:
                        date_str = date_match.group(1).replace("/", ".").replace("-", ".")
                        doc_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
                    except: pass
                
                # 2. Table Extraction (Iterate pages)
                for i, page in enumerate(pdf.pages):
                    print(f"DEBUG: Processing Page {i+1}")
                    # Extract structured rows based on provider config
                    extracted_rows = self.extractor.extract(page)
                    print(f"DEBUG: Page {i+1} returned {len(extracted_rows)} rows.")
                    
                    for row in extracted_rows:
                        self._process_row(row, results)

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Universal Parser Error: {e}")
            return {"error": str(e)}

        return {
            "provider": self.provider_name,
            "patient_name": patient_name,
            "collection_date": doc_date,
            "results": results
        }

    def _process_row(self, row: Dict[str, str], results: List[Dict]):
        """
        Process a single extracted row: Validate, Clean, Flag.
        """
        raw_name = row["name"]
        
        with open("debug_row_dump.txt", "a") as f:
            f.write(f"Row: Name='{raw_name}' Result='{row['result']}' Unit='{row['unit']}' Ref='{row['reference']}'\n")
            
        raw_val = row["result"]
        raw_unit = row["unit"]
        raw_ref = row["reference"]
        
        # 1. Name Handling (Clean & Validate)
        clean_name = TextCleaner.normalize_name(raw_name)
        if len(clean_name) < 3: 
            print(f"DEBUG: Dropped row, name too short ('{clean_name}')")
            return

        validation = self.validator.validate(clean_name)
        print(f"DEBUG: Validation Result: {validation}")
        if not validation["is_valid"]:
            # If name is invalid, maybe we have a multi-line split situation?
            # Or assume it's noise. For robustness, if we have a table row, 
            # we respect the Grid first. If validator blocks, we block.
            return

        final_name = validation.get("standardized_name") or clean_name

        # 2. Value Handling
        clean_val_str = TextCleaner.clean_value(raw_val)
        
        # Multi-line Lookahead Support (Simple Version)
        # If this row has Name but empty Value, store as pending?
        # The TableExtractor usually handles simple multi-line cells if they overlap Y-range.
        # But if they are distinct rows, TableExtractor separates them.
        
        if not clean_val_str and not raw_val:
            # Maybe store self.pending_name? 
            # For strict table parsers, a name with no result is usually a section header.
            # But let's check our specific Synevo case (Name line 1, Result line 2).
            # If TableExtractor put them in different rows, we'd see Row1(Name, "", "", "") and Row2("", "Negativ", "", "").
            self.pending_name = final_name
            return

        # If this row has No Name but Has Value -> Check pending
        if not raw_name and (clean_val_str or raw_val) and self.pending_name:
            final_name = self.pending_name
            self.pending_name = None # Consumed
        
        # Re-check validity if we reconstructed
        if not final_name: return

        # 3. Dynamic Flagging
        flags = "NORMAL"
        # Determine strict value for evaluation
        # We prefer clean value. If empty, use raw but ensure it's a string.
        eval_value = clean_val_str if clean_val_str else (raw_val or "")
        
        eval_status = RangeEvaluator.evaluate(eval_value, raw_ref or "")
        if eval_status in ["HIGH", "LOW"]:
            flags = eval_status
            
        print(f"DEBUG: APPENDING RESULT: {final_name} | {eval_value}")
        results.append({
            "test_name": final_name,
            "value": clean_val_str or raw_val, 
            "unit": TextCleaner.clean_unit(raw_unit),
            "reference_range": raw_ref,
            "category": "General",
            "flags": flags
        })
