"""
Migration: Add converted column and unique constraint to lead_captures table.

Run with:
    python -m backend_v2.migrations.add_lead_capture_fields
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Add converted column and unique constraint to lead_captures."""
    try:
        from backend_v2.database import engine, SessionLocal
    except ImportError:
        from database import engine, SessionLocal

    db = SessionLocal()

    try:
        is_postgres = 'postgresql' in str(engine.url)

        if is_postgres:
            # Add converted column
            db.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name='lead_captures' AND column_name='converted') THEN
                        ALTER TABLE lead_captures ADD COLUMN converted BOOLEAN DEFAULT FALSE;
                    END IF;
                END $$;
            """))
            logger.info("Added 'converted' column (if not exists)")

            # Add unique constraint on (email, source)
            db.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_lead_email_source') THEN
                        ALTER TABLE lead_captures ADD CONSTRAINT uq_lead_email_source UNIQUE (email, source);
                    END IF;
                END $$;
            """))
            logger.info("Added unique constraint on (email, source) (if not exists)")
        else:
            # SQLite fallback
            try:
                db.execute(text("ALTER TABLE lead_captures ADD COLUMN converted BOOLEAN DEFAULT FALSE"))
                logger.info("Added 'converted' column")
            except Exception:
                logger.info("'converted' column already exists")

            try:
                db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_lead_email_source ON lead_captures (email, source)"))
                logger.info("Added unique index on (email, source)")
            except Exception:
                logger.info("Unique index already exists")

        db.commit()
        logger.info("Migration complete.")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
