import os
import datetime
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import Document, TestResult, Provider
from backend.ingest_data import get_or_create_provider

# Specific file testing
target_file = "data/raw/synevo/31033112056.pdf" 
# Ensure relative path is correct based on where we run it
# If running from root: data/raw/synevo/31033112056.pdf

if not os.path.exists(target_file):
    print(f"File not found: {target_file}")
else:
    print(f"Testing logic on {target_file}")
    
    session = SessionLocal()
    filename = os.path.basename(target_file)
    path_lower = target_file.lower()
    name_lower = filename.lower()
    
    final_provider = "ai_auto"
    if "regina" in path_lower or "regina" in name_lower:
        final_provider = "Regina Maria"
    elif "synevo" in path_lower or "synevo" in name_lower:
        final_provider = "Synevo"
    
    print(f"LOGIC CHECK: {filename} -> {final_provider}")
    
    # Update DB directly for this file to verify UI
    doc = session.query(Document).filter(Document.filename == filename).first()
    if doc:
        print(f"Updating existing doc {doc.id}...")
        provider_db = get_or_create_provider(session, final_provider)
        doc.provider_id = provider_db.id
        doc.provider = provider_db # Update relation
        
        # Hardcode date for test if regex fails on this specific file (it shouldn't if pattern matches)
        # Synevo file 31033112056.pdf doesn't have date in filename.
        # But let's check if my regex logic handles it. 
        # Actually my regex was: 20\d{2}\.\d{2}\.\d{2} or \d{2}\.\d{2}\.20\d{2}
        # This filename has NO date. So it falls back to AI.
        # If AI returns valid date, good.
        
        session.commit()
        print("Updated in DB.")
    else:
        print("Doc not found in DB.")
    
    session.close()
