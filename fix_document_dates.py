"""
Script to reprocess all documents and extract correct test dates.
Run this once to fix existing documents that have upload_date instead of test_date.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from backend_v2.database import SessionLocal
from backend_v2.models import Document
from backend_v2.services.ai_parser import AIParser
import pdfplumber
import datetime

def fix_document_dates():
    db = SessionLocal()
    parser = AIParser()

    # Get all documents
    documents = db.query(Document).all()
    print(f"Found {len(documents)} documents to check")

    fixed = 0
    for doc in documents:
        if not os.path.exists(doc.file_path):
            print(f"  Skipping {doc.filename} - file not found at {doc.file_path}")
            continue

        # Extract text from PDF
        try:
            full_text = ""
            with pdfplumber.open(doc.file_path) as pdf:
                for page in pdf.pages:
                    full_text += (page.extract_text() or "") + "\n"
        except Exception as e:
            print(f"  Error reading {doc.filename}: {e}")
            continue

        if not full_text.strip():
            print(f"  Skipping {doc.filename} - no text extracted")
            continue

        # Parse with AI to get metadata
        result = parser.parse_text(full_text)
        metadata = result.get("metadata", {})

        if "date" in metadata:
            try:
                extracted_date = datetime.datetime.strptime(metadata["date"], "%Y-%m-%d")
                if doc.document_date != extracted_date:
                    old_date = doc.document_date
                    doc.document_date = extracted_date
                    print(f"  Fixed {doc.filename}: {old_date} -> {extracted_date.date()}")
                    fixed += 1
            except Exception as e:
                print(f"  Could not parse date for {doc.filename}: {metadata.get('date')} - {e}")
        else:
            print(f"  No date found in {doc.filename}")

    db.commit()
    db.close()
    print(f"\nDone! Fixed {fixed} document dates.")

if __name__ == "__main__":
    fix_document_dates()
