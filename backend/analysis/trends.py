from typing import List, Dict, Any
from backend.models import TestResult, Document
from backend.analysis.parser import RangeEvaluator
import statistics

class TrendAnalyzer:
    @staticmethod
    def calculate_trends(results: List[TestResult]) -> List[Dict[str, Any]]:
        """
        Groups results by test_name and calculates trends.
        Returns a list of trend objects for tests with >= 2 data points.
        Ordered by Date of most recent test (Newest First).
        """
        # Group by test name
        grouped = {}
        for r in results:
            if not r.value: continue
            
            # Simple normalization of test name
            name = r.test_name.lower().strip()
            
            # Try numeric first
            val = RangeEvaluator.parse_value(r.value)
            
            # If not numeric, check if it's a known qualitative status
            if val is None:
                # Qualitative fallback
                val_str = r.value.lower().strip()
                if any(x in val_str for x in ["negativ", "pozitiv", "absent", "prezent", "reactiv", "nereactiv"]):
                    val = val_str # Keep textual value
                else:
                    continue # Skip garbage
            
            if name not in grouped:
                grouped[name] = []
            
            grouped[name].append({
                "date": r.document.document_date,
                "value": val,
                "unit": r.unit,
                "original_result": r
            })
            
        trends = []
        for name, points in grouped.items():
            # Sort by date ascending to calculate trend history
            points.sort(key=lambda x: x["date"])
            
            # Use 'value' as the key for numbers
            filtered_values = [p["value"] for p in points]

            if len(filtered_values) < 2:
                # SPECIAL CASE: For qualitative results, even a SINGLE positive result is a trend worth showing
                # Identify if it's qualitative
                display_name = points[-1]["original_result"].test_name
                last_val = points[-1]["value"]
                
                if isinstance(last_val, str):
                    # For qualitative, allow single point if attention needed
                     pass # Continue to processing below (slice will handle len<2 safely)
                else:
                    continue
                
            # User Rule: "for key trends I would like to have them related to my past 3 analysis"
            # Take the last 3 data points
            recent_values = filtered_values[-3:]
            recent_points = points[-3:]
            
            # Simple Trend Logic on recent_values
            first = recent_values[0]
            last = recent_values[-1]
            last_date = recent_points[-1]["date"]
            
            change_pct = 0
            direction = "stable"
            
            # NUMERIC LOGIC
            if isinstance(last, (int, float)) and isinstance(first, (int, float)):
                # Simple Direction: Compare last vs avg of previous (in the sliced window)
                if len(recent_values) > 1:
                    comparison_base = statistics.mean(recent_values[:-1])
                    if comparison_base != 0:
                        change_pct = ((last - comparison_base) / comparison_base) * 100
                    
                    if change_pct > 10: direction = "up"
                    elif change_pct < -10: direction = "down"
            
            # QUALITATIVE LOGIC
            elif isinstance(last, str):
                # No numeric change pct
                change_pct = 0
                direction = "qualitative"
            
            # Formatted Name (Capitalized)
            original_result = points[-1]["original_result"]
            display_name = original_result.test_name
            
            # Attention Logic:
            # 1. Check existing flags
            is_abnormal = original_result.flags in ["HIGH", "LOW"]
            
            # 2. If no flag, check Knowledge Base limits OR Qualitative Keywords
            if not is_abnormal:
                # Qualitative check
                if isinstance(last, str):
                    bad_keywords = ["pozitiv", "prezent", "reactiv", "detectabil"]
                    if any(bad in last.lower() for bad in bad_keywords):
                        is_abnormal = True
                else:
                    # Numeric Check
                    from backend.data.biomarkers import get_biomarker_info
                    info = get_biomarker_info(display_name)
                    if info:
                        min_safe = info.get("min_safe")
                        max_safe = info.get("max_safe")
                        val = last
                        
                        if min_safe is not None and val < min_safe:
                            is_abnormal = True
                        elif max_safe is not None and val > max_safe:
                            is_abnormal = True
            
            trends.append({
                "test_name": display_name,
                "current_value": last,
                "unit": points[-1]["unit"],
                "history": recent_values,
                "change_pct": round(change_pct, 1),
                "direction": direction,
                "dates": [p["date"].isoformat() for p in recent_points],
                "is_attention_needed": is_abnormal,
                "last_date_obj": last_date # Helper for sorting
            })
            
        # Sort by Date (Newest First)
        trends.sort(key=lambda x: x["last_date_obj"], reverse=True)
        
        # Cleanup helper key
        for t in trends:
            del t["last_date_obj"]
            
        return trends
