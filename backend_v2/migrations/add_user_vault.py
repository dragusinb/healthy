"""
Migration: Add per-user encryption vault fields to users table.

Run with: python migrations/add_user_vault.py
"""
import sys
import os

# Set up paths
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_dir = os.path.dirname(backend_dir)
sys.path.insert(0, project_dir)

# Load .env file from backend_v2 directory
env_file = os.path.join(backend_dir, '.env')
if os.path.exists(env_file):
    print(f"Loading environment from {env_file}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from sqlalchemy import inspect, text
from backend_v2.database import engine, DATABASE_URL

def run_migration():
    print(f"Connecting to database: {DATABASE_URL[:50]}..." if DATABASE_URL else "No DATABASE_URL found!")
    """Add per-user vault fields to users table."""
    inspector = inspect(engine)

    # Get existing columns in users table
    existing_columns = [col['name'] for col in inspector.get_columns('users')]
    print(f"Existing columns in users table: {existing_columns}")

    with engine.connect() as conn:
        # Add vault_data column
        if 'vault_data' not in existing_columns:
            print("Adding vault_data column...")
            conn.execute(text("ALTER TABLE users ADD COLUMN vault_data TEXT"))
            print("vault_data column added.")
        else:
            print("vault_data column already exists.")

        # Add vault_setup_at column
        if 'vault_setup_at' not in existing_columns:
            print("Adding vault_setup_at column...")
            conn.execute(text("ALTER TABLE users ADD COLUMN vault_setup_at TIMESTAMP"))
            print("vault_setup_at column added.")
        else:
            print("vault_setup_at column already exists.")

        conn.commit()

    print("Migration complete!")

if __name__ == "__main__":
    run_migration()
