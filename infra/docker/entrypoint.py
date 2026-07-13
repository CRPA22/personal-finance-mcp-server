#!/usr/bin/env python3
"""Docker entrypoint: ensure DB schema is ready, then start MCP server."""
import os
import subprocess
import sys
import time


def tables_exist(db_url: str) -> bool:
    """Check if the main tables already exist (Supabase case)."""
    try:
        import psycopg2
        conn = psycopg2.connect(db_url, connect_timeout=10)
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='transactions'"
        )
        count = cur.fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False


def stamp_alembic_version(db_url: str, revision: str) -> None:
    """Create alembic_version table and stamp with the given revision if not present."""
    try:
        import psycopg2
        conn = psycopg2.connect(db_url, connect_timeout=10)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS alembic_version "
            "(version_num VARCHAR(32) NOT NULL, PRIMARY KEY (version_num))"
        )
        cur.execute("SELECT COUNT(*) FROM alembic_version")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO alembic_version VALUES (%s)", (revision,))
            print(f"Alembic version stamped: {revision}")
        else:
            print("Alembic version already set.")
        conn.close()
    except Exception as e:
        print(f"Warning: could not stamp alembic version: {e}", file=sys.stderr)


def main():
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/finance_mcp")

    print("Checking database connection...")
    for attempt in range(30):
        if tables_exist(db_url):
            print("Database reachable and tables exist.")
            stamp_alembic_version(db_url, "010")
            break
        print(f"Waiting for database... (attempt {attempt + 1}/30)")
        time.sleep(2)
    else:
        # Tables don't exist yet — try alembic migrations (fresh local DB)
        print("Tables not found, running Alembic migrations...")
        for _ in range(30):
            r = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                env={**os.environ, "DATABASE_URL": db_url},
            )
            if r.returncode == 0:
                print("Migrations applied.")
                break
            time.sleep(2)
        else:
            print("Failed to apply migrations.", file=sys.stderr)
            sys.exit(1)

    os.execvp("python", ["python", "-m", "app.mcp.server"])


if __name__ == "__main__":
    main()
