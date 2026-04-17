"""
Migration: Add trial fields to subscriptions table.

Run with:
    python -m backend_v2.migrations.add_trial_fields
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Add is_trial and trial_end_date columns to subscriptions."""
    try:
        from backend_v2.database import engine, SessionLocal
    except ImportError:
        from database import engine, SessionLocal

    db = SessionLocal()

    try:
        is_postgres = 'postgresql' in str(engine.url)

        if is_postgres:
            db.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name='subscriptions' AND column_name='is_trial') THEN
                        ALTER TABLE subscriptions ADD COLUMN is_trial BOOLEAN DEFAULT FALSE;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name='subscriptions' AND column_name='trial_end_date') THEN
                        ALTER TABLE subscriptions ADD COLUMN trial_end_date TIMESTAMP;
                    END IF;
                END $$;
            """))
        else:
            try:
                db.execute(text("ALTER TABLE subscriptions ADD COLUMN is_trial BOOLEAN DEFAULT 0"))
            except Exception:
                logger.info("is_trial column already exists")
            try:
                db.execute(text("ALTER TABLE subscriptions ADD COLUMN trial_end_date DATETIME"))
            except Exception:
                logger.info("trial_end_date column already exists")

        db.commit()
        logger.info("Migration complete: trial fields added to subscriptions")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
