from typing import List, Dict, Any

class MedicalAdvisor:
    
    SPECIALISTS = {
        "BIOCHIMIE": "Internist",
        "HEMATOLOGIE": "Hematologist",
        "IMUNOLOGIE": "Immunologist",
        "HORMONI": "Endocrinologist"
    }

    ADVICE_MAP = {
        "CHOLESTEROL TOTAL": "High cholesterol increases cardiovascular risk. Considerations: Diet low in saturated fats, exercise. If very high, statins might be discussed.",
        "LDL CHOLESTEROL": "Elevated LDL is a primary risk factor for atherosclerosis. Focus on heart-healthy diet and weight management.",
        "GLUCOZA SERICA": "Abnormal glucose suggests metabolic issues (prediabetes/diabetes). HbA1c test recommended for long-term view.",
        "UREE SERICA": "Kidney function indicator. High levels can mean dehydration or reduced kidney filtration. Hydration is key.",
        "CREATININA SERICA": "Specific kidney function test. Abnormalities require nephrological evaluation.",
        "HEMOGLOBINA": "Low levels indicate anemia. High levels might indicate polycythemia or dehydration. Check iron status.",
        "TGO": "Liver enzyme. Elevation suggests liver cell injury or muscle issues.",
        "TGP": "Specific liver enzyme. Elevation suggests liver inflammation (fatty liver, viral, alcohol).",
        "TSH": "Thyroid function. High=Hypothyroid, Low=Hyperthyroid. Endocrine consult recommended."
    }

    @staticmethod
    def generate_advice(alerts: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Generates advice cards based on alerts.
        Returns list of { "role": str, "advice": str, "triggers": list }
        """
        if not alerts:
            return [{
                "role": "General Practitioner",
                "advice": "No significant abnormalities detected in the recent results. Continue with regular check-ups.",
                "type": "success"
            }]

        advice_cards = []
        
        # Group by Category/System to determine Specialist
        grouped_alerts = {}
        for alert in alerts:
            # We assume alert has 'test_name'
            name = alert['test_name'].upper()
            
            # Simple Category/Specialist mapping
            # This is a heuristic. In real app, would use the DB category.
            role = "General Practitioner"
            if "CHOLESTEROL" in name or "TRIGLICERIDE" in name: role = "Cardiologist/Internist"
            elif "GLUCOZA" in name: role = "Diabetologist/Internist"
            elif "TGO" in name or "TGP" in name or "BILIRUBINA" in name: role = "Gastroenterologist"
            elif "UREE" in name or "CREATININA" in name: role = "Nephrologist"
            elif "HEMOGLOBINA" in name or "LEUCOCITE" in name: role = "Hematologist"
            elif "TSH" in name or "FT4" in name: role = "Endocrinologist"

            if role not in grouped_alerts:
                grouped_alerts[role] = []
            grouped_alerts[role].append(name)

        # Generate Text
        for role, tests in grouped_alerts.items():
            tests_str = ", ".join(set(tests)) # Unique test names
            
            # Composite advice
            details = []
            for t in tests:
                # Find partial match in map
                for key, text in MedicalAdvisor.ADVICE_MAP.items():
                    if key in t:
                        details.append(text)
                        break
            
            if not details:
                details.append("Please consult a doctor to interpret these abnormal values in context.")
            
            # Deduplicate details
            details = list(set(details))
            
            advice_text = f"Consultation recommended for abnormal: {tests_str}. " + " ".join(details)
            
            advice_cards.append({
                "role": role,
                "advice": advice_text,
                "type": "warning",
                "triggers": tests
            })
            
        return advice_cards
