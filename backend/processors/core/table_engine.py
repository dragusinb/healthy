from typing import List, Dict, Any, Optional
import pdfplumber
import pandas as pd

class TableConfig:
    def __init__(self, 
                 headers: Dict[str, List[str]], 
                 row_tolerance: int = 4,
                 footer_keywords: List[str] = None):
        self.headers = headers
        self.row_tolerance = row_tolerance
        self.footer_keywords = footer_keywords or []

class HeaderDrivenTableExtractor:
    def __init__(self, config: TableConfig):
        self.config = config

    def extract(self, page) -> List[Dict[str, str]]:
        words = page.extract_words()
        if not words: 
            print("DEBUG: No words found on page.")
            return []
        
        # 1. Find Headers & Define Columns using Voting/Clustering Strategy
        header_anchors = {} # 'key' -> x0
        
        candidates = [] 
        
        def match_header(word_text, key):
            candidates = self.config.headers.get(key, [])
            return any(c.lower() in word_text.lower() for c in candidates)

        for w in words:
            for key in self.config.headers:
                if match_header(w['text'], key):
                    candidates.append({
                        "y": w['top'],
                        "x": w['x0'],
                        "key": key,
                        "text": w['text']
                    })
        
        if not candidates:
            print("DEBUG: No header candidates found matching config.")
            return []
            
        # Cluster candidates by Y-coordinate
        clusters = [] 
        for c in candidates:
            added = False
            for clust in clusters:
                if abs(c["y"] - clust["y_avg"]) < 10:
                    clust["matches"].append(c)
                    added = True
                    break
            
            if not added:
                clusters.append({"y_avg": c["y"], "matches": [c]})
        
        # Score clusters
        best_cluster = None
        max_score = 0
        
        for clust in clusters:
            unique_keys = set(m["key"] for m in clust["matches"])
            score = len(unique_keys)
            clust["score"] = score
            
            if score > max_score:
                max_score = score
                best_cluster = clust
            elif score == max_score and score > 0:
                if best_cluster and clust["y_avg"] < best_cluster["y_avg"]:
                    best_cluster = clust
        
        found_header_y = 0

        if not best_cluster or max_score < 1:
             print("DEBUG: Voting Logic failed (Max Score < 1). Attempting Fallback Single-Anchor Search...")
             fallback_anchors, fallback_y = self._fallback_single_anchor_search(words)
             
             if not fallback_anchors:
                 print("DEBUG: Fallback failed. No headers found.")
                 return []
             
             header_anchors = fallback_anchors
             found_header_y = fallback_y
             print(f"DEBUG: Fallback Headers locked at Y={found_header_y:.2f}: {header_anchors}")
        else:
            found_header_y = best_cluster["y_avg"]
            print(f"DEBUG: Best Header Line at Y={found_header_y:.2f} (Score: {max_score})")
            
            for m in best_cluster["matches"]:
                 if m["key"] not in header_anchors:
                      header_anchors[m["key"]] = m["x"]
                      print(f"DEBUG: Locked '{m['key']}' at X={m['x']:.2f} (using '{m['text']}')")

            # Supplement missing critical headers (Result) using Fallback OR Deduction
            if "result" not in header_anchors:
                if "reference" in header_anchors:
                    r = header_anchors['reference']
                    print(f"DEBUG: derived x_result. RefX={r:.2f} -> Res={r-180:.2f} Unit={r-80:.2f}")
                    header_anchors["unit"] = r - 80
                    header_anchors["result"] = r - 180
                else:
                    print("DEBUG: Voting Logic missed 'result' and 'reference'. Supplementing with Fallback Search...")
                    supp_anchors, _ = self._fallback_single_anchor_search(words)
                    if supp_anchors and "result" in supp_anchors:
                        header_anchors["result"] = supp_anchors["result"]
                        # If unit missing, take fallback unit too?
                        if "unit" not in header_anchors and "unit" in supp_anchors:
                            header_anchors["unit"] = supp_anchors["unit"]
                    print(f"DEBUG: Supplemented Anchors: {header_anchors}")

        print(f"DEBUG: Final Anchors: {list(header_anchors.keys())}")

        # Define Boundaries
        x_result = header_anchors.get("result", 0)
        x_unit = header_anchors.get("unit", x_result + 50)
        x_ref = header_anchors.get("reference", x_unit + 50)
        
        # 2. Group Words into Rows
        rows_by_y = {}
        content_start_y = found_header_y + 10 
        bottom_limit = 100000 
        
        if self.config.footer_keywords:
            sorted_words = sorted(words, key=lambda w: w['top'])
            for w in sorted_words:
                if w['top'] > content_start_y:
                    if any(fk.lower() in w['text'].lower() for fk in self.config.footer_keywords):
                        if w['top'] < bottom_limit:
                            bottom_limit = w['top']
        
        for w in words:
            if w['top'] < content_start_y: continue
            if w['top'] >= bottom_limit: continue
            
            y_center = w['top'] + (w['bottom'] - w['top'])/2
            
            matched_y = None
            for existing_y in rows_by_y.keys():
                if abs(existing_y - y_center) < self.config.row_tolerance:
                    matched_y = existing_y
                    break
            
            if matched_y is None:
                matched_y = y_center
                rows_by_y[matched_y] = []
            
            rows_by_y[matched_y].append(w)
            
        # 3. Bin words into cells
        structured_rows = []
        
        for y in sorted(rows_by_y.keys()):
            row_words = rows_by_y[y]
            row_words.sort(key=lambda w: w['x0'])
            
            name_parts = []
            val_parts = []
            unit_parts = []
            ref_parts = []
            
            for w in row_words:
                mid_x = (w['x0'] + w['x1']) / 2
                print(f"DEBUG: Binning '{w['text']}' MidX={mid_x:.1f} vs Res={x_result:.1f} Unit={x_unit:.1f}")
                
                if mid_x < x_result:
                    name_parts.append(w['text'])
                elif mid_x >= x_result and mid_x < x_unit:
                    val_parts.append(w['text'])
                elif mid_x >= x_unit and mid_x < x_ref:
                    unit_parts.append(w['text'])
                else:
                    ref_parts.append(w['text'])
            
            row_dict = {
                "name": " ".join(name_parts).strip(),
                "result": " ".join(val_parts).strip(),
                "unit": " ".join(unit_parts).strip(),
                "reference": " ".join(ref_parts).strip()
            }
            
            if not row_dict["name"] and not row_dict["result"]:
                continue
                
            structured_rows.append(row_dict)
            
        return structured_rows

    def _fallback_single_anchor_search(self, words):
        sorted_words = sorted(words, key=lambda w: w['top'])
        for w in sorted_words:
            txt = w['text'].lower()
            if "rezultat" in txt or "result" in txt or "valoare" in txt:
                x_res = w['x0']
                anchors = {
                    # Massive shift left to catch centered text
                    "result": x_res - 60,
                    # Massive expansion right (200px) to prevent Unit capture
                    "unit": x_res + 200, 
                    "reference": x_res + 280
                }
                return anchors, w['top']
        return None, None
