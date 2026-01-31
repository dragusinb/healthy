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

SPECIALIST REFERRALS:
Based on the biomarker findings, you should recommend specialist consultations when warranted.
You can recommend ANY type of medical specialist - common ones include:
- Cardiologist (heart, lipids, cardiovascular)
- Endocrinologist (hormones, thyroid, diabetes)
- Hematologist (blood cells, anemia, clotting)
- Hepatologist (liver function)
- Nephrologist (kidney function)
- Gastroenterologist (digestive system)
- Immunologist (immune system)
- Oncologist (cancer markers)
- Rheumatologist (autoimmune, inflammation)
- Pulmonologist (lung function)
- Neurologist (nervous system)
- Dermatologist (skin-related markers)
- Infectious Disease Specialist (infections)

But you are NOT limited to this list - recommend whatever specialist is most appropriate
for the findings. Only recommend specialists when there's a clear, recent clinical indication.

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
    "specialist_referrals": [
        {
            "specialty": "cardiology",
            "specialist_name": "Cardiologist",
            "focus_area": "cardiovascular health, lipid profiles, and heart disease risk",
            "relevant_markers": ["cholesterol", "LDL", "HDL", "triglycerides"],
            "reasoning": "Specific reason why this specialist review is needed based on recent results"
        }
    ]
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
    """Dynamic specialist agent that can represent any medical specialty.

    The specialist configuration is provided dynamically by the generalist,
    allowing for flexible specialist recommendations based on the actual findings.
    """

    def __init__(self, specialty: str, specialist_name: str, focus_area: str,
                 relevant_markers: List[str] = None, language: str = "en"):
        """Initialize a dynamic specialist agent.

        Args:
            specialty: The specialty identifier (e.g., "cardiology")
            specialist_name: Display name (e.g., "Cardiologist")
            focus_area: What this specialist focuses on
            relevant_markers: Optional list of marker keywords to filter biomarkers
            language: Response language ("en" or "ro")
        """
        super().__init__(language=language)
        self.specialty = specialty
        self.config = {
            "name": specialist_name,
            "focus": focus_area,
            "markers": relevant_markers or []
        }

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
        """Filter biomarkers to those relevant to this specialty.

        If no markers are specified in config, returns all biomarkers
        (specialist will focus on what's relevant based on their expertise).
        """
        # If no specific markers defined, return all biomarkers
        if not self.config.get('markers'):
            return biomarkers

        relevant = []
        for bio in biomarkers:
            name = bio.get('name', '').lower()
            for marker in self.config['markers']:
                if marker.lower() in name:
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

CRITICAL: You MUST provide REAL, SPECIFIC recommendations based on the patient's profile.
DO NOT use placeholder text like "Test name" or "Brief summary" - write actual medical test names and real explanations.

Respond in JSON format with this structure:
{
    "recommended_tests": [
        {
            "test_name": "Actual test name like 'Lipid Panel' or 'HbA1c'",
            "category": "Cardiovascular|Cancer Screening|Metabolic|General|Infectious",
            "priority": "high|medium|low",
            "reason": "Specific explanation why this test is important for this patient",
            "frequency": "e.g., 'Every 1-2 years' or 'Once at age 50'",
            "age_recommendation": "e.g., 'Recommended starting at age 40'"
        }
    ],
    "summary": "Write 2-3 sentences summarizing the key screening recommendations for this specific patient based on their age, gender, and risk factors",
    "notes": "Any additional personalized notes or caveats"
}

EXAMPLE of a GOOD summary: "Based on your age of 39 and male gender, cardiovascular health monitoring becomes increasingly important. A comprehensive lipid panel and fasting glucose test are recommended to establish baseline values before age 40. Consider also a thyroid function test given no recent thyroid markers in your records."

EXAMPLE of a BAD summary (DO NOT DO THIS): "Brief summary of screening recommendations" - this is placeholder text!

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
4. Any follow-up tests suggested by their existing results

