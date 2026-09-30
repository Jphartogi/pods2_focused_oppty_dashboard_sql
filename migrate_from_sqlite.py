"""
One-time data migration: copy an existing v1 db.sqlite3 into the v2.0
Postgres database.

Run this ONCE, right after `docker compose up -d` has created the schema
(and auto-seeded placeholder admin/AM users + example deals via init_db()),
and BEFORE pointing real users at the app. If the target tables already
have data - which they will, from that placeholder seed - this prompts for
confirmation and then erases it before migrating; pass --yes to skip the
prompt for a scripted/non-interactive run.

Usage (from the host, with the sqlite file path and the Postgres DSN):

    python3 migrate_from_sqlite.py /path/to/db.sqlite3 \
        postgresql://pods2:pods2@localhost:5432/pods2 [--yes]

Or, run inside the running `app` container against a copy of the old file:

    docker compose cp /path/to/db.sqlite3 app:/tmp/old.sqlite3
    docker compose exec app python3 migrate_from_sqlite.py /tmp/old.sqlite3 "$DATABASE_URL"

Always test this against a COPY of the real db.sqlite3 first - never the
live file - the same practice used throughout this project's development.
"""
import sqlite3
import sys

import psycopg
from psycopg.rows import dict_row

# Order matters: deals before deal_tasks/deal_sync_map/account_coverage's
# FK-free but logically-dependent tables, users before login_logs.
TABLES = [
    "users",
    "deals",
    "deal_tasks",
    "login_logs",
    "performance",
    "account_coverage",
    "config",
    "deal_sync_map",
]

BOOL_COLUMNS = {
    "deals": {"is_blocked"},
    "account_coverage": {"is_manual", "is_champion"},
}


def migrate(sqlite_path, pg_dsn, assume_yes=False):
    sconn = sqlite3.connect(sqlite_path)
    sconn.row_factory = sqlite3.Row

    with psycopg.connect(pg_dsn, row_factory=dict_row) as pconn:
        with pconn.cursor() as pcur:
            counts = {
                t: pcur.execute(f"SELECT COUNT(*) AS c FROM {t}").fetchone()["c"]
                for t in TABLES
            }
        nonempty = {t: c for t, c in counts.items() if c > 0}
        if nonempty:
            # `docker compose up` on a brand-new database seeds placeholder
            # admin/AM users and example deals via init_db() - that's exactly
            # what this migration is meant to replace, so we clear it rather
            # than refuse. This is NOT meant to run against a database that
            # already holds real production data.
            print("The target Postgres database already has data in:")
            for t, c in nonempty.items():
                print(f"  {t}: {c} row(s)")
            print("\nThis is expected right after a fresh `docker compose up` (it seeds "
                  "placeholder admin/AM users and example deals). Continuing will ERASE "
                  "all of the above and replace it with the migrated SQLite data.")
            if not assume_yes:
                answer = input("Type 'yes' to erase and continue: ").strip().lower()
                if answer != "yes":
                    print("Aborted - nothing was changed.")
                    sys.exit(1)
            with pconn.cursor() as pcur:
                # Reverse dependency order so FK constraints don't block the truncate.
                for table in reversed(TABLES):
                    pcur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
            pconn.commit()

        print("Migrating...")
        summary = {}
        with pconn.cursor() as pcur:
            for table in TABLES:
                src_rows = sconn.execute(f"SELECT * FROM {table}").fetchall()
                if not src_rows:
                    summary[table] = 0
                    continue

                cols = src_rows[0].keys()
                bool_cols = BOOL_COLUMNS.get(table, set())
                placeholders = ", ".join(["%s"] * len(cols))
                col_list = ", ".join(cols)
                sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"

                for r in src_rows:
                    values = []
                    for c in cols:
                        v = r[c]
                        if c in bool_cols:
                            v = bool(v)
                        values.append(v)
                    pcur.execute(sql, values)
                summary[table] = len(src_rows)

                # Reset the identity sequence so future INSERTs (which don't
                # specify an id) start after the highest migrated id.
                if "id" in cols:
                    pcur.execute(
                        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                        f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
                    )
        pconn.commit()

    print("\nMigration complete. Rows copied per table:")
    for table, n in summary.items():
        print(f"  {table:20s} {n}")
    print("\nSpot-check a few tables in the app before pointing real users at it.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--yes"]
    if len(args) != 2:
        print(__doc__)
        sys.exit(1)
    migrate(args[0], args[1], assume_yes="--yes" in sys.argv)
