"""Restore demo account data from a pg_dump backup file."""
import psycopg2

BACKUP_FILE = "/tmp/backup_full.sql"
TARGET_IDS = {"27", "28"}


def parse_copy_block(lines, table_name):
    rows = []
    columns = None
    in_block = False
    for line in lines:
        if f"COPY public.{table_name} " in line and "FROM stdin" in line:
            col_str = line.split("(")[1].split(")")[0]
            columns = [c.strip() for c in col_str.split(",")]
            in_block = True
            continue
        if in_block:
            stripped = line.strip()
            if stripped == "\\.":
                break
            rows.append(stripped.split("\t"))
    return columns, rows


def filter_rows(columns, rows, col_name, values):
    idx = columns.index(col_name)
    return [r for r in rows if r[idx] in values]


def nc(vals):
    """Convert \\N to None for psycopg2."""
    return [None if v == "\\N" else v for v in vals]


def insert_rows(cur, table, cols, rows):
    count = 0
    for row in rows:
        vals = nc(row)
        col_names = ",".join(cols)
        placeholders = ",".join(["%s"] * len(vals))
        cur.execute(
            f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
            vals,
        )
        count += 1
    return count


def main():
    with open(BACKUP_FILE) as f:
        lines = f.readlines()

    conn = psycopg2.connect("postgresql://healthy:HealthyDB123@localhost/healthy")
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # 1. Users
        cols, rows = parse_copy_block(lines, "users")
        n = insert_rows(cur, "users", cols, filter_rows(cols, rows, "id", TARGET_IDS))
        print(f"users: {n}")

        # 2. Tables with user_id FK
        for table in [
            "subscriptions", "usage_trackers", "usage_metrics",
            "linked_accounts", "notifications", "notification_preferences",
            "food_preferences", "medications", "health_reports",
            "documents", "openai_usage_logs", "medication_logs",
        ]:
            cols, rows = parse_copy_block(lines, table)
            if not cols:
                continue
            filtered = filter_rows(cols, rows, "user_id", TARGET_IDS)
            n = insert_rows(cur, table, cols, filtered)
            print(f"{table}: {n}")

        # 3. sync_jobs via linked_account_id
        cur.execute("SELECT id FROM linked_accounts WHERE user_id IN (27,28)")
        la_ids = {str(r[0]) for r in cur.fetchall()}
        cols, rows = parse_copy_block(lines, "sync_jobs")
        if cols and la_ids:
            filtered = filter_rows(cols, rows, "linked_account_id", la_ids)
            n = insert_rows(cur, "sync_jobs", cols, filtered)
            print(f"sync_jobs: {n}")

        # 4. test_results via document_id
        cur.execute("SELECT id FROM documents WHERE user_id IN (27,28)")
        doc_ids = {str(r[0]) for r in cur.fetchall()}
        cols, rows = parse_copy_block(lines, "test_results")
        if cols and doc_ids:
            filtered = filter_rows(cols, rows, "document_id", doc_ids)
            n = insert_rows(cur, "test_results", cols, filtered)
            print(f"test_results: {n}")

        # 5. Family groups and members
        cols, rows = parse_copy_block(lines, "family_groups")
        if cols:
            n = insert_rows(cur, "family_groups", cols, filter_rows(cols, rows, "owner_id", TARGET_IDS))
            print(f"family_groups: {n}")

        cur.execute("SELECT id FROM family_groups WHERE owner_id IN (27,28)")
        fg_ids = {str(r[0]) for r in cur.fetchall()}
        cols, rows = parse_copy_block(lines, "family_members")
        if cols and fg_ids:
            n = insert_rows(cur, "family_members", cols, filter_rows(cols, rows, "family_id", fg_ids))
            print(f"family_members: {n}")

        # 6. Audit logs
        cols, rows = parse_copy_block(lines, "audit_logs")
        if cols:
            n = insert_rows(cur, "audit_logs", cols, filter_rows(cols, rows, "user_id", TARGET_IDS))
            print(f"audit_logs: {n}")

        conn.commit()
        print("\nRESTORE COMPLETE!")

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
