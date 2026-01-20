from typing import List
from ..models import TestResult, Document

class MedicalInterpreter:
    def analyze_trends(self, results: List[TestResult]) -> List[str]:
        """
        Detect simple trends in data.
        """
        insights = []
        # Group by test name
        grouped = {}
        for r in results:
             if r.test_name not in grouped: grouped[r.test_name] = []
             try:
                 val = float(r.value.replace(",", "."))
                 grouped[r.test_name].append((r.document.document_date, val))
             except:
                 pass
        
        for name, values in grouped.items():
            if len(values) < 2: continue
            values.sort(key=lambda x: x[0])
            
            first_val = values[0][1]
            last_val = values[-1][1]
            
            diff = last_val - first_val
            percent_change = (diff / first_val) * 100 if first_val != 0 else 0
            
            if percent_change > 20:
                 insights.append(f"{name} has increased by {percent_change:.1f}% since {values[0][0].strftime('%b %Y')}.")
            elif percent_change < -20:
                 insights.append(f"{name} has decreased by {abs(percent_change):.1f}% since {values[0][0].strftime('%b %Y')}.")
                 
        return insights

    def summarize_latest(self, document: Document, results: List[TestResult]) -> str:
        """
        Summarize a specific document's findings.
        """
        abnormal = [f"{r.test_name} ({r.value}) is {r.flags}" for r in results if r.flags in ["HIGH", "LOW"]]
        if not abnormal:
            return "All test results appear to be within normal reference ranges."
        
        return f"Attention required for: {', '.join(abnormal)}."
