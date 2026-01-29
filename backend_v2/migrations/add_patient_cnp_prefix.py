"""
Migration: Add patient_cnp_prefix column to documents table.

This column stores the first 7 digits of the patient's CNP (Cod Numeric Personal)
for unique patient identification across documents with different name formats.

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
        print("All tables created (including patient_cnp_prefix column).")
        return

    # Table exists - check if column exists
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


def run_migration():
    """Run the complete migration."""
    print("=" * 50)
    print("Add Patient CNP Prefix Migration")
    print("=" * 50)

    print("\nAdding column...")
    add_patient_cnp_prefix_column()

    print("\n" + "=" * 50)
    print("Migration completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    run_migration()
