"""
Migration: Add email verification and password reset fields to users table.

Run with: python -m backend_v2.migrations.add_email_verification
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import inspect, text
from backend_v2.database import engine, SessionLocal

def run_migration():
    """Add email verification columns to users table."""
    inspector = inspect(engine)

    # Check which columns already exist
    columns = [col['name'] for col in inspector.get_columns('users')]

    columns_to_add = []

    if 'email_verified' not in columns:
        columns_to_add.append("ADD COLUMN email_verified BOOLEAN DEFAULT FALSE")

    if 'verification_token' not in columns:
        columns_to_add.append("ADD COLUMN verification_token VARCHAR(255)")

    if 'verification_token_expires' not in columns:
        columns_to_add.append("ADD COLUMN verification_token_expires TIMESTAMP")

    if 'reset_token' not in columns:
        columns_to_add.append("ADD COLUMN reset_token VARCHAR(255)")

    if 'reset_token_expires' not in columns:
        columns_to_add.append("ADD COLUMN reset_token_expires TIMESTAMP")

    if not columns_to_add:
        print("All columns already exist. Nothing to do.")
        return

    with engine.connect() as conn:
        for col_sql in columns_to_add:
            sql = f"ALTER TABLE users {col_sql}"
            print(f"Running: {sql}")
            conn.execute(text(sql))
        conn.commit()

    # Mark existing users as verified (they registered before verification was required)
    db = SessionLocal()
    try:
        result = db.execute(text("UPDATE users SET email_verified = TRUE WHERE email_verified IS NULL OR email_verified = FALSE"))
        db.commit()
        print(f"Marked {result.rowcount} existing users as verified.")
    finally:
        db.close()

    print("Migration complete!")

if __name__ == "__main__":
    run_migration()
