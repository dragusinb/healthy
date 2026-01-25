"""
Migration: Add canonical_name column to test_results table and populate it.

This migration:
1. Adds a new 'canonical_name' column to the test_results table
2. Populates canonical_name for all existing records using the biomarker normalizer
3. Creates an index on canonical_name for efficient queries

Run this script once after deploying the code changes.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import SessionLocal, engine
from services.biomarker_normalizer import get_canonical_name


def add_canonical_name_column():
    """Add canonical_name column if it doesn't exist."""
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'test_results' AND column_name = 'canonical_name'
        """))

        if result.fetchone() is None:
            print("Adding canonical_name column to test_results table...")
            conn.execute(text("""
                ALTER TABLE test_results
                ADD COLUMN canonical_name VARCHAR
            """))
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column canonical_name already exists.")


def create_index():
    """Create index on canonical_name if it doesn't exist."""
    with engine.connect() as conn:
        # Check if index exists
        result = conn.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'test_results' AND indexname = 'ix_test_results_canonical_name'
        """))

        if result.fetchone() is None:
            print("Creating index on canonical_name...")
            conn.execute(text("""
                CREATE INDEX ix_test_results_canonical_name
                ON test_results (canonical_name)
            """))
            conn.commit()
            print("Index created successfully.")
        else:
            print("Index already exists.")


def populate_canonical_names():
    """Populate canonical_name for all existing records."""
    db = SessionLocal()

    try:
        # Get all test results without canonical_name
        result = db.execute(text("""
            SELECT id, test_name FROM test_results
            WHERE canonical_name IS NULL AND test_name IS NOT NULL
        """))

        records = result.fetchall()
        total = len(records)

        if total == 0:
            print("No records need updating.")
            return

        print(f"Updating {total} records...")

        # Update in batches for better performance
        batch_size = 100
        updated = 0

        for i in range(0, total, batch_size):
            batch = records[i:i + batch_size]

            for row in batch:
                record_id, test_name = row
                canonical = get_canonical_name(test_name)

                db.execute(text("""
                    UPDATE test_results
                    SET canonical_name = :canonical
                    WHERE id = :id
                """), {"canonical": canonical, "id": record_id})

            db.commit()
            updated += len(batch)
            print(f"  Updated {updated}/{total} records...")

        print(f"Successfully updated {updated} records.")

    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def run_migration():
    """Run the complete migration."""
    print("=" * 50)
    print("Biomarker Canonical Name Migration")
    print("=" * 50)

    print("\nStep 1: Adding column...")
    add_canonical_name_column()

    print("\nStep 2: Creating index...")
    create_index()

    print("\nStep 3: Populating canonical names...")
    populate_canonical_names()

    print("\n" + "=" * 50)
    print("Migration completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    run_migration()
