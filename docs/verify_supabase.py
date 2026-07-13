# -*- coding: utf-8 -*-
import os
import psycopg2
from pathlib import Path

_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from urllib.parse import urlparse
_u = urlparse(os.environ["DATABASE_URL"])
conn = psycopg2.connect(
    host=_u.hostname, port=_u.port or 5432,
    dbname=(_u.path or "/postgres").lstrip("/"),
    user=_u.username, password=os.environ["SUPABASE_DB_PASSWORD"]
)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM public.accounts")
print("Cuentas:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM public.transactions")
print("Transacciones:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM public.categories")
print("Categorias:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM public.transactions WHERE transfer_peer_id IS NOT NULL")
print("Transferencias vinculadas:", cur.fetchone()[0])

cur.execute("SELECT a.name, a.currency, a.balance FROM public.accounts a ORDER BY a.currency, a.balance DESC")
print("\n--- Cuentas ---")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} {row[2]}")

cur.execute("""
    SELECT t.type, c.name, t.amount, t.date, t.description
    FROM public.transactions t
    JOIN public.categories c ON c.id = t.category_id
    WHERE t.type != 'transfer'
    ORDER BY t.date DESC LIMIT 8
""")
print("\n--- Ultimas transacciones ---")
for row in cur.fetchall():
    print(f"  {row[3]} | {row[0]:7} | {row[1]:15} | {row[2]:8} | {row[4]}")

conn.close()
