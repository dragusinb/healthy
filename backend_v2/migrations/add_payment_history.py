"""
Migration: Add payment_history table.

This migration creates the payment_history table for tracking payments and generating receipts.

Run with:
    python -m backend_v2.migrations.add_payment_history
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the payment history migration."""
    try:
        from backend_v2.database import engine, SessionLocal
    except ImportError:
        from database import engine, SessionLocal

    db = SessionLocal()

    try:
        # Check database type
        is_postgres = 'postgresql' in str(engine.url)

        # Create payment_history table
        logger.info("Creating payment_history table...")
        if is_postgres:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS payment_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    order_id VARCHAR UNIQUE,
                    invoice_number VARCHAR UNIQUE,
                    plan_type VARCHAR,
                    tier VARCHAR,
                    amount FLOAT,
                    currency VARCHAR DEFAULT 'RON',
                    status VARCHAR,
                    paid_at TIMESTAMP,
                    period_start TIMESTAMP,
                    period_end TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
        else:
            # SQLite
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS payment_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id),
                    order_id VARCHAR UNIQUE,
                    invoice_number VARCHAR UNIQUE,
                    plan_type VARCHAR,
                    tier VARCHAR,
                    amount FLOAT,
                    currency VARCHAR DEFAULT 'RON',
                    status VARCHAR,
                    paid_at DATETIME,
                    period_start DATETIME,
                    period_end DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))

        # Create indexes
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_payment_history_user_id
            ON payment_history(user_id)
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_payment_history_order_id
            ON payment_history(order_id)
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_payment_history_invoice_number
            ON payment_history(invoice_number)
        """))

        db.commit()
        logger.info("Migration completed successfully!")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
