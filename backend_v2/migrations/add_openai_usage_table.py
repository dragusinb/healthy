"""Add OpenAI usage tracking table.

Run with: python -m migrations.add_openai_usage_table
"""
from sqlalchemy import text

try:
    from backend_v2.database import engine
except ImportError:
    from database import engine


def run_migration():
    """Create the openai_usage_logs table."""
    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'openai_usage_logs'
            )
        """))
        if result.scalar():
            print("Table openai_usage_logs already exists")
            return

        # Create table
        conn.execute(text("""
            CREATE TABLE openai_usage_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date VARCHAR(10),
                model VARCHAR(50),
                purpose VARCHAR(100),
                tokens_input INTEGER DEFAULT 0,
                tokens_output INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                cost_usd FLOAT DEFAULT 0.0,
                user_id INTEGER REFERENCES users(id),
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT
            )
        """))

        # Create indexes
        conn.execute(text("""
            CREATE INDEX ix_openai_usage_logs_timestamp ON openai_usage_logs(timestamp)
        """))
        conn.execute(text("""
            CREATE INDEX ix_openai_usage_logs_date ON openai_usage_logs(date)
        """))
        conn.execute(text("""
            CREATE INDEX ix_openai_usage_date_purpose ON openai_usage_logs(date, purpose)
        """))

        conn.commit()
        print("Created openai_usage_logs table with indexes")


if __name__ == "__main__":
    run_migration()
