import os
import json
import re
from typing import List, Dict, Any

class AIParser:
    """
    Parser 4.0: Uses OpenAI GPT-4o to extract structured data.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            print("WARNING: No OPENAI_API_KEY found. AI Parsing will fail.")

    def extract_profile(self, text: str) -> Dict[str, Any]:
        """
        Extract patient profile information from medical document text.
        This is a dedicated extraction specifically for patient demographics,
        separate from biomarker extraction.
        """
        if not self.api_key:
            return {"error": "Missing API Key", "profile": {}}

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            prompt = self._construct_profile_prompt(text)

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting patient information from Romanian medical laboratory reports. Extract patient demographics accurately from the document header sections."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            return {
                "profile": data.get("profile", {}),
                "confidence": data.get("confidence", "low"),
                "source_hints": data.get("source_hints", [])
            }

        except Exception as e:
            return {"error": str(e), "profile": {}}

    def _construct_profile_prompt(self, text: str) -> str:
        """Construct prompt for profile extraction from Romanian medical documents."""
        # Limit text but focus on header area where patient info usually is
        max_chars = 15000
        truncated_text = text[:max_chars]

        return f"""
Analyze this Romanian medical laboratory report and extract the PATIENT INFORMATION from the document header.

IMPORTANT: Focus on the TOP SECTION of the document where patient details are typically listed.

Common formats in Romanian medical documents:

**Regina Maria format:**
- "Pacient: NUME PRENUME" or "Nume: PRENUME NUME"
- "CNP: 1850315..." (first digit: 1=male, 2=female; digits 2-7 = YYMMDD birth date)
- "Data nasterii: DD.MM.YYYY" or "Nascut: DD.MM.YYYY"
- "Sex: M/F" or "Masculin/Feminin" or "Barbat/Femeie"
- "Varsta: XX ani" (age in years)

**Synevo format:**
- Patient name in header
- CNP number
- Birth date
- Sometimes height/weight for certain tests

**CNP (Cod Numeric Personal) decoding:**
- First digit: 1,3,5,7 = Male; 2,4,6,8 = Female
- Digits 2-3: Year (add 1900 or 2000 based on first digit)
- Digits 4-5: Month (01-12)
- Digits 6-7: Day (01-31)

Example: CNP 1850315... means Male, born 15 March 1985

Extract and return JSON:
{{
    "profile": {{
        "full_name": "First Last Name" or null,
        "date_of_birth": "YYYY-MM-DD" or null,
        "gender": "male" or "female" or null,
        "age_years": number or null,
        "cnp_prefix": "first 7 digits of CNP" or null
    }},
    "confidence": "high" or "medium" or "low",
    "source_hints": ["list of text snippets that helped identify the info"]
}}

Rules:
1. Only include fields you can confidently extract
2. For names: Use proper capitalization (Title Case)
3. For dates: Always output in YYYY-MM-DD format
4. If you find CNP, decode birth date and gender from it
5. If age is given but not birth date, calculate approximate birth year
6. Set confidence based on how clear the information was

Document text:
{truncated_text}
"""
    
    def parse_text(self, text: str) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "Missing API Key", "results": []}

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            prompt = self._construct_prompt(text)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert medical data assistant. Extract ALL test results from laboratory reports. Output strictly valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=8000,  # Increased to handle large number of biomarkers
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)

            results = data.get("results", [])
            metadata = data.get("metadata", {})
            patient_info = data.get("patient_info", {})

            return {
                "results": results,
                "metadata": metadata,
                "patient_info": patient_info,
                "provider": metadata.get("provider", "Unknown")
            }

        except Exception as e:
            return {"error": str(e), "results": []}

    def _construct_prompt(self, text: str) -> str:
        # GPT-4o supports 128k tokens (~400k chars), but we limit to 50k for safety and cost
        max_chars = 50000
        truncated_text = text[:max_chars]

        return f"""
        Analyze the following medical laboratory report text and extract ALL biomarker test results.

        IMPORTANT: Extract EVERY single test result from the document. Do not skip any tests.

        Rules:
        1. Extract: Test Name, Value (number), Unit, Reference Range.
        2. Detect Provider: If text contains "Regina Maria" or "Centrul Medical Unirea", provider="Regina Maria". If "Synevo", provider="Synevo". Else "Unknown".
        3. Extract Date: Find date in format DD.MM.YYYY or YYYY-MM-DD (e.g. from "Data cerere", "Data rezultatului", "Data recoltarii"). Convert to YYYY-MM-DD.
        4. For flags: Compare value to reference_range. If outside range, set "HIGH" or "LOW". If within range, set "NORMAL".
        5. Extract patient information if found: name, date of birth (convert to YYYY-MM-DD), gender (male/female), height (in cm), weight (in kg), blood type.
        6. Output strictly valid JSON with this structure:
        {{
            "metadata": {{
                "provider": "Regina Maria",
                "date": "2017-08-01"
            }},
            "patient_info": {{
                "full_name": "John Doe",
                "date_of_birth": "1985-03-15",
                "gender": "male",
                "height_cm": 175,
                "weight_kg": 80,
                "blood_type": "A+"
            }},
            "results": [
                {{
                    "test_name": "Hemoglobina",
                    "value": "14.2",
                    "numeric_value": 14.2,
                    "unit": "g/dL",
                    "reference_range": "12 - 16",
                    "flags": "NORMAL"
                }}
            ]
        }}

        Note: Only include patient_info fields that are actually found in the document. Leave out fields that are not present.

        Text content:
        {truncated_text}
        """
