"""
Database migration to add vault-encrypted columns.

Run this script to add encrypted columns to existing tables.
After running this migration, you can initialize the vault and
run the data migration to encrypt existing data.

Usage:
    python -m backend_v2.migrations.add_encrypted_columns
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text, inspect
from database import engine, SessionLocal


def column_exists(inspector, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def table_exists(inspector, table_name: str) -> bool:
    """Check if a table exists."""
    return table_name in inspector.get_table_names()


def run_migration():
    """Add encrypted columns to all tables."""

    inspector = inspect(engine)

    with engine.connect() as conn:
        # Create vault_config table if not exists
        if not table_exists(inspector, 'vault_config'):
            print("Creating vault_config table...")
            conn.execute(text("""
                CREATE TABLE vault_config (
                    id INTEGER PRIMARY KEY,
                    salt VARCHAR NOT NULL,
                    master_key_hash VARCHAR NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("  Created vault_config table")

        # Add encrypted columns to linked_accounts
        print("\nUpdating linked_accounts table...")
        if not column_exists(inspector, 'linked_accounts', 'username_enc'):
            conn.execute(text("ALTER TABLE linked_accounts ADD COLUMN username_enc BYTEA"))
            print("  Added username_enc column")
        if not column_exists(inspector, 'linked_accounts', 'password_enc'):
            conn.execute(text("ALTER TABLE linked_accounts ADD COLUMN password_enc BYTEA"))
            print("  Added password_enc column")

        # Add encrypted columns to test_results (biomarkers)
        print("\nUpdating test_results table...")
        if not column_exists(inspector, 'test_results', 'value_enc'):
            conn.execute(text("ALTER TABLE test_results ADD COLUMN value_enc BYTEA"))
            print("  Added value_enc column")
        if not column_exists(inspector, 'test_results', 'numeric_value_enc'):
            conn.execute(text("ALTER TABLE test_results ADD COLUMN numeric_value_enc BYTEA"))
            print("  Added numeric_value_enc column")

        # Add encrypted columns to health_reports
        print("\nUpdating health_reports table...")
        if not column_exists(inspector, 'health_reports', 'content_enc'):
            conn.execute(text("ALTER TABLE health_reports ADD COLUMN content_enc BYTEA"))
            print("  Added content_enc column")

        # Add encrypted columns to users (profile data)
        print("\nUpdating users table...")
        encrypted_user_columns = [
            'full_name_enc', 'date_of_birth_enc', 'gender_enc',
            'blood_type_enc', 'profile_data_enc', 'health_context_enc'
        ]
        for col in encrypted_user_columns:
            if not column_exists(inspector, 'users', col):
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} BYTEA"))
                print(f"  Added {col} column")

        # Add encrypted columns to documents
        print("\nUpdating documents table...")
        if not column_exists(inspector, 'documents', 'encrypted_path'):
            conn.execute(text("ALTER TABLE documents ADD COLUMN encrypted_path VARCHAR"))
            print("  Added encrypted_path column")
        if not column_exists(inspector, 'documents', 'is_encrypted'):
            conn.execute(text("ALTER TABLE documents ADD COLUMN is_encrypted BOOLEAN DEFAULT FALSE"))
            print("  Added is_encrypted column")
        if not column_exists(inspector, 'documents', 'patient_name_enc'):
            conn.execute(text("ALTER TABLE documents ADD COLUMN patient_name_enc BYTEA"))
            print("  Added patient_name_enc column")
        if not column_exists(inspector, 'documents', 'patient_cnp_enc'):
            conn.execute(text("ALTER TABLE documents ADD COLUMN patient_cnp_enc BYTEA"))
            print("  Added patient_cnp_enc column")

        conn.commit()
        print("\n✓ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Initialize the vault: POST /admin/vault/initialize")
        print("2. Run data migration: python -m backend_v2.migrations.migrate_to_encrypted")


if __name__ == "__main__":
    print("=" * 50)
    print("Vault Encryption - Database Migration")
    print("=" * 50)
    print()

    run_migration()
