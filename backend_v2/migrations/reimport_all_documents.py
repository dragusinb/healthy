#!/usr/bin/env python3
"""
Re-import all documents from disk with proper AI processing.
This script:
1. Clears all documents and test results for specified users
2. Scans PDF files on disk
3. Re-imports each with AI processing to extract correct dates and biomarkers

Deduplication: Uses MD5 hash of file content to detect true duplicates.
Same file downloaded multiple times = skip (same hash)
Different tests on same day = import both (different hashes)
"""
import os
import sys
import datetime
import hashlib
import pdfplumber

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from database import SessionLocal
from models import Document, TestResult, User
from services.ai_parser import AIParser
from services.biomarker_normalizer import get_canonical_name

def reimport_user_documents(user_id: int, dry_run: bool = False):
    """Re-import all documents for a user from disk."""
    db = SessionLocal()
    parser = AIParser()

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"User {user_id} not found!")
            return

        print(f"\n{'='*60}")
        print(f"Re-importing documents for user {user_id} ({user.email})")
        print(f"{'='*60}")

        # Find all PDF directories for this user
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), f"../../data/raw/{user_id}"))

        if not os.path.exists(base_dir):
            print(f"No data directory found: {base_dir}")
            return

        # Collect all PDF files
        pdf_files = []
        for provider_dir in os.listdir(base_dir):
            provider_path = os.path.join(base_dir, provider_dir)
            if os.path.isdir(provider_path):
                for filename in os.listdir(provider_path):
                    if filename.lower().endswith('.pdf'):
                        pdf_files.append({
                            "path": os.path.join(provider_path, filename),
                            "filename": filename,
                            "provider": provider_dir.replace("_", " ").title()
                        })

        print(f"Found {len(pdf_files)} PDF files on disk")

        # Get current document count
        current_docs = db.query(Document).filter(Document.user_id == user_id).count()
        current_biomarkers = db.query(TestResult).join(Document).filter(Document.user_id == user_id).count()
        print(f"Current in DB: {current_docs} documents, {current_biomarkers} biomarkers")

        if dry_run:
            print("\n[DRY RUN] Would delete all documents and re-import")
            for pdf in pdf_files[:5]:
                print(f"  Would process: {pdf['filename']}")
            print(f"  ... and {len(pdf_files) - 5} more")
            return

        # Delete existing documents and biomarkers
        print("\nDeleting existing documents and biomarkers...")
        db.query(TestResult).filter(
            TestResult.document_id.in_(
                db.query(Document.id).filter(Document.user_id == user_id)
            )
        ).delete(synchronize_session=False)
        db.query(Document).filter(Document.user_id == user_id).delete()
        db.commit()
        print("Deleted all existing documents")

        # Process each PDF
        imported = 0
        failed = 0
        skipped_duplicates = 0
        seen_hashes = {}  # Track file content hashes to detect true duplicates

        # First pass: compute hashes for all files
        print("\nComputing file hashes...")
        file_hashes = {}
        for pdf_info in pdf_files:
            with open(pdf_info['path'], 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            file_hashes[pdf_info['path']] = file_hash

        for i, pdf_info in enumerate(pdf_files):
            print(f"\n[{i+1}/{len(pdf_files)}] Processing: {pdf_info['filename']}")

            try:
                # Extract text from PDF
                full_text = ""
                with pdfplumber.open(pdf_info['path']) as pdf:
                    for page in pdf.pages:
                        full_text += (page.extract_text() or "") + "\n"

                if not full_text.strip():
                    print(f"  WARNING: No text extracted")
                    failed += 1
                    continue

                # Parse with AI
                result = parser.parse_text(full_text)

                if "error" in result:
                    print(f"  ERROR: AI parsing failed: {result['error']}")
                    failed += 1
                    continue

                # Extract metadata
                meta = result.get("metadata", {})
                patient_info = result.get("patient_info", {})
                biomarkers = result.get("results", [])

                # Determine provider
                provider = meta.get("provider", pdf_info["provider"])
                if provider == "Unknown":
                    provider = pdf_info["provider"]

                # Extract date
                doc_date = None
                date_str = meta.get("date")
                if date_str:
                    try:
                        doc_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        pass

                if not doc_date:
                    # Try to extract from filename
                    print(f"  WARNING: No date extracted, using file date")
                    doc_date = datetime.datetime.fromtimestamp(os.path.getmtime(pdf_info['path']))

                # Check for duplicate by file content hash
                # Same file downloaded multiple times = skip
                # Different tests on same day = import both
                file_hash = file_hashes[pdf_info['path']]
                if file_hash in seen_hashes:
                    print(f"  SKIP: Duplicate content (hash match with {seen_hashes[file_hash]})")
                    skipped_duplicates += 1
                    continue

                # Extract CNP prefix (first 7 digits) for patient identification
                cnp_prefix = patient_info.get("cnp_prefix")
                if cnp_prefix and len(cnp_prefix) >= 7:
                    cnp_prefix = cnp_prefix[:7]  # Ensure only 7 digits
                else:
                    cnp_prefix = None

                # Create document
                doc = Document(
                    user_id=user_id,
                    filename=pdf_info['filename'],
                    file_path=pdf_info['path'],
                    provider=provider,
                    document_date=doc_date,
                    upload_date=datetime.datetime.now(),
                    is_processed=True,
                    patient_name=patient_info.get("full_name"),
                    patient_cnp_prefix=cnp_prefix,
                    file_hash=file_hash
                )
                db.add(doc)
                db.flush()  # Get doc.id

                seen_hashes[file_hash] = pdf_info['filename']

                # Create biomarkers
                biomarker_count = 0
                for bio in biomarkers:
                    test_name = bio.get("test_name")
                    if not test_name:
                        continue

                    # Get numeric value
                    numeric_val = bio.get("numeric_value")
                    if numeric_val is None:
                        try:
                            numeric_val = float(bio.get("value", "").replace(",", "."))
                        except (ValueError, TypeError, AttributeError):
                            numeric_val = None

                    tr = TestResult(
                        document_id=doc.id,
                        test_name=test_name,
                        canonical_name=get_canonical_name(test_name),
                        value=str(bio.get("value", "")),
                        numeric_value=numeric_val,
                        unit=bio.get("unit"),
                        reference_range=bio.get("reference_range"),
                        flags=bio.get("flags", "NORMAL")
                    )
                    db.add(tr)
                    biomarker_count += 1

                # Auto-populate user's blood type if found and not already set
                blood_type = patient_info.get("blood_type")
                if blood_type and not user.blood_type:
                    valid_blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
                    if blood_type in valid_blood_types:
                        user.blood_type = blood_type
                        print(f"  -> Updated user blood type to: {blood_type}")

                db.commit()
                imported += 1
                print(f"  OK: Date={doc_date.strftime('%Y-%m-%d')}, Biomarkers={biomarker_count}, Provider={provider}, CNP={cnp_prefix or 'N/A'}")

            except Exception as e:
                print(f"  ERROR: {e}")
                failed += 1
                db.rollback()
                continue

        print(f"\n{'='*60}")
        print(f"COMPLETE: Imported {imported}, Failed {failed}, Skipped duplicates {skipped_duplicates}")

        # Final counts
        final_docs = db.query(Document).filter(Document.user_id == user_id).count()
        final_biomarkers = db.query(TestResult).join(Document).filter(Document.user_id == user_id).count()
        print(f"Final in DB: {final_docs} documents, {final_biomarkers} biomarkers")
        print(f"{'='*60}\n")

    finally:
        db.close()


def reimport_all_users(dry_run: bool = False):
    """Re-import documents for all users."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            reimport_user_documents(user.id, dry_run)
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Re-import documents from disk with AI processing")
    parser.add_argument("--user", type=int, help="User ID to process (default: all users)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    args = parser.parse_args()

    if args.user:
        reimport_user_documents(args.user, args.dry_run)
    else:
        reimport_all_users(args.dry_run)
