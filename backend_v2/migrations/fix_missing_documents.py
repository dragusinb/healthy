"""
Migration: Fix missing documents by scanning raw files and importing those not in DB.
Uses file_hash (MD5) for accurate duplicate detection.

Run with: python migrations/fix_missing_documents.py
"""
import sys
import os
import hashlib
import datetime

# Set up paths
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_dir = os.path.dirname(backend_dir)
sys.path.insert(0, project_dir)

# Load .env file
env_file = os.path.join(backend_dir, '.env')
if os.path.exists(env_file):
    print(f"Loading environment from {env_file}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value


def calculate_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"  Error hashing {file_path}: {e}")
        return None


def run_migration():
    from sqlalchemy import text
    from backend_v2.database import engine, SessionLocal
    from backend_v2.models import Document, TestResult
    from backend_v2.services.ai_service import AIService
    from backend_v2.services.biomarker_normalizer import get_canonical_name

    print("Starting missing documents fix...")

    db = SessionLocal()

    try:
        # Step 1: Update existing documents with file_hash if missing
        print("\n=== Step 1: Updating existing documents with file_hash ===")
        docs_without_hash = db.query(Document).filter(Document.file_hash == None).all()
        print(f"Found {len(docs_without_hash)} documents without file_hash")

        for doc in docs_without_hash:
            if doc.file_path and os.path.exists(doc.file_path):
                file_hash = calculate_file_hash(doc.file_path)
                if file_hash:
                    doc.file_hash = file_hash
                    print(f"  Updated {doc.filename}: {file_hash[:16]}...")

        db.commit()
        print("File hashes updated.")

        # Step 2: Get all existing hashes for each user
        print("\n=== Step 2: Building hash index ===")
        existing_hashes = {}
        all_docs = db.query(Document).all()
        for doc in all_docs:
            if doc.file_hash:
                key = (doc.user_id, doc.file_hash)
                existing_hashes[key] = doc.id

        print(f"Indexed {len(existing_hashes)} existing document hashes")

        # Step 3: Scan raw directories for missing documents
        print("\n=== Step 3: Scanning for missing documents ===")
        data_dir = os.path.join(project_dir, "data", "raw")

        if not os.path.exists(data_dir):
            print(f"Data directory not found: {data_dir}")
            return

        # Initialize AI service for parsing
        try:
            ai_service = AIService()
        except Exception as e:
            print(f"Warning: AI Service init failed: {e}")
            ai_service = None

        total_imported = 0
        total_biomarkers = 0

        # Iterate through user directories
        for user_dir in os.listdir(data_dir):
            user_path = os.path.join(data_dir, user_dir)
            if not os.path.isdir(user_path):
                continue

            try:
                user_id = int(user_dir)
            except ValueError:
                continue

            print(f"\nProcessing user {user_id}...")

            # Process each provider directory
            for provider_dir in os.listdir(user_path):
                provider_path = os.path.join(user_path, provider_dir)
                if not os.path.isdir(provider_path):
                    continue

                # Map directory name to provider
                provider_name = {
                    "regina_maria": "Regina Maria",
                    "synevo": "Synevo"
                }.get(provider_dir.lower(), provider_dir)

                print(f"  Provider: {provider_name}")

                # Get all PDFs in this directory
                pdf_files = [f for f in os.listdir(provider_path) if f.lower().endswith('.pdf')]
                print(f"    Found {len(pdf_files)} PDF files")

                # Check each file
                missing_files = []
                for pdf_file in pdf_files:
                    file_path = os.path.join(provider_path, pdf_file)
                    file_hash = calculate_file_hash(file_path)

                    if not file_hash:
                        continue

                    key = (user_id, file_hash)
                    if key not in existing_hashes:
                        missing_files.append((pdf_file, file_path, file_hash))

                print(f"    Missing from DB: {len(missing_files)} files")

                # Import missing files
                for filename, file_path, file_hash in missing_files:
                    print(f"    Importing: {filename}")

                    # Create document
                    new_doc = Document(
                        user_id=user_id,
                        filename=filename,
                        file_path=file_path,
                        file_hash=file_hash,
                        provider=provider_name,
                        upload_date=datetime.datetime.now(),
                        is_processed=False
                    )
                    db.add(new_doc)
                    db.commit()
                    db.refresh(new_doc)

                    # Add to existing hashes to avoid re-importing
                    existing_hashes[(user_id, file_hash)] = new_doc.id

                    # AI Parse if available
                    if ai_service:
                        try:
                            parsed_data = ai_service.process_document(file_path)

                            if "results" in parsed_data and parsed_data["results"]:
                                biomarker_count = 0
                                for r in parsed_data["results"]:
                                    numeric_val = r.get("numeric_value")
                                    if numeric_val is None:
                                        try:
                                            numeric_val = float(r.get("value"))
                                        except (TypeError, ValueError):
                                            numeric_val = None

                                    test_name = r.get("test_name")
                                    tr = TestResult(
                                        document_id=new_doc.id,
                                        test_name=test_name,
                                        canonical_name=get_canonical_name(test_name) if test_name else None,
                                        value=str(r.get("value")),
                                        numeric_value=numeric_val,
                                        unit=r.get("unit"),
                                        reference_range=r.get("reference_range"),
                                        flags=r.get("flags", "NORMAL")
                                    )
                                    db.add(tr)
                                    biomarker_count += 1

                                # Update document date
                                if "metadata" in parsed_data and parsed_data["metadata"].get("date"):
                                    try:
                                        new_doc.document_date = datetime.datetime.strptime(
                                            parsed_data["metadata"]["date"], "%Y-%m-%d"
                                        )
                                    except:
                                        pass

                                # Update patient info
                                if "patient_info" in parsed_data:
                                    pi = parsed_data["patient_info"]
                                    if pi.get("full_name"):
                                        new_doc.patient_name = pi["full_name"]
                                    if pi.get("cnp_prefix") and len(pi["cnp_prefix"]) >= 7:
                                        new_doc.patient_cnp_prefix = pi["cnp_prefix"][:7]

                                new_doc.is_processed = True
                                db.commit()
                                total_biomarkers += biomarker_count
                                print(f"      Extracted {biomarker_count} biomarkers")
                            else:
                                new_doc.is_processed = True
                                db.commit()
                                print(f"      No biomarkers found")

                        except Exception as e:
                            print(f"      AI parsing error: {e}")
                            new_doc.is_processed = True
                            db.commit()
                    else:
                        new_doc.is_processed = True
                        db.commit()

                    total_imported += 1

        print(f"\n=== Summary ===")
        print(f"Documents imported: {total_imported}")
        print(f"Biomarkers extracted: {total_biomarkers}")

        # Final count
        final_count = db.query(Document).count()
        print(f"Total documents in DB: {final_count}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
