import os
import json
from typing import Dict, Any, List
from pypdf import PdfReader
from openai import OpenAI

class AIService:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            print("WARNING: No OPENAI_API_KEY found. AI Parsing will fail.")
            
    def extract_text_from_pdf(self, file_path: str) -> str:
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF {file_path}: {e}")
            return ""

    def process_document(self, file_path: str) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "Missing API Key", "results": [], "metadata": {}}

        text = self.extract_text_from_pdf(file_path)
        if not text:
            return {"error": "Empty or unreadable PDF", "results": [], "metadata": {}}
            
        return self.parse_text_with_ai(text)

    def parse_text_with_ai(self, text: str) -> Dict[str, Any]:
        try:
            client = OpenAI(api_key=self.api_key)
            
            prompt = self._construct_prompt(text)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert medical data assistant. Output strictly valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            print(f"AI Response: {content[:100]}...") # Debug log
            
            data = json.loads(content)
            return data

        except Exception as e:
            print(f"AI Parse Error: {e}")
            return {"error": str(e), "results": [], "metadata": {}}

    def _construct_prompt(self, text: str) -> str:
        return f"""
        Analyze the following medical laboratory report text and extract all biomarker test results.
        
        Rules:
        1. Extract: Test Name, Value (number), Unit, Reference Range.
        2. Detect Provider: If text contains "Regina Maria" or "Centrul Medical Unirea", provider="Regina Maria". If "Synevo", provider="Synevo". Else "Unknown".
        3. Extract Date: Find date in format DD.MM.YYYY or YYYY-MM-DD. Convert to YYYY-MM-DD.
        4. FLAGS: Determine if the value is NORMAL, HIGH, or LOW based on the Reference Range.
        5. Output strictly valid JSON with this structure:
        {{
            "metadata": {{
                "provider": "Regina Maria",
                "date": "2023-10-15"
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
        {text[:15000]} 
        """
