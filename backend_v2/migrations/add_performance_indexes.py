"""
Migration: Add performance indexes to improve query speed.

This migration adds indexes on frequently queried columns:
- linked_accounts: user_id, provider_name
- documents: user_id, is_processed
- test_results: document_id
- health_reports: user_id, created_at
- support_tickets: status, reporter_id, ai_status
- notifications: user_id, is_read
- sync_jobs: user_id, status

Run this script once after deploying the code changes.
Safe to run multiple times - existing indexes are skipped.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine

# Index definitions: (table_name, column_name, index_name)
INDEXES = [
    # Original indexes
    ("linked_accounts", "user_id", "ix_linked_accounts_user_id"),
    ("linked_accounts", "provider_name", "ix_linked_accounts_provider_name"),
    ("documents", "user_id", "ix_documents_user_id"),
    ("test_results", "document_id", "ix_test_results_document_id"),
    # Health reports - for report listing and filtering
    ("health_reports", "user_id", "ix_health_reports_user_id"),
    ("health_reports", "created_at", "ix_health_reports_created_at"),
    # Support tickets - for ticket management
    ("support_tickets", "status", "ix_support_tickets_status"),
    ("support_tickets", "reporter_id", "ix_support_tickets_reporter_id"),
    ("support_tickets", "ai_status", "ix_support_tickets_ai_status"),
    # Notifications - for unread counts and user queries
    ("notifications", "user_id", "ix_notifications_user_id"),
    ("notifications", "is_read", "ix_notifications_is_read"),
    # Documents - for processing status
    ("documents", "is_processed", "ix_documents_is_processed"),
    # Sync jobs - for job management
    ("sync_jobs", "user_id", "ix_sync_jobs_user_id"),
    ("sync_jobs", "status", "ix_sync_jobs_status"),
]


def check_index_exists(conn, table_name: str, index_name: str) -> bool:
    """Check if an index exists in PostgreSQL."""
    result = conn.execute(text("""
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = :table_name AND indexname = :index_name
    """), {"table_name": table_name, "index_name": index_name})
    return result.fetchone() is not None


def create_index(conn, table_name: str, column_name: str, index_name: str) -> bool:
    """Create an index if it doesn't exist. Returns True if created."""
    if check_index_exists(conn, table_name, index_name):
        print(f"  Index {index_name} already exists, skipping.")
        return False

    print(f"  Creating index {index_name} on {table_name}.{column_name}...")
    conn.execute(text(f"""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name}
        ON {table_name} ({column_name})
    """))
    conn.commit()
    print(f"  Index {index_name} created successfully.")
    return True


def run_migration():
    """Run the complete migration."""
    print("=" * 60)
    print("Performance Indexes Migration")
    print("=" * 60)

    created_count = 0
    skipped_count = 0

    with engine.connect() as conn:
        for table_name, column_name, index_name in INDEXES:
            print(f"\nProcessing {table_name}.{column_name}:")
            try:
                if create_index(conn, table_name, column_name, index_name):
                    created_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                print(f"  Error creating index: {e}")
                # For CONCURRENTLY, we may need to use regular CREATE INDEX
                # if there's an issue
                try:
                    print(f"  Retrying without CONCURRENTLY...")
                    conn.execute(text(f"""
                        CREATE INDEX IF NOT EXISTS {index_name}
                        ON {table_name} ({column_name})
                    """))
                    conn.commit()
                    print(f"  Index {index_name} created successfully.")
                    created_count += 1
                except Exception as e2:
                    print(f"  Failed: {e2}")

    print("\n" + "=" * 60)
    print(f"Migration completed: {created_count} indexes created, {skipped_count} already existed")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
