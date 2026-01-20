import os
import glob
import datetime
import time
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend.models import Document, TestResult, Provider
from backend.processors.ai_parser import AIParser
from backend.analysis.mapper import BiomarkerMapper
import pdfplumber

# Hardcoded key as per session context
# In production, use os.environ variables
# OPENAI_API_KEY loaded from .env

def get_or_create_provider(session: Session, name: str) -> Provider:
    p = session.query(Provider).filter(Provider.name == name).first()
    if not p:
        p = Provider(name=name, username="dragusinb@gmail.com")
        session.add(p)
        session.commit()
    return p

def run_ingestion(force=True):
    print("--- STARTING AI INGESTION (PARSER 4.0) ---")
    session = SessionLocal()
    
    # 1. Setup Provider (Generic AI Provider)
    ai_provider = get_or_create_provider(session, "ai_auto")
    
    # 2. Find Files
    root_dir = os.path.abspath("data/raw")
    pdf_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, file))
    
    print(f"Found {len(pdf_files)} PDFs.")
    
    # 3. Initialize Parser
    parser = AIParser()
    
    # 4. Process Each
    for file_path in pdf_files:
        filename = os.path.basename(file_path)
        
        # Deduplication
        existing = session.query(Document).filter_by(filename=filename).first()
        if existing:
            if not force:
                print(f"Skipping {filename}")
                continue
            else:
                print(f"Re-ingesting {filename}...")
                session.query(TestResult).filter_by(document_id=existing.id).delete()
                session.delete(existing)
                session.commit()
        else:
            print(f"Ingesting {filename}...")

        # Extract Text
        try:
            full_text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    full_text += (page.extract_text() or "") + "\n"
        except Exception as e:
            print(f"  [!] PDF Error: {e}")
            continue

        # AI Parse
        print(f"  -> Sending to AI...")
        start_t = time.time()
        parse_res = parser.parse_text(full_text)
        duration = time.time() - start_t
        
        if "error" in parse_res:
            print(f"  [!] AI Error: {parse_res['error']}")
            continue
            
        results = parse_res.get("results", [])
        print(f"  -> Extracted {len(results)} results in {duration:.1f}s")
        
        if results:
            # 1. Extract Metadata from AI
            ai_meta = parse_res.get("metadata", {})
            
            # 2. Extract Metadata from Filename (STRONGER SIGNAL)
            # e.g. data/raw/synevo/31033112056.pdf -> Provider: Synevo
            # e.g. result_2025.12.08.pdf -> Date: 2025-12-08
            
            path_lower = file_path.lower()
            name_lower = filename.lower()
            
            # --- Provider Detection ---
            final_provider = "ai_auto"
            if "regina" in path_lower or "regina" in name_lower:
                final_provider = "Regina Maria"
            elif "synevo" in path_lower or "synevo" in name_lower:
                final_provider = "Synevo"
            else:
                # Fallback to AI
                final_provider = ai_meta.get("provider", "ai_auto")

            # --- Date Detection ---
            # User Request: "date for the documents should be the date of the analysis not the date of the crawling"
            # Priority: 
            # 1. AI Content Extraction (Metadata from text)
            # 2. Filename Regex (Fallback)
            
            final_date = datetime.datetime.now() # Default
            date_found = False
            
            # 1. Try AI Date (Content)
            ai_date_str = ai_meta.get("date")
            if ai_date_str:
                try:
                    # AI usually returns ISO YYYY-MM-DD
                    final_date = datetime.datetime.strptime(ai_date_str, "%Y-%m-%d")
                    date_found = True
                    print(f"DEBUG: Using AI Date from content: {final_date.date()}")
                except: 
                    print(f"DEBUG: Failed to parse AI date: {ai_date_str}")
                    pass
            
            if not date_found:
                # 2. Key Regex (YYYY.MM.DD) provided it's NOT just the crawl date?
                # Actually, user says "date of crawling" is wrong. 
                # Be careful with filename dates if they are crawl timestamps.
                # However, if AI failed, this is better than "Today".
                
                import re
                match_ymd = re.search(r"20\d{2}\.\d{2}\.\d{2}", filename)
                if match_ymd:
                    try:
                        final_date = datetime.datetime.strptime(match_ymd.group(0), "%Y.%m.%d")
                        date_found = True
                    except: pass
                
                if not date_found:
                     match_dmy = re.search(r"\d{2}\.\d{2}\.20\d{2}", filename)
                     if match_dmy:
                         try:
                            final_date = datetime.datetime.strptime(match_dmy.group(0), "%d.%m.%Y")
                            date_found = True
                         except: pass
            
            # Get/Create DB Provider
            print(f"DEBUG: File={filename} | Path={path_lower} -> Provider={final_provider} | Date={final_date}")
            db_provider = get_or_create_provider(session, final_provider)
        
            doc = Document(
                provider_id=db_provider.id,
                filename=filename,
                file_path=file_path,
                upload_date=datetime.datetime.now(),
                document_date=final_date, 
                file_type="PDF",
                category="AI_Parsed"
            )
            session.add(doc)
            session.commit()
            
            for res in results:
                # Map Name
                raw_name = res.get("test_name", "Unknown")
                std_name = BiomarkerMapper.map_to_standard(raw_name)
                
                # Validation of Value
                val = res.get("value")
                
                tr = TestResult(
                    document_id=doc.id,
                    test_name=std_name,
                    value=str(val),
                    unit=res.get("unit"),
                    reference_range=res.get("reference_range"),
                    flags=res.get("flags") or "NORMAL",
                    category="Global"
                )
                session.add(tr)
            session.commit()
            print("  -> Saved.")
            
    session.close()
    print("--- INGESTION COMPLETE ---")

if __name__ == "__main__":
    run_ingestion()
