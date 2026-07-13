# -*- coding: utf-8 -*-
"""
Script de migracion completa a Supabase.
Ejecutar desde la raiz del proyecto:
    .venv\\Scripts\\python.exe docs\\migrate_to_supabase.py
"""

import os
import uuid
import json
import requests
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from urllib.parse import urlparse

# Cargar .env desde la raiz del proyecto
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# ── Configuración (leída desde .env) ──────────────────────────────────────────
SUPABASE_URL  = os.environ["SUPABASE_URL"]
SERVICE_KEY   = os.environ["SUPABASE_SERVICE_KEY"]
USER_EMAIL    = os.environ["SUPABASE_USER_EMAIL"]
USER_PASSWORD = os.environ["SUPABASE_USER_PASSWORD"]

_sb_url = urlparse(os.environ["DATABASE_URL"])
SB_CONN = dict(
    host=_sb_url.hostname,
    port=_sb_url.port or 5432,
    dbname=(_sb_url.path or "/postgres").lstrip("/"),
    user=_sb_url.username,
    password=os.environ["SUPABASE_DB_PASSWORD"],
    connect_timeout=30,
)
LOCAL_CONN = dict(
    host="localhost", port=5432, dbname="finance_mcp",
    user="postgres", password="postgres", connect_timeout=10,
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def sb_conn():  return psycopg2.connect(**SB_CONN)
def local_conn(): return psycopg2.connect(**LOCAL_CONN)

def step(msg): print(f"\n{'='*60}\n  {msg}\n{'='*60}")
def ok(msg):   print(f"  ✓ {msg}")
def info(msg): print(f"  · {msg}")


# ── PASO 1: Crear schema en Supabase ──────────────────────────────────────────
SCHEMA_SQL = """
-- Extensiones
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- TABLA: currencies
CREATE TABLE IF NOT EXISTS public.currencies (
    code   TEXT PRIMARY KEY,
    name   TEXT NOT NULL,
    symbol TEXT NOT NULL
);

-- TABLA: account_types
CREATE TABLE IF NOT EXISTS public.account_types (
    code  TEXT PRIMARY KEY,
    label TEXT NOT NULL
);

-- TABLA: user_profiles (reemplaza users, referencia auth.users)
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id         UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role       TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Trigger: crear perfil automáticamente al registrarse
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    INSERT INTO public.user_profiles (id, role)
    VALUES (NEW.id, 'user')
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- TABLA: categories
CREATE TABLE IF NOT EXISTS public.categories (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name       TEXT NOT NULL,
    type       TEXT NOT NULL CHECK (type IN ('income','expense','transfer')),
    is_default BOOLEAN NOT NULL DEFAULT true,
    user_id    UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (name, type, user_id)
);
CREATE INDEX IF NOT EXISTS ix_categories_type    ON public.categories(type);
CREATE INDEX IF NOT EXISTS ix_categories_user_id ON public.categories(user_id);

-- TABLA: accounts
CREATE TABLE IF NOT EXISTS public.accounts (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name       TEXT NOT NULL,
    type       TEXT NOT NULL REFERENCES public.account_types(code),
    currency   TEXT NOT NULL DEFAULT 'PEN' REFERENCES public.currencies(code),
    balance    NUMERIC(15,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_accounts_user_id ON public.accounts(user_id);

-- TABLA: transactions
CREATE TABLE IF NOT EXISTS public.transactions (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id       UUID NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,
    user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    category_id      UUID NOT NULL REFERENCES public.categories(id),
    amount           NUMERIC(15,2) NOT NULL CHECK (amount > 0),
    type             TEXT NOT NULL CHECK (type IN ('income','expense','transfer')),
    date             DATE NOT NULL,
    description      TEXT,
    transfer_peer_id UUID REFERENCES public.transactions(id) ON DELETE SET NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_transactions_account_id  ON public.transactions(account_id);
CREATE INDEX IF NOT EXISTS ix_transactions_user_id     ON public.transactions(user_id);
CREATE INDEX IF NOT EXISTS ix_transactions_category_id ON public.transactions(category_id);
CREATE INDEX IF NOT EXISTS ix_transactions_date        ON public.transactions(date);

-- TABLA: budgets
CREATE TABLE IF NOT EXISTS public.budgets (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    category_id  UUID NOT NULL REFERENCES public.categories(id) ON DELETE CASCADE,
    month        DATE NOT NULL,
    limit_amount NUMERIC(15,2) NOT NULL,
    currency     TEXT NOT NULL DEFAULT 'PEN' REFERENCES public.currencies(code),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, category_id, month)
);
CREATE INDEX IF NOT EXISTS ix_budgets_user_id ON public.budgets(user_id);
CREATE INDEX IF NOT EXISTS ix_budgets_month   ON public.budgets(month);

-- TABLA: budget_alerts
CREATE TABLE IF NOT EXISTS public.budget_alerts (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    budget_id         UUID NOT NULL REFERENCES public.budgets(id) ON DELETE CASCADE,
    threshold_percent INTEGER NOT NULL CHECK (threshold_percent BETWEEN 1 AND 100),
    triggered_at      TIMESTAMPTZ
);

-- Trigger: updated_at automático
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$;

DROP TRIGGER IF EXISTS trg_accounts_updated_at     ON public.accounts;
DROP TRIGGER IF EXISTS trg_transactions_updated_at ON public.transactions;
CREATE TRIGGER trg_accounts_updated_at     BEFORE UPDATE ON public.accounts     FOR EACH ROW EXECUTE PROCEDURE public.set_updated_at();
CREATE TRIGGER trg_transactions_updated_at BEFORE UPDATE ON public.transactions FOR EACH ROW EXECUTE PROCEDURE public.set_updated_at();

-- RLS
ALTER TABLE public.user_profiles  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.accounts        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.budgets         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.budget_alerts   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.currencies      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.account_types   ENABLE ROW LEVEL SECURITY;

-- Políticas
DO $$ BEGIN
  -- user_profiles
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='user_profiles' AND policyname='profiles: select own') THEN
    CREATE POLICY "profiles: select own" ON public.user_profiles FOR SELECT USING (auth.uid() = id);
    CREATE POLICY "profiles: update own" ON public.user_profiles FOR UPDATE USING (auth.uid() = id);
  END IF;
  -- categories (sistema + propias)
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='categories' AND policyname='categories: select') THEN
    CREATE POLICY "categories: select"  ON public.categories FOR SELECT TO authenticated USING (user_id IS NULL OR auth.uid() = user_id);
    CREATE POLICY "categories: insert"  ON public.categories FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
    CREATE POLICY "categories: delete"  ON public.categories FOR DELETE TO authenticated USING (auth.uid() = user_id AND is_default = false);
  END IF;
  -- accounts
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='accounts' AND policyname='accounts: select own') THEN
    CREATE POLICY "accounts: select own" ON public.accounts FOR SELECT USING (auth.uid() = user_id);
    CREATE POLICY "accounts: insert own" ON public.accounts FOR INSERT WITH CHECK (auth.uid() = user_id);
    CREATE POLICY "accounts: update own" ON public.accounts FOR UPDATE USING (auth.uid() = user_id);
    CREATE POLICY "accounts: delete own" ON public.accounts FOR DELETE USING (auth.uid() = user_id);
  END IF;
  -- transactions
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='transactions' AND policyname='transactions: select own') THEN
    CREATE POLICY "transactions: select own" ON public.transactions FOR SELECT USING (auth.uid() = user_id);
    CREATE POLICY "transactions: insert own" ON public.transactions FOR INSERT WITH CHECK (auth.uid() = user_id);
    CREATE POLICY "transactions: update own" ON public.transactions FOR UPDATE USING (auth.uid() = user_id);
    CREATE POLICY "transactions: delete own" ON public.transactions FOR DELETE USING (auth.uid() = user_id);
  END IF;
  -- budgets
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='budgets' AND policyname='budgets: select own') THEN
    CREATE POLICY "budgets: select own" ON public.budgets FOR SELECT USING (auth.uid() = user_id);
    CREATE POLICY "budgets: insert own" ON public.budgets FOR INSERT WITH CHECK (auth.uid() = user_id);
    CREATE POLICY "budgets: update own" ON public.budgets FOR UPDATE USING (auth.uid() = user_id);
    CREATE POLICY "budgets: delete own" ON public.budgets FOR DELETE USING (auth.uid() = user_id);
  END IF;
  -- currencies y account_types: lectura pública
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='currencies' AND policyname='currencies: select') THEN
    CREATE POLICY "currencies: select"     ON public.currencies     FOR SELECT TO authenticated USING (true);
    CREATE POLICY "account_types: select"  ON public.account_types  FOR SELECT TO authenticated USING (true);
  END IF;
END $$;
"""


def create_schema():
    step("1/7 — Creando schema en Supabase")
    conn = sb_conn()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(SCHEMA_SQL)
    conn.close()
    ok("Schema creado correctamente")


# ── PASO 2: Crear usuario en Supabase Auth ────────────────────────────────────
def create_auth_user() -> str:
    step("2/7 — Creando usuario en Supabase Auth")
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    }

    # Verificar si ya existe
    r = requests.get(f"{SUPABASE_URL}/auth/v1/admin/users?email={USER_EMAIL}", headers=headers)
    users = r.json().get("users", [])
    if users:
        user_id = users[0]["id"]
        ok(f"Usuario ya existe: {user_id}")
        return user_id

    # Crear nuevo
    payload = {
        "email": USER_EMAIL,
        "password": USER_PASSWORD,
        "email_confirm": True,
    }
    r = requests.post(f"{SUPABASE_URL}/auth/v1/admin/users", headers=headers, json=payload)
    r.raise_for_status()
    user_id = r.json()["id"]
    ok(f"Usuario creado: {user_id}")

    # Insertar perfil manualmente (el trigger puede no disparar en creación admin)
    conn = sb_conn()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO public.user_profiles (id, role) VALUES (%s, 'user') ON CONFLICT DO NOTHING",
        (user_id,)
    )
    conn.close()
    ok("Perfil de usuario creado")
    return user_id


