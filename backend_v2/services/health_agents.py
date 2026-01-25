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
3. Highlight TRENDS if multiple tests of the same biomarker are available
4. Consider DATA AGE - older results may no longer be relevant
5. Note when abnormal values have NORMALIZED in recent tests (condition may be resolved)
6. Determine which specialist consultations are warranted based on findings
7. Provide general lifestyle recommendations

IMPORTANT DATA AGE CONSIDERATIONS:
- Results older than 1 year should be treated as historical context, not current status
- If a biomarker was abnormal in the past but is normal in recent tests, note the improvement
- If data is very old (2+ years), recommend re-testing to get current values
- Focus your main analysis on the most recent results
- Only recommend specialists for RECENT abnormalities (within last year)

SPECIALIST SELECTION:
You may recommend these specialists when warranted:
- cardiology: cardiovascular health, lipid profiles, heart disease risk
- endocrinology: hormones, thyroid, diabetes, metabolic health
- hematology: blood cells, anemia, clotting disorders
- hepatology: liver function and disease
- nephrology: kidney function and renal health
- infectious_disease: infections, inflammation markers, immune response

Only recommend specialists when there's a clear, recent clinical indication.
Provide specific reasoning for each recommendation.

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
    "specialist_referrals": {
        "recommended": ["cardiology", "endocrinology"],
        "reasoning": {
            "cardiology": "Specific reason why cardiology review is needed based on recent results",
            "endocrinology": "Specific reason for endocrinology based on findings"
        }
    }
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

    def _get_data_age_summary(self, biomarkers: List[Dict]) -> str:
        """Generate a summary of data age and date range."""
        from datetime import datetime, timedelta

        dates = []
        for bio in biomarkers:
            date_str = bio.get('date', '')
            if date_str and date_str != 'Unknown':
                try:
                    dates.append(datetime.strptime(date_str, '%Y-%m-%d'))
                except:
                    pass

        if not dates:
            return "Data age: Unknown dates"

        oldest = min(dates)
        newest = max(dates)
        today = datetime.now()
        newest_age_days = (today - newest).days

        summary = f"Data Range: {oldest.strftime('%Y-%m-%d')} to {newest.strftime('%Y-%m-%d')}"

        if newest_age_days > 365:
            summary += f"\n⚠️ WARNING: Most recent data is {newest_age_days // 30} months old. Consider re-testing."
        elif newest_age_days > 180:
            summary += f"\n⚠️ Note: Most recent data is {newest_age_days // 30} months old."

        return summary

    def _format_biomarkers(self, biomarkers: List[Dict]) -> str:
        """Format biomarkers into a readable string for the AI."""
        lines = []

        # Add data age summary at the top
        lines.append(self._get_data_age_summary(biomarkers))
        lines.append("")

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
        },
        "infectious_disease": {
            "name": "Infectious Disease Specialist",
            "markers": ["wbc", "leucocite", "neutrofil", "limfocit", "monocit", "procalcitonin",
                       "crp", "vsh", "esr", "streptococ", "borrelia", "antigen"],
            "focus": "infections, inflammation markers, and immune response"
        }
    }

    def __init__(self, specialty: str, language: str = "en"):
        super().__init__(language=language)
        if specialty not in self.SPECIALISTS:
            raise ValueError(f"Unknown specialty: {specialty}")
        self.specialty = specialty
        self.config = self.SPECIALISTS[specialty]

    def get_system_prompt(self, generalist_context: str = "") -> str:
        generalist_section = ""
        if generalist_context:
            generalist_section = f"""
REFERRAL CONTEXT:
{generalist_context}

Use this context to focus your specialist assessment.

"""

        return f"""You are an AI {self.config['name']} specialist assistant providing a focused review
of laboratory results. You are analyzing these results as a specialist would, looking for patterns
and concerns specific to {self.config['focus']}.

IMPORTANT DISCLAIMER: You are an AI assistant, not a licensed physician. Your analysis is for
educational purposes and should not replace professional medical consultation.

YOUR SPECIALIST PERSPECTIVE:
As a {self.config['name']} specialist, you should:
1. Review all relevant biomarkers through the lens of {self.config['focus']}
2. Identify clinical patterns that may warrant further investigation
3. Consider how findings relate to each other (e.g., multiple liver enzymes elevated together)
4. Assess trends over time when multiple measurements are available
5. Provide actionable recommendations while being appropriately cautious
6. Explain findings in terms a patient can understand

DATA TIMELINE AWARENESS:
- Each result includes a test date - always note this in your analysis
- Distinguish between current findings (< 6 months) and historical context (> 1 year)
- If a concerning value has normalized in recent tests, note the improvement
- For old data (> 2 years), recommend confirmatory re-testing before clinical decisions
- Focus your clinical assessment on the most RECENT laboratory values
{generalist_section}
Respond in JSON format:
{{
    "specialty": "{self.specialty}",
    "summary": "Concise specialty-focused clinical impression",
    "risk_level": "normal|attention|concern",
    "key_findings": [
        {{
            "marker": "Biomarker name",
            "value": "Measured value with unit",
            "reference_range": "Laboratory reference range",
            "date": "Test date for this result",
            "status": "normal|high|low",
            "clinical_significance": "What this means in the context of {self.config['focus']}"
        }}
    ],
    "clinical_patterns": ["Observed patterns across related markers"],
    "recommendations": [
        {{
            "priority": "high|medium|low",
            "action": "Specific clinical recommendation",
            "rationale": "Clinical reasoning for this recommendation"
        }}
    ],
    "suggested_follow_up": ["Additional tests or evaluations that may be warranted"]
}}"""

    def analyze(self, biomarkers: List[Dict], profile_context: str = "", generalist_context: str = "") -> Dict[str, Any]:
        """Analyze biomarkers relevant to this specialty.

        Args:
            biomarkers: List of biomarker dicts with name, value, unit, range, date, status
            profile_context: Patient profile information
            generalist_context: Findings from the generalist analysis relevant to this specialty
        """
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

        response = self._call_ai(self.get_system_prompt(generalist_context), user_prompt)

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
        """Format biomarkers into readable text with dates prominently displayed."""
        # Group by date for clearer timeline
        from collections import defaultdict
        by_date = defaultdict(list)

        for bio in biomarkers:
            date = bio.get('date', 'Unknown')
            by_date[date].append(bio)

        lines = []
        for date in sorted(by_date.keys(), reverse=True):  # Most recent first
            lines.append(f"\n=== {date} ===")
            for bio in by_date[date]:
                status = "⚠️" if bio.get('status') != 'normal' else "✓"
                value = bio.get('value', 'N/A')
                unit = bio.get('unit', '')
                ref_range = bio.get('range', 'N/A')
                lines.append(f"  {status} {bio.get('name', 'Unknown')}: {value} {unit} (ref: {ref_range})")

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

    def _is_recent(self, biomarker: Dict, max_age_days: int = 365) -> bool:
        """Check if a biomarker is from recent data (within max_age_days)."""
        date_str = biomarker.get('date', '')
        if not date_str or date_str == 'Unknown':
            return False  # Treat unknown dates as not recent
        try:
            bio_date = datetime.strptime(date_str, '%Y-%m-%d')
            age_days = (datetime.now() - bio_date).days
            return age_days <= max_age_days
        except:
            return False

    def _extract_generalist_context_for_specialty(self, general_report: Dict, specialty: str) -> str:
        """Extract relevant generalist findings for a specific specialty."""
        context_parts = []

        # First, check if generalist provided specific reasoning for this specialty
        referrals = general_report.get("specialist_referrals", {})

        # Handle both old format (list) and new format (dict with reasoning)
        if isinstance(referrals, dict):
            reasoning = referrals.get("reasoning", {})
            if specialty in reasoning:
                context_parts.append(f"Generalist's reason for referral: {reasoning[specialty]}")
        elif isinstance(referrals, list) and specialty in referrals:
            context_parts.append(f"Referred by generalist analysis.")

        # Also extract relevant findings based on keywords
        findings = general_report.get("findings", [])

        # Map specialties to relevant categories
        specialty_categories = {
            "cardiology": ["cardiovascular", "lipid", "heart", "cardiac", "cholesterol"],
            "endocrinology": ["diabetes", "metabolic", "thyroid", "hormone", "glucose"],
            "hematology": ["blood", "anemia", "hematology", "hemoglobin", "cell"],
            "hepatology": ["liver", "hepatic"],
            "nephrology": ["kidney", "renal"],
            "infectious_disease": ["infection", "inflammation", "immune", "bacteria", "virus"]
        }

        keywords = specialty_categories.get(specialty, [])
        relevant_findings = []

        for finding in findings:
            category = finding.get("category", "").lower()
            explanation = finding.get("explanation", "").lower()
            # Check if finding is relevant to this specialty
            if any(kw in category or kw in explanation for kw in keywords):
                relevant_findings.append(f"- {finding.get('category', 'Finding')}: {finding.get('explanation', '')}")

        if relevant_findings:
            context_parts.append("Related findings:\n" + "\n".join(relevant_findings))

        return "\n\n".join(context_parts) if context_parts else ""

    def run_full_analysis(self, biomarkers: List[Dict]) -> Dict[str, Any]:
        """Run general analysis and determine if specialist analyses are needed.

        The generalist AI determines which specialists should be consulted based on its analysis.
        We also have a fallback to check for recent abnormal markers in case generalist missed something.
        """
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

        # Get specialist referrals from generalist - handle both old and new format
        raw_referrals = general_report.get("specialist_referrals", [])
        if isinstance(raw_referrals, dict):
            # New format: {"recommended": [...], "reasoning": {...}}
            referrals = set(raw_referrals.get("recommended", []))
        elif isinstance(raw_referrals, list):
            # Old format: ["cardiology", "endocrinology"]
            referrals = set(raw_referrals)
        else:
            referrals = set()

        # Track which specialists we'll run and why
        specialists_to_run = {}

        # First pass: Add all specialists recommended by generalist
        for specialty in referrals:
            if specialty in SpecialistAgent.SPECIALISTS:
                specialists_to_run[specialty] = "generalist_referral"

        # Second pass: Check for recent concerning markers as fallback
        for specialty in SpecialistAgent.SPECIALISTS.keys():
            if specialty in specialists_to_run:
                continue  # Already added via generalist referral

            # Check if any RECENT concerning markers exist for this specialty
            specialist = SpecialistAgent(specialty, language=self.language)
            relevant = specialist._filter_relevant_markers(biomarkers)
            recent_concerns = [
                b for b in relevant
                if b.get('status') != 'normal' and self._is_recent(b, max_age_days=365)
            ]
            if len(recent_concerns) > 0:
                specialists_to_run[specialty] = "marker_fallback"

        # Run specialist analyses
        for specialty, trigger_reason in specialists_to_run.items():
            specialist = SpecialistAgent(specialty, language=self.language)
            # Extract generalist findings relevant to this specialty
            generalist_context = self._extract_generalist_context_for_specialty(general_report, specialty)
            specialist_result = specialist.analyze(biomarkers, profile_context, generalist_context)
            # Add trigger reason for debugging/transparency
            specialist_result["triggered_by"] = trigger_reason
            result["specialists"][specialty] = specialist_result

        return result

    def run_specialist_analysis(self, specialty: str, biomarkers: List[Dict], generalist_context: str = "") -> Dict[str, Any]:
        """Run analysis for a specific specialty."""
        profile_context = self._format_profile_context()
        specialist = SpecialistAgent(specialty, language=self.language)
        return specialist.analyze(biomarkers, profile_context, generalist_context)

    def run_gap_analysis(self, existing_test_names: List[str]) -> Dict[str, Any]:
        """Run gap analysis to recommend missing tests."""
        gap_agent = GapAnalysisAgent(language=self.language)
        return gap_agent.analyze(existing_test_names, self.profile)
