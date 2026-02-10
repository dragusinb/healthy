"""
Migration: Add push notification tables and columns.

This migration:
1. Creates the push_subscriptions table
2. Adds push notification preference columns to notification_preferences

Run with:
    python -m backend_v2.migrations.add_push_notifications
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, text
from sqlalchemy.orm import Session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the push notifications migration."""
    try:
        from backend_v2.database import engine, SessionLocal
    except ImportError:
        from database import engine, SessionLocal

    db = SessionLocal()

    try:
        # Check database type
        is_postgres = 'postgresql' in str(engine.url)

        # 1. Create push_subscriptions table if it doesn't exist
        logger.info("Creating push_subscriptions table...")
        if is_postgres:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS push_subscriptions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    endpoint VARCHAR UNIQUE NOT NULL,
                    p256dh_key VARCHAR NOT NULL,
                    auth_key VARCHAR NOT NULL,
                    user_agent VARCHAR,
                    device_name VARCHAR,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_used TIMESTAMP,
                    failure_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_push_subscriptions_user_id
                ON push_subscriptions(user_id)
            """))
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_push_subscriptions_endpoint
                ON push_subscriptions(endpoint)
            """))
        else:
            # SQLite
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS push_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id),
                    endpoint VARCHAR UNIQUE NOT NULL,
                    p256dh_key VARCHAR NOT NULL,
                    auth_key VARCHAR NOT NULL,
                    user_agent VARCHAR,
                    device_name VARCHAR,
                    is_active BOOLEAN DEFAULT 1,
                    last_used DATETIME,
                    failure_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_push_subscriptions_user_id
                ON push_subscriptions(user_id)
            """))
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_push_subscriptions_endpoint
                ON push_subscriptions(endpoint)
            """))

        # 2. Add push notification columns to notification_preferences table
        logger.info("Adding push notification columns to notification_preferences...")

        push_columns = [
            ("push_enabled", "BOOLEAN", "TRUE" if is_postgres else "1"),
            ("push_new_documents", "BOOLEAN", "TRUE" if is_postgres else "1"),
            ("push_abnormal_biomarkers", "BOOLEAN", "TRUE" if is_postgres else "1"),
            ("push_analysis_complete", "BOOLEAN", "TRUE" if is_postgres else "1"),
            ("push_sync_failed", "BOOLEAN", "TRUE" if is_postgres else "1"),
        ]

        for col_name, col_type, default in push_columns:
            try:
                if is_postgres:
                    db.execute(text(f"""
                        ALTER TABLE notification_preferences
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type} DEFAULT {default}
                    """))
                else:
                    # SQLite - check if column exists first
                    result = db.execute(text(
                        "PRAGMA table_info(notification_preferences)"
                    ))
                    columns = [row[1] for row in result]
                    if col_name not in columns:
                        db.execute(text(f"""
                            ALTER TABLE notification_preferences
                            ADD COLUMN {col_name} {col_type} DEFAULT {default}
                        """))
                        logger.info(f"Added column {col_name}")
                    else:
                        logger.info(f"Column {col_name} already exists")
            except Exception as e:
                logger.warning(f"Could not add column {col_name}: {e}")

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
