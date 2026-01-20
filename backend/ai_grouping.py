import os
import json
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from backend.database import SessionLocal
from backend.models import TestResult, BiomarkerAlias
from openai import OpenAI

# Keep the key here for the session
# OPENAI_API_KEY loaded from .env

def run_grouping():
    print("--- STARTING AI BIOMARKER GROUPING ---")
    session = SessionLocal()
    
    # 1. Get all unique names
    unique_names = [r[0] for r in session.query(TestResult.test_name).distinct().all()]
    print(f"Found {len(unique_names)} unique biomarker names.")
    
    if len(unique_names) < 2:
        print("Not enough data to group.")
        return

    # 2. Call OpenAI
    client = OpenAI()
    
    prompt = f"""
    I have a list of raw biological test names from medical reports (some in Romanian, some English, some abbreviated).
    Your job is to GROUP synonyms together under a single CANONICAL ENGLISH NAME.
    
    Input List:
    {json.dumps(unique_names)}
    
    Rules:
    1. Output a JSON object where Key = Canonical English Name, Value = List of raw strings from the input that verify match this.
    2. Be aggressive with synonyms: "VSH" == "ESR" == "Viteza de sedimentare".
    3. If a name is already perfect, map it to itself (Key=Name, Value=[Name]).
    4. Ignore useless strings (numbers, dates) if they slipped in, by not including them.
    5. Prefer full names: "Hemoglobin" over "Hb".
    
    Example Output:
    {{
        "Hepatitis B Viral DNA": ["ADN Viral Hep B", "Hepatitis B DNA quant"],
        "Hemoglobin": ["HGB", "Hemoglobina"]
    }}
    """
    
    print("Sending to OpenAI...")
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a medical terminologist helper. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        content = completion.choices[0].message.content
        mapping = json.loads(content)
        
    except Exception as e:
        print(f"AI Error: {e}")
        return

    # 3. Apply Updates
    print("Applying updates to Database...")
    updates_count = 0
    
    # Extract inner dictionary if nested (gpt sometimes returns {"groups": ...})
    final_map = mapping if not "groups" in mapping else mapping["groups"]
    if "mappings" in mapping: final_map = mapping["mappings"]
    
    for canonical, aliases in final_map.items():
        # Ensure canonical is cleaner
        canonical = canonical.strip()
        
        for alias in aliases:
            # 3a. Save to BiomarkerAlias table for future ingestion
            existing_alias = session.query(BiomarkerAlias).filter_by(alias=alias).first()
            if not existing_alias:
                session.add(BiomarkerAlias(alias=alias, standardized_name=canonical))
            
            # 3b. Update existing records in TestResult
            # We use a bulk update for speed
            if alias != canonical:
                result = session.query(TestResult).filter(TestResult.test_name == alias).update(
                    {TestResult.test_name: canonical},
                    synchronize_session=False
                )
                updates_count += result
                
    session.commit()
    session.close()
    print(f"--- DONE. Updated {updates_count} records. ---")

if __name__ == "__main__":
    run_grouping()
