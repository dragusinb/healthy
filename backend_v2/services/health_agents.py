"""AI Health Analysis Agents.

Implements specialist AI agents that analyze biomarkers and generate health insights.
"""
import json
import os
from openai import OpenAI
from typing import List, Dict, Any, Optional
from datetime import datetime


class HealthAgent:
    """Base class for health analysis agents."""

    LANGUAGE_INSTRUCTIONS = {
        "ro": "IMPORTANT: You MUST respond entirely in Romanian. All text including summary, findings, explanations, and recommendations must be written in Romanian language.",
        "en": "Respond in English."
    }

    def __init__(self, language: str = "en"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"
        self.language = language if language in self.LANGUAGE_INSTRUCTIONS else "en"

    def _get_language_instruction(self) -> str:
        """Get the language instruction for prompts."""
        return self.LANGUAGE_INSTRUCTIONS.get(self.language, self.LANGUAGE_INSTRUCTIONS["en"])

    def _call_ai(self, system_prompt: str, user_prompt: str) -> str:
        """Make an API call to OpenAI."""
        # Add language instruction to system prompt
        full_system_prompt = f"{system_prompt}\n\n{self._get_language_instruction()}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content


class GeneralistAgent(HealthAgent):
    """General health analyst that reviews all biomarkers and identifies areas of concern."""

    def __init__(self, language: str = "en"):
        super().__init__(language=language)

    SYSTEM_PROMPT = """You are an AI health analyst assistant. Your role is to review lab test results
and provide a general health assessment. You are NOT a doctor and cannot diagnose conditions.

Your analysis should:
1. Identify biomarkers that are outside normal ranges
2. Group related abnormalities (e.g., liver markers, kidney markers)
3. Highlight trends if multiple tests are available
4. Suggest which specialist areas might need attention
5. Provide general lifestyle recommendations

Always be balanced - acknowledge both concerning and positive findings.
Use clear, non-alarmist language appropriate for a patient.

Respond in JSON format with this structure:
{
    "summary": "Brief 2-3 sentence overview",
    "risk_level": "normal|attention|concern|urgent",
    "findings": [
        {
            "category": "Category name",
            "status": "normal|attention|concern",
            "markers": ["marker1", "marker2"],
            "explanation": "What this means"
        }
    ],
    "recommendations": [
        {
            "priority": "high|medium|low",
            "action": "What to do",
            "reason": "Why this is recommended"
        }
    ],
    "specialist_referrals": ["cardiology", "endocrinology"] // if needed
}"""

    def analyze(self, biomarkers: List[Dict], profile_context: str = "") -> Dict[str, Any]:
        """Analyze all biomarkers and generate a general health report."""
        if not biomarkers:
            return {
                "summary": "No biomarker data available for analysis.",
                "risk_level": "normal",
                "findings": [],
                "recommendations": [],
                "specialist_referrals": []
            }

        # Format biomarkers for the prompt
        biomarker_text = self._format_biomarkers(biomarkers)

        # Include profile context if available
        profile_section = ""
        if profile_context:
            profile_section = f"""
{profile_context}

Consider the patient's profile when analyzing results. Age, gender, BMI, lifestyle factors, and existing conditions can affect interpretation of lab values.

"""

        user_prompt = f"""{profile_section}Please analyze these lab test results and provide a comprehensive health assessment:

{biomarker_text}

Provide your analysis in JSON format as specified."""

        response = self._call_ai(self.SYSTEM_PROMPT, user_prompt)

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            return json.loads(json_str)
        except json.JSONDecodeError:
            return {
                "summary": response[:500],
                "risk_level": "normal",
                "findings": [],
                "recommendations": [],
                "specialist_referrals": [],
                "raw_response": response
            }

    def _format_biomarkers(self, biomarkers: List[Dict]) -> str:
        """Format biomarkers into a readable string for the AI."""
        lines = []
        current_date = None

        for bio in sorted(biomarkers, key=lambda x: x.get('date', '')):
            date = bio.get('date', 'Unknown')
            if date != current_date:
                if current_date is not None:
                    lines.append("")
                lines.append(f"=== Test Date: {date} ===")
                current_date = date

            status = "⚠️" if bio.get('status') != 'normal' else "✓"
            value = bio.get('value', 'N/A')
            unit = bio.get('unit', '')
            ref_range = bio.get('range', 'N/A')

            lines.append(f"{status} {bio.get('name', 'Unknown')}: {value} {unit} (ref: {ref_range})")

        return "\n".join(lines)


class SpecialistAgent(HealthAgent):
    """Specialist agent for specific medical areas."""

    SPECIALISTS = {
        "cardiology": {
            "name": "Cardiologist",
            "markers": ["cholesterol", "ldl", "hdl", "triglycerides", "crp", "homocysteine",
                       "lipoprotein", "apolipoprotein", "bnp", "troponin"],
            "focus": "cardiovascular health, lipid profiles, and heart disease risk factors"
        },
        "endocrinology": {
            "name": "Endocrinologist",
            "markers": ["glucose", "hba1c", "insulin", "tsh", "t3", "t4", "ft3", "ft4",
                       "cortisol", "testosterone", "estrogen", "progesterone", "dhea"],
            "focus": "hormones, thyroid function, diabetes, and metabolic health"
        },
        "hematology": {
            "name": "Hematologist",
            "markers": ["hemoglobin", "hematocrit", "rbc", "wbc", "platelets", "mcv", "mch",
                       "mchc", "rdw", "ferritin", "iron", "tibc", "transferrin", "reticulocytes"],
            "focus": "blood cells, anemia, clotting disorders, and blood health"
        },
        "hepatology": {
            "name": "Hepatologist",
            "markers": ["alt", "ast", "alp", "ggt", "bilirubin", "albumin", "protein",
                       "afp", "ammonia"],
            "focus": "liver function and liver disease"
        },
        "nephrology": {
            "name": "Nephrologist",
            "markers": ["creatinine", "bun", "urea", "egfr", "cystatin", "microalbumin",
                       "uric acid", "potassium", "sodium", "phosphorus"],
            "focus": "kidney function and renal health"
        }
    }

    def __init__(self, specialty: str, language: str = "en"):
        super().__init__(language=language)
        if specialty not in self.SPECIALISTS:
            raise ValueError(f"Unknown specialty: {specialty}")
        self.specialty = specialty
        self.config = self.SPECIALISTS[specialty]

    def get_system_prompt(self) -> str:
        return f"""You are an AI assistant with expertise in {self.config['name']} analysis.
Your focus is {self.config['focus']}.

You are NOT a doctor and cannot diagnose conditions. Your role is to:
1. Analyze biomarkers relevant to your specialty
2. Identify patterns and potential concerns
3. Explain findings in patient-friendly language
4. Suggest follow-up tests if appropriate
5. Recommend lifestyle modifications

Be thorough but avoid causing unnecessary alarm.

Respond in JSON format:
{{
    "specialty": "{self.specialty}",
    "summary": "Brief specialty-focused summary",
    "risk_level": "normal|attention|concern",
    "key_findings": [
        {{
            "marker": "Marker name",
            "value": "Value with unit",
            "reference_range": "Reference range from the test",
            "status": "normal|high|low",
            "significance": "What this means for {self.config['focus']}"
        }}
    ],
    "patterns": ["Any patterns observed across markers"],
    "recommendations": [
        {{
            "action": "Specific recommendation",
            "rationale": "Why this is suggested"
        }}
    ],
    "follow_up_tests": ["Suggested additional tests if any"]
}}"""

    def analyze(self, biomarkers: List[Dict], profile_context: str = "") -> Dict[str, Any]:
        """Analyze biomarkers relevant to this specialty."""
        # Filter to relevant markers
        relevant = self._filter_relevant_markers(biomarkers)

        if not relevant:
            return {
                "specialty": self.specialty,
                "summary": f"No {self.config['name'].lower()}-related markers found in the data.",
                "risk_level": "normal",
                "key_findings": [],
                "patterns": [],
                "recommendations": [],
                "follow_up_tests": []
            }

        biomarker_text = self._format_biomarkers(relevant)

        # Include profile context if available
        profile_section = ""
        if profile_context:
            profile_section = f"""
{profile_context}

Consider the patient's profile when analyzing results. Age, gender, BMI, lifestyle factors, and existing conditions can affect interpretation.

"""

        user_prompt = f"""{profile_section}Please analyze these lab results from a {self.config['name'].lower()} perspective:

{biomarker_text}

Focus on {self.config['focus']}. Provide your specialist analysis in JSON format."""

        response = self._call_ai(self.get_system_prompt(), user_prompt)

        try:
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            return json.loads(json_str)
        except json.JSONDecodeError:
            return {
                "specialty": self.specialty,
                "summary": response[:500],
                "risk_level": "normal",
                "key_findings": [],
                "patterns": [],
                "recommendations": [],
                "follow_up_tests": [],
                "raw_response": response
            }

    def _filter_relevant_markers(self, biomarkers: List[Dict]) -> List[Dict]:
        """Filter biomarkers to those relevant to this specialty."""
        relevant = []
        for bio in biomarkers:
            name = bio.get('name', '').lower()
            for marker in self.config['markers']:
                if marker in name:
                    relevant.append(bio)
                    break
        return relevant

    def _format_biomarkers(self, biomarkers: List[Dict]) -> str:
        """Format biomarkers into readable text."""
        lines = []
        for bio in sorted(biomarkers, key=lambda x: x.get('date', '')):
            status = "⚠️" if bio.get('status') != 'normal' else "✓"
            value = bio.get('value', 'N/A')
            unit = bio.get('unit', '')
            ref_range = bio.get('range', 'N/A')
            date = bio.get('date', 'Unknown')

            lines.append(f"{status} {bio.get('name', 'Unknown')}: {value} {unit} (ref: {ref_range}) - {date}")

        return "\n".join(lines)


class GapAnalysisAgent(HealthAgent):
    """Agent that recommends missing tests based on age, gender, and medical history."""

    SYSTEM_PROMPT = """You are an AI health screening advisor. Your role is to recommend medical tests
that a person should consider based on their age, gender, existing health data, and medical history.

You are NOT a doctor and cannot diagnose conditions. Your recommendations are for general health screening.

Consider standard medical screening guidelines such as:
- Age-appropriate cancer screenings (e.g., colonoscopy after 45, mammograms for women 40+)
- Cardiovascular risk assessments for those over 40
- Bone density tests for women over 65
- Diabetes screening based on risk factors
- Thyroid function tests based on symptoms or history
- Vitamin D levels for those with limited sun exposure
- STD screenings based on risk factors

Be specific about test names and explain why each is recommended.

Respond in JSON format:
{
    "recommended_tests": [
        {
            "test_name": "Test name",
            "category": "Category (e.g., Cancer Screening, Cardiovascular, Metabolic)",
            "priority": "high|medium|low",
            "reason": "Why this test is recommended",
            "frequency": "How often this test should be done",
            "age_recommendation": "Standard age recommendation"
        }
    ],
    "summary": "Brief summary of screening recommendations",
    "notes": "Any additional notes about the recommendations"
}"""

    def analyze(self, existing_tests: List[str], profile: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend tests based on profile and what tests are already done."""
        profile_text = self._format_profile(profile)
        tests_text = ", ".join(existing_tests) if existing_tests else "No recent tests on record"

        user_prompt = f"""Based on this patient profile and their existing test history, recommend health screening tests they should consider.

{profile_text}

Existing tests on record (no need to repeat these unless they should be redone):
{tests_text}

Provide your recommendations in JSON format. Focus on:
1. Age-appropriate screenings they may be missing
2. Tests relevant to any chronic conditions or risk factors
3. Standard preventive care tests
4. Any follow-up tests suggested by their existing results"""

        response = self._call_ai(self.SYSTEM_PROMPT, user_prompt)

        try:
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            return json.loads(json_str)
        except json.JSONDecodeError:
            return {
                "recommended_tests": [],
                "summary": response[:500],
                "notes": "",
                "raw_response": response
            }

    def _format_profile(self, profile: Dict[str, Any]) -> str:
        """Format profile for the AI prompt."""
        parts = ["Patient Profile:"]

        if profile.get("age"):
            parts.append(f"- Age: {profile['age']} years")
        elif profile.get("date_of_birth"):
            parts.append(f"- Date of Birth: {profile['date_of_birth']}")
        else:
            parts.append("- Age: Unknown")

        if profile.get("gender"):
            parts.append(f"- Gender: {profile['gender']}")
        else:
            parts.append("- Gender: Unknown")

        if profile.get("bmi"):
            bmi = profile['bmi']
            bmi_category = "underweight" if bmi < 18.5 else "normal" if bmi < 25 else "overweight" if bmi < 30 else "obese"
            parts.append(f"- BMI: {bmi} ({bmi_category})")

        if profile.get("smoking_status"):
            parts.append(f"- Smoking: {profile['smoking_status']}")

        if profile.get("alcohol_consumption"):
            parts.append(f"- Alcohol: {profile['alcohol_consumption']}")

        if profile.get("physical_activity"):
            parts.append(f"- Physical Activity: {profile['physical_activity']}")

        if profile.get("chronic_conditions") and len(profile['chronic_conditions']) > 0:
            parts.append(f"- Chronic Conditions: {', '.join(profile['chronic_conditions'])}")

        if profile.get("current_medications") and len(profile['current_medications']) > 0:
            parts.append(f"- Current Medications: {', '.join(profile['current_medications'])}")

        if profile.get("allergies") and len(profile['allergies']) > 0:
            parts.append(f"- Allergies: {', '.join(profile['allergies'])}")

        return "\n".join(parts)


class HealthAnalysisService:
    """Service to run health analysis across all agents."""

    def __init__(self, language: str = "en", profile: Dict[str, Any] = None):
        self.language = language
        self.profile = profile or {}
        self.generalist = GeneralistAgent(language=language)

    def _format_profile_context(self) -> str:
        """Format user profile data for AI context."""
        if not self.profile:
            return ""

        parts = ["Patient Profile:"]

        if self.profile.get("full_name"):
            parts.append(f"- Name: {self.profile['full_name']}")

        if self.profile.get("age"):
            parts.append(f"- Age: {self.profile['age']} years")
        elif self.profile.get("date_of_birth"):
            parts.append(f"- Date of Birth: {self.profile['date_of_birth']}")

        if self.profile.get("gender"):
            parts.append(f"- Gender: {self.profile['gender']}")

        if self.profile.get("height_cm"):
            parts.append(f"- Height: {self.profile['height_cm']} cm")

        if self.profile.get("weight_kg"):
            parts.append(f"- Weight: {self.profile['weight_kg']} kg")

        if self.profile.get("bmi"):
            bmi = self.profile['bmi']
            bmi_category = "underweight" if bmi < 18.5 else "normal" if bmi < 25 else "overweight" if bmi < 30 else "obese"
            parts.append(f"- BMI: {bmi} ({bmi_category})")

        if self.profile.get("blood_type"):
            parts.append(f"- Blood Type: {self.profile['blood_type']}")

        if self.profile.get("smoking_status"):
            parts.append(f"- Smoking: {self.profile['smoking_status']}")

        if self.profile.get("alcohol_consumption"):
            parts.append(f"- Alcohol: {self.profile['alcohol_consumption']}")

        if self.profile.get("physical_activity"):
            parts.append(f"- Physical Activity: {self.profile['physical_activity']}")

        if self.profile.get("allergies") and len(self.profile['allergies']) > 0:
            parts.append(f"- Allergies: {', '.join(self.profile['allergies'])}")

        if self.profile.get("chronic_conditions") and len(self.profile['chronic_conditions']) > 0:
            parts.append(f"- Chronic Conditions: {', '.join(self.profile['chronic_conditions'])}")

        if self.profile.get("current_medications") and len(self.profile['current_medications']) > 0:
            parts.append(f"- Current Medications: {', '.join(self.profile['current_medications'])}")

        if len(parts) == 1:
            return ""

        return "\n".join(parts)

    def run_full_analysis(self, biomarkers: List[Dict]) -> Dict[str, Any]:
        """Run general analysis and determine if specialist analyses are needed."""
        # Get profile context
        profile_context = self._format_profile_context()

        # Run general analysis first
        general_report = self.generalist.analyze(biomarkers, profile_context)

        result = {
            "general": general_report,
            "specialists": {},
            "analyzed_at": datetime.now().isoformat(),
            "language": self.language,
            "profile_used": bool(profile_context)
        }

        # Run specialist analyses based on referrals or concerning markers
        referrals = general_report.get("specialist_referrals", [])

        # Also check for out-of-range markers in each specialty area
        for specialty in SpecialistAgent.SPECIALISTS.keys():
            # Check if referred or has concerning markers
            should_analyze = specialty in referrals

            if not should_analyze:
                # Check if any concerning markers exist for this specialty
                specialist = SpecialistAgent(specialty, language=self.language)
                relevant = specialist._filter_relevant_markers(biomarkers)
                has_concerns = any(b.get('status') != 'normal' for b in relevant)
                should_analyze = has_concerns

            if should_analyze:
                specialist = SpecialistAgent(specialty, language=self.language)
                result["specialists"][specialty] = specialist.analyze(biomarkers, profile_context)

        return result

    def run_specialist_analysis(self, specialty: str, biomarkers: List[Dict]) -> Dict[str, Any]:
        """Run analysis for a specific specialty."""
        profile_context = self._format_profile_context()
        specialist = SpecialistAgent(specialty, language=self.language)
        return specialist.analyze(biomarkers, profile_context)

    def run_gap_analysis(self, existing_test_names: List[str]) -> Dict[str, Any]:
        """Run gap analysis to recommend missing tests."""
        gap_agent = GapAnalysisAgent(language=self.language)
        return gap_agent.analyze(existing_test_names, self.profile)
