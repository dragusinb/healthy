from typing import List, Dict, Any, Optional
import pdfplumber
import pandas as pd
from backend.processors.core.text_utils import TextCleaner
from backend.processors.normalizer import ValueNormalizer
from backend.analysis.validator import BiomarkerValidator
from backend.analysis.parser import RangeEvaluator

class ReginaTableParser:
    """
    Specialized parser for Regina Maria PDFs.
    Uses 'Stripe-Based' extraction instead of strictly row-based.
    Deals with vertical misalignment of headers.
    """
    
    def __init__(self):
        self.validator = BiomarkerValidator()
        self.range_evaluator = RangeEvaluator()

    def parse(self, pdf_path: str) -> Dict[str, Any]:
        results = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_results = self._process_page(page)
                    results.extend(page_results)
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR: Regina parsing failed: {e}")
            
        return {
            "provider": "regina_maria",
            "results": results
        }

    def _process_page(self, page) -> List[Dict]:
        words = page.extract_words()
        if not words: return []
        
        # 1. Define Column Stripes (Hardcoded Fallbacks + Detection)
        # Regina Layout is usually:
        # Name: Left aligned ~30-50
        # Result: ~190-300
        # Unit: ~370
        # Ref: ~450
        
        # Attempt to confirm with headers
        x_name_end = 180
        x_res_start = 185
        x_res_end = 360
        x_unit_start = 365
        x_unit_end = 440
        x_ref_start = 445
        
        # Refine using found headers
        for w in words:
            txt = w['text'].lower()
            if "rezultate" in txt:
                x_res_start = w['x0'] - 20 # Buffer
            if "um" == txt or "u.m." == txt:
                x_unit_start = w['x0'] - 10
            if "interval" in txt or "referinta" in txt:
                x_ref_start = w['x0'] - 10
                
        # 2. Bin words into stripes
        name_words = []
        res_words = []
        unit_words = []
        ref_words = []
        
        for w in words:
            if w['top'] < 150: continue # Skip header metadata
            
            mid = (w['x0'] + w['x1']) / 2
            
            if mid < x_name_end:
                name_words.append(w)
            elif mid >= x_res_start and mid < x_res_end:
                res_words.append(w)
            elif mid >= x_unit_start and mid < x_unit_end:
                unit_words.append(w)
            elif mid >= x_ref_start:
                ref_words.append(w)
                
        # 3. Cluster Name Words into Lines (Biomarkers)
        # A "Name Line" implies a row
        name_lines = self._cluster_lines(name_words)
        
        valid_rows = []
        
        for n_line in name_lines:
            n_text = " ".join([w['text'] for w in n_line['words']])
            y_center = n_line['y_center']
            
            # Find closest Result
            best_res = self._find_closest_line(y_center, res_words)
            best_unit = self._find_closest_line(y_center, unit_words)
            best_ref = self._find_closest_line(y_center, ref_words)
            
            # Construct Row
            res_text = best_res['text'] if best_res else ""
            unit_text = best_unit['text'] if best_unit else ""
            ref_text = best_ref['text'] if best_ref else ""
            
            if len(n_text) < 3 or not res_text: continue
            
            # Normalize & Validate
            clean_name = TextCleaner.normalize_name(n_text)
            
            # --- PHASE 17 INTELLIGENT FILTER (Parser 3.1) ---
            # 1. Structural Blocklist (Headers, Metadata, Contact Info)
            lower_name = clean_name.lower()
            blocklist = [
                "varsta", "sex", "cnp", "cod", "telefon", "data", "unitate", 
                "trimitator", "medic", "id", "adresa", "tel", "fax", 
                "note", "comentariu", "analiza", "denumire", "test", "rezultat"
            ]
            if any(b in lower_name for b in blocklist):
                continue

            # 2. Length Heuristic (Biomarkers are usually short, Disclaimers are sentences)
            # "Examinarile marcate cu asterisc..." -> 6+ words -> SKIP
            if len(clean_name.split()) > 6:
                continue

            # 3. Value Quality Check (Address often has no value or noise)
            if not res_text.strip() or len(res_text) > 20: # Values shouldn't be sentences
                 # Exception: Some quali tests have long results. 
                 # But usually "Normal", "Negativ". 
                 # If value is length > 20, suspicious.
                 # Let's check for digits. If no digits and long -> SKIP
                 import re
                 if len(res_text) > 20 and not re.search(r'\d', res_text):
                     continue
            # ------------------------------------------------

            norm_val, flags = ValueNormalizer.normalize_value(res_text)
            norm_unit = ValueNormalizer.normalize_unit(unit_text)
            
            # Validate
            validation = self.validator.validate(clean_name)
            
            # Evaluate Range (if validation passed or discovery mode)
            # Regina often puts flags in results (handled by Normalizer)
            # We still run RangeEvaluator for safety
            final_status = flags or "NORMAL"
            if validation["is_valid"]:
                if ref_text:
                     eval_res = self.range_evaluator.evaluate(norm_val, ref_text)
                     if eval_res != "UNKNOWN":
                          final_status = eval_res
            
            valid_rows.append({
                "test_name": clean_name,
                "value": norm_val,
                "unit": norm_unit,
                "reference_range": ref_text,
                "category": validation.get("category", "General"),
                "flags": final_status
            })
            
        return valid_rows

    def _cluster_lines(self, words, tolerance=10):
        if not words: return []
        sorted_words = sorted(words, key=lambda w: w['top'])
        lines = []
        current_line = [sorted_words[0]]
        
        for w in sorted_words[1:]:
            last = current_line[-1]
            if abs(w['top'] - last['top']) < tolerance:
                current_line.append(w)
            else:
                lines.append(self._make_line(current_line))
                current_line = [w]
        lines.append(self._make_line(current_line))
        return lines

    def _make_line(self, words):
        words.sort(key=lambda w: w['x0'])
        y_min = min(w['top'] for w in words)
        y_max = max(w['bottom'] for w in words)
        text = " ".join([w['text'] for w in words])
        return {
            "y_center": (y_min + y_max) / 2,
            "text": text,
            "words": words
        }

    def _find_closest_line(self, target_y, words_pool):
        # Quick & Dirty: Cluster pool into lines, then find closest Y
        lines = self._cluster_lines(words_pool)
        if not lines: return None
        
        best = None
        min_dist = 20 # Max vertical distance to be considered "same row"
        
        for line in lines:
            dist = abs(line['y_center'] - target_y)
            if dist < min_dist:
                min_dist = dist
                best = line
                
        return best
