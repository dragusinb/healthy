"""
Migration: Add performance indexes to improve query speed.

This migration adds indexes on:
1. linked_accounts.user_id - for user account lookups
2. linked_accounts.provider_name - for provider filtering
3. documents.user_id - for user document queries
4. test_results.document_id - for document join queries

Run this script once after deploying the code changes.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine

# Index definitions: (table_name, column_name, index_name)
INDEXES = [
    ("linked_accounts", "user_id", "ix_linked_accounts_user_id"),
    ("linked_accounts", "provider_name", "ix_linked_accounts_provider_name"),
    ("documents", "user_id", "ix_documents_user_id"),
    ("test_results", "document_id", "ix_test_results_document_id"),
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
