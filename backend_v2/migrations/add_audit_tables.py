"""
Migration: Add audit logging, usage tracking, and abuse detection tables.

Run with: python migrations/add_audit_tables.py
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
from backend_v2.database import engine, SessionLocal, DATABASE_URL

def run_migration():
    print(f"Connecting to database: {DATABASE_URL[:50]}..." if DATABASE_URL else "No DATABASE_URL found!")
    """Create audit and tracking tables."""
    inspector = inspect(engine)

    existing_tables = inspector.get_table_names()
    print(f"Existing tables: {existing_tables}")

    with engine.connect() as conn:
        # Create audit_logs table
        if 'audit_logs' not in existing_tables:
            print("Creating audit_logs table...")
            conn.execute(text("""
                CREATE TABLE audit_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    action VARCHAR(100) NOT NULL,
                    resource_type VARCHAR(100),
                    resource_id INTEGER,
                    details TEXT,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    status VARCHAR(20) DEFAULT 'success',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX ix_audit_logs_user_id ON audit_logs(user_id)"))
            conn.execute(text("CREATE INDEX ix_audit_logs_action ON audit_logs(action)"))
            conn.execute(text("CREATE INDEX ix_audit_logs_created_at ON audit_logs(created_at)"))
            print("audit_logs table created.")
        else:
            print("audit_logs table already exists.")

        # Create user_sessions table
        if 'user_sessions' not in existing_tables:
            print("Creating user_sessions table...")
            conn.execute(text("""
                CREATE TABLE user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    session_token VARCHAR(64) NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    device_fingerprint VARCHAR(255),
                    location VARCHAR(255),
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """))
            conn.execute(text("CREATE INDEX ix_user_sessions_user_id ON user_sessions(user_id)"))
            conn.execute(text("CREATE INDEX ix_user_sessions_token ON user_sessions(session_token)"))
            print("user_sessions table created.")
        else:
            print("user_sessions table already exists.")

        # Create abuse_flags table
        if 'abuse_flags' not in existing_tables:
            print("Creating abuse_flags table...")
            conn.execute(text("""
                CREATE TABLE abuse_flags (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    ip_address VARCHAR(45),
                    flag_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) DEFAULT 'low',
                    description TEXT,
                    details TEXT,
                    is_resolved BOOLEAN DEFAULT FALSE,
                    resolved_by INTEGER REFERENCES users(id),
                    resolved_at TIMESTAMP,
                    resolution_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX ix_abuse_flags_user_id ON abuse_flags(user_id)"))
            conn.execute(text("CREATE INDEX ix_abuse_flags_flag_type ON abuse_flags(flag_type)"))
            conn.execute(text("CREATE INDEX ix_abuse_flags_created_at ON abuse_flags(created_at)"))
            print("abuse_flags table created.")
        else:
            print("abuse_flags table already exists.")

        # Create rate_limit_counters table
        if 'rate_limit_counters' not in existing_tables:
            print("Creating rate_limit_counters table...")
            conn.execute(text("""
                CREATE TABLE rate_limit_counters (
                    id SERIAL PRIMARY KEY,
                    identifier VARCHAR(255) NOT NULL,
                    action VARCHAR(100) NOT NULL,
                    count INTEGER DEFAULT 0,
                    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    window_minutes INTEGER DEFAULT 60
                )
            """))
            conn.execute(text("CREATE INDEX ix_rate_limit_identifier ON rate_limit_counters(identifier)"))
            conn.execute(text("CREATE INDEX ix_rate_limit_action ON rate_limit_counters(action)"))
            conn.execute(text("CREATE INDEX ix_rate_limit_identifier_action ON rate_limit_counters(identifier, action)"))
            print("rate_limit_counters table created.")
        else:
            print("rate_limit_counters table already exists.")

        # Create usage_metrics table
        if 'usage_metrics' not in existing_tables:
            print("Creating usage_metrics table...")
            conn.execute(text("""
                CREATE TABLE usage_metrics (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    date TIMESTAMP NOT NULL,
                    api_calls INTEGER DEFAULT 0,
                    documents_uploaded INTEGER DEFAULT 0,
                    documents_viewed INTEGER DEFAULT 0,
                    documents_deleted INTEGER DEFAULT 0,
                    ai_analyses_run INTEGER DEFAULT 0,
                    biomarkers_viewed INTEGER DEFAULT 0,
                    reports_generated INTEGER DEFAULT 0,
                    reports_exported INTEGER DEFAULT 0,
                    sessions_count INTEGER DEFAULT 0,
                    total_session_minutes INTEGER DEFAULT 0,
                    syncs_triggered INTEGER DEFAULT 0,
                    syncs_completed INTEGER DEFAULT 0,
                    syncs_failed INTEGER DEFAULT 0
                )
            """))
            conn.execute(text("CREATE INDEX ix_usage_metrics_user_id ON usage_metrics(user_id)"))
            conn.execute(text("CREATE INDEX ix_usage_metrics_date ON usage_metrics(date)"))
            conn.execute(text("CREATE INDEX ix_usage_metrics_user_date ON usage_metrics(user_id, date)"))
            print("usage_metrics table created.")
        else:
            print("usage_metrics table already exists.")

        conn.commit()

    print("Migration complete!")

if __name__ == "__main__":
    run_migration()
