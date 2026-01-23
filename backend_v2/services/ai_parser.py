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

            return {
                "results": results,
                "metadata": metadata,
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
        5. Output strictly valid JSON with this structure:
        {{
            "metadata": {{
                "provider": "Regina Maria",
                "date": "2017-08-01"
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

        Text content:
        {truncated_text}
        """
