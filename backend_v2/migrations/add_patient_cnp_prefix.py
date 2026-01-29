"""
Migration: Add patient_cnp_prefix and file_hash columns to documents table.

- patient_cnp_prefix: First 7 digits of CNP for unique patient identification
- file_hash: MD5 hash of file content for duplicate detection

Run this script once after deploying the code changes.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from database import engine, Base
import models  # Import models to register them with Base


def add_patient_cnp_prefix_column():
    """Add patient_cnp_prefix column if it doesn't exist."""
    inspector = inspect(engine)

    # Check if documents table exists
    if 'documents' not in inspector.get_table_names():
        print("Documents table doesn't exist. Creating all tables...")
        Base.metadata.create_all(bind=engine)
        print("All tables created (including new columns).")
        return

    # Table exists - check if columns exist
    columns = [col['name'] for col in inspector.get_columns('documents')]

    if 'patient_cnp_prefix' not in columns:
        print("Adding patient_cnp_prefix column to documents table...")
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE documents
                ADD COLUMN patient_cnp_prefix VARCHAR(7)
            """))
            conn.commit()
        print("Column added successfully.")
    else:
        print("Column patient_cnp_prefix already exists.")


def add_file_hash_column():
    """Add file_hash column if it doesn't exist."""
    inspector = inspect(engine)

    if 'documents' not in inspector.get_table_names():
        return  # Table will be created with all columns

    columns = [col['name'] for col in inspector.get_columns('documents')]

    if 'file_hash' not in columns:
        print("Adding file_hash column to documents table...")
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE documents
                ADD COLUMN file_hash VARCHAR(32)
            """))
            conn.commit()
        print("Column added successfully.")

        # Create index for fast duplicate lookups
        print("Creating index on file_hash...")
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_documents_file_hash
                ON documents (file_hash)
            """))
            conn.commit()
        print("Index created.")
    else:
        print("Column file_hash already exists.")


def run_migration():
    """Run the complete migration."""
    print("=" * 50)
    print("Document Columns Migration")
    print("=" * 50)

    print("\nStep 1: Adding patient_cnp_prefix column...")
    add_patient_cnp_prefix_column()

    print("\nStep 2: Adding file_hash column...")
    add_file_hash_column()

    print("\n" + "=" * 50)
    print("Migration completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    run_migration()