# ── PASO 3: Migrar datos de referencia ───────────────────────────────────────
def migrate_reference_data():
    step("3/7 — Migrando currencies, account_types y categories")
    local = local_conn()
    supa  = sb_conn()
    lc, sc = local.cursor(), supa.cursor()

    # currencies
    lc.execute("SELECT code, name, symbol FROM currencies")
    rows = lc.fetchall()
    execute_values(sc, "INSERT INTO public.currencies (code, name, symbol) VALUES %s ON CONFLICT DO NOTHING", rows)
    supa.commit()
    ok(f"{len(rows)} currencies migradas")

    # account_types
    lc.execute("SELECT code, label FROM account_types")
    rows = lc.fetchall()
    execute_values(sc, "INSERT INTO public.account_types (code, label) VALUES %s ON CONFLICT DO NOTHING", rows)
    supa.commit()
    ok(f"{len(rows)} account_types migrados")

    local.close()
    supa.close()


def migrate_categories(new_user_id: str) -> dict:
    """Migra categorías y devuelve mapeo old_id → new_id."""
    step("4/7 — Migrando categories")
    local = local_conn()
    supa  = sb_conn()
    lc, sc = local.cursor(), supa.cursor()

    lc.execute("SELECT id, name, type, is_default FROM categories ORDER BY is_default DESC, name")
    cats = lc.fetchall()

    id_map = {}
    for old_id, name, ctype, is_default in cats:
        new_id = str(uuid.uuid4())
        sc.execute(
            """INSERT INTO public.categories (id, name, type, is_default, user_id)
               VALUES (%s, %s, %s, %s, NULL)
               ON CONFLICT (name, type, user_id) DO UPDATE SET name=EXCLUDED.name
               RETURNING id""",
            (new_id, name, ctype, is_default)
        )
        returned_id = sc.fetchone()[0]
        id_map[str(old_id)] = str(returned_id)

    supa.commit()
    local.close()
    supa.close()
    ok(f"{len(cats)} categorías migradas")
    return id_map


