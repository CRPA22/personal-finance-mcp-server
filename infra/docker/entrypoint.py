#!/usr/bin/env python3
"""Docker entrypoint: wait for DB, run migrations, start MCP server."""
import os
import subprocess
import sys
import time

def main():
    print("Waiting for PostgreSQL...")
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/finance_mcp")
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
        print("Failed to connect to PostgreSQL", file=sys.stderr)
        sys.exit(1)
    os.execvp("python", ["python", "-m", "app.mcp.server"])

if __name__ == "__main__":
    main()