IMPORTANT: Write a REAL, personalized summary for this specific patient - do NOT use placeholder text."""

        response = self._call_ai(self.SYSTEM_PROMPT, user_prompt)

        try:
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            result = json.loads(json_str)

            # Validate that summary is not placeholder text
            summary = result.get("summary", "")
            placeholder_indicators = [
                "brief summary",
                "summary of screening",
                "placeholder",
                "test name",
                "[insert",
                "example"
            ]
            if any(indicator in summary.lower() for indicator in placeholder_indicators):
                # Summary looks like placeholder - generate a fallback
                age = profile.get("age", "unknown age")
                gender = profile.get("gender", "unknown gender")
                test_count = len(result.get("recommended_tests", []))
                if self.language == "ro":
                    result["summary"] = f"Pe baza profilului dumneavoastră ({gender}, {age} ani), am identificat {test_count} teste de screening recomandate. Consultați lista de mai jos pentru detalii și priorități."
                else:
                    result["summary"] = f"Based on your profile ({gender}, age {age}), we have identified {test_count} recommended screening tests. See the list below for details and priorities."

            return result
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

        The generalist AI dynamically determines which specialists should be consulted
        based on its analysis. Specialists are created on-the-fly based on the
        generalist's recommendations - there is no predefined specialist list.
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

        # Get specialist referrals from generalist
        # New format: list of specialist objects with full configuration
        raw_referrals = general_report.get("specialist_referrals", [])

        # Handle different response formats for backwards compatibility
        specialist_configs = []
        if isinstance(raw_referrals, list):
            for ref in raw_referrals:
                if isinstance(ref, dict) and "specialty" in ref:
                    # New dynamic format with full specialist config
                    specialist_configs.append(ref)
                elif isinstance(ref, str):
                    # Old format: just specialty name - create default config
                    specialist_configs.append({
                        "specialty": ref,
                        "specialist_name": ref.replace("_", " ").title(),
                        "focus_area": f"{ref} related health concerns",
                        "relevant_markers": [],
                        "reasoning": "Recommended by generalist"
                    })
        elif isinstance(raw_referrals, dict):
            # Legacy format: {"recommended": [...], "reasoning": {...}}
            recommended = raw_referrals.get("recommended", [])
            reasoning = raw_referrals.get("reasoning", {})
            for spec in recommended:
                specialist_configs.append({
                    "specialty": spec,
                    "specialist_name": spec.replace("_", " ").title(),
                    "focus_area": f"{spec} related health concerns",
                    "relevant_markers": [],
                    "reasoning": reasoning.get(spec, "Recommended by generalist")
                })

        # Run specialist analyses dynamically
        for spec_config in specialist_configs:
            specialty = spec_config.get("specialty", "unknown")
            specialist_name = spec_config.get("specialist_name", specialty.title())
            focus_area = spec_config.get("focus_area", "")
            relevant_markers = spec_config.get("relevant_markers", [])
            reasoning = spec_config.get("reasoning", "")

            # Create specialist agent with dynamic configuration
            specialist = SpecialistAgent(
                specialty=specialty,
                specialist_name=specialist_name,
                focus_area=focus_area,
                relevant_markers=relevant_markers,
                language=self.language
            )

            # Build generalist context for this specialist
            generalist_context = f"Referral reason: {reasoning}"
            additional_context = self._extract_generalist_context_for_specialty(general_report, specialty)
            if additional_context:
                generalist_context += f"\n\n{additional_context}"

            # Run specialist analysis
            specialist_result = specialist.analyze(biomarkers, profile_context, generalist_context)
            specialist_result["triggered_by"] = "generalist_referral"
            specialist_result["referral_reasoning"] = reasoning
            result["specialists"][specialty] = specialist_result

        return result

    def run_specialist_analysis(self, specialty: str, biomarkers: List[Dict],
                                specialist_name: str = None, focus_area: str = None,
                                relevant_markers: List[str] = None,
                                generalist_context: str = "") -> Dict[str, Any]:
        """Run analysis for a specific specialty with dynamic configuration.

        Args:
            specialty: Specialty identifier (e.g., "cardiology")
            biomarkers: List of biomarker data
            specialist_name: Display name (defaults to specialty title)
            focus_area: What this specialist focuses on
            relevant_markers: Optional marker keywords for filtering
            generalist_context: Context from generalist analysis
        """
        profile_context = self._format_profile_context()
        specialist = SpecialistAgent(
            specialty=specialty,
            specialist_name=specialist_name or specialty.replace("_", " ").title(),
            focus_area=focus_area or f"{specialty} related health concerns",
            relevant_markers=relevant_markers or [],
            language=self.language
        )
        return specialist.analyze(biomarkers, profile_context, generalist_context)

    def run_gap_analysis(self, existing_test_names: List[str]) -> Dict[str, Any]:
        """Run gap analysis to recommend missing tests."""
        gap_agent = GapAnalysisAgent(language=self.language)
        return gap_agent.analyze(existing_test_names, self.profile)