# ── PASO 4: Migrar cuentas ────────────────────────────────────────────────────
def migrate_accounts(new_user_id: str) -> dict:
    step("5/7 — Migrando accounts")
    local = local_conn()
    supa  = sb_conn()
    lc, sc = local.cursor(), supa.cursor()

    lc.execute("SELECT id, name, type, currency, balance, created_at FROM accounts")
    accounts = lc.fetchall()

    acc_id_map = {}
    for old_id, name, atype, currency, balance, created_at in accounts:
        new_id = str(uuid.uuid4())
        sc.execute(
            """INSERT INTO public.accounts (id, user_id, name, type, currency, balance, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
            (new_id, new_user_id, name, atype, currency, balance, created_at)
        )
        acc_id_map[str(old_id)] = new_id

    supa.commit()
    local.close()
    supa.close()
    ok(f"{len(accounts)} cuentas migradas")
    return acc_id_map


# ── PASO 5: Migrar transacciones ──────────────────────────────────────────────
def migrate_transactions(new_user_id: str, acc_id_map: dict, cat_id_map: dict):
    step("6/7 — Migrando transactions")
    local = local_conn()
    supa  = sb_conn()
    lc, sc = local.cursor(), supa.cursor()

    lc.execute("""
        SELECT id, account_id, category_id, amount, type, date, description,
               transfer_peer_id, created_at
        FROM transactions
        ORDER BY date ASC, created_at ASC
    """)
    txs = lc.fetchall()

    # Primera pasada: insertar sin transfer_peer_id para evitar FK circular
    old_to_new = {}
    rows_first = []
    for old_id, acc_id, cat_id, amount, ttype, date, desc, peer_id, created_at in txs:
        new_id      = str(uuid.uuid4())
        new_acc_id  = acc_id_map.get(str(acc_id))
        new_cat_id  = cat_id_map.get(str(cat_id))
        if not new_acc_id or not new_cat_id:
            info(f"  SKIP tx {old_id} — account o category no mapeada")
            continue
        old_to_new[str(old_id)] = new_id
        rows_first.append((new_id, new_acc_id, new_user_id, new_cat_id, amount, ttype, date, desc, created_at))

    execute_values(sc, """
        INSERT INTO public.transactions
            (id, account_id, user_id, category_id, amount, type, date, description, created_at)
        VALUES %s ON CONFLICT DO NOTHING
    """, rows_first)
    supa.commit()

    # Segunda pasada: actualizar transfer_peer_id
    peer_updates = []
    for old_id, _, _, _, _, _, _, peer_id, _ in txs:
        if peer_id and str(old_id) in old_to_new and str(peer_id) in old_to_new:
            peer_updates.append((old_to_new[str(peer_id)], old_to_new[str(old_id)]))

    for new_peer_id, new_tx_id in peer_updates:
        sc.execute(
            "UPDATE public.transactions SET transfer_peer_id = %s WHERE id = %s",
            (new_peer_id, new_tx_id)
        )
    supa.commit()

    local.close()
    supa.close()
    ok(f"{len(rows_first)} transacciones migradas, {len(peer_updates)} pares de transferencia vinculados")


# ── PASO 6: Actualizar .env ────────────────────────────────────────────────────
def update_env(new_user_id: str):
    step("7/7 — Actualizando .env")
    env_path = ".env"
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        with open(".env.example", "r", encoding="utf-8") as f:
            content = f.read()

    supabase_db_url = os.environ["DATABASE_URL"]

    lines = content.splitlines()
    new_lines = []
    found_db, found_user = False, False
    for line in lines:
        if line.startswith("DATABASE_URL="):
            new_lines.append(f"DATABASE_URL={supabase_db_url}")
            found_db = True
        elif line.startswith("DEFAULT_USER_ID="):
            new_lines.append(f"DEFAULT_USER_ID={new_user_id}")
            found_user = True
        else:
            new_lines.append(line)

    if not found_db:
        new_lines.append(f"DATABASE_URL={supabase_db_url}")
    if not found_user:
        new_lines.append(f"DEFAULT_USER_ID={new_user_id}")

    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
    ok(f".env actualizado con Supabase DB y user_id={new_user_id}")


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n== MIGRACION A SUPABASE ==\n")

    create_schema()
    new_user_id  = create_auth_user()
    migrate_reference_data()
    cat_id_map   = migrate_categories(new_user_id)
    acc_id_map   = migrate_accounts(new_user_id)
    migrate_transactions(new_user_id, acc_id_map, cat_id_map)
    update_env(new_user_id)

    print("\n" + "="*60)
    print("  MIGRACION COMPLETADA")
    print(f"  Usuario: {USER_EMAIL}")
    print(f"  UUID:    {new_user_id}")
    print("="*60 + "\n")
