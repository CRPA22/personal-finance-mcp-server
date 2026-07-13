-- =============================================================================
-- Personal Finance MCP Server — Schema para Supabase
-- =============================================================================
-- Instrucciones:
--   1. Ejecutar en el SQL Editor de Supabase (https://app.supabase.com)
--   2. Supabase ya provee auth.users — NO recrear esa tabla
--   3. Habilitar RLS después de crear las tablas (incluido abajo)
-- =============================================================================


-- ---------------------------------------------------------------------------
-- EXTENSIONES
-- ---------------------------------------------------------------------------
create extension if not exists "uuid-ossp";


-- ---------------------------------------------------------------------------
-- TABLA: profiles
-- Reemplaza la tabla `users` del esquema anterior.
-- Referencia auth.users de Supabase; NO almacena contraseñas.
-- ---------------------------------------------------------------------------
create table public.profiles (
    id          uuid primary key references auth.users(id) on delete cascade,
    email       text not null,
    role        text not null default 'user' check (role in ('user', 'admin')),
    created_at  timestamptz not null default now()
);

-- Se llena automáticamente cuando un usuario se registra en Supabase Auth
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
    insert into public.profiles (id, email)
    values (new.id, new.email);
    return new;
end;
$$;

create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();


-- ---------------------------------------------------------------------------
-- TABLA: currencies
-- ---------------------------------------------------------------------------
create table public.currencies (
    code    text primary key,
    name    text not null,
    symbol  text not null
);

insert into public.currencies (code, name, symbol) values
    ('PEN', 'Sol peruano',    'S/'),
    ('USD', 'Dólar americano','$'),
    ('EUR', 'Euro',           '€');


-- ---------------------------------------------------------------------------
-- TABLA: account_types
-- ---------------------------------------------------------------------------
create table public.account_types (
    code  text primary key,
    label text not null
);

insert into public.account_types (code, label) values
    ('checking',   'Cuenta corriente'),
    ('savings',    'Cuenta de ahorros'),
    ('investment', 'Inversiones'),
    ('credit',     'Tarjeta de crédito'),
    ('cash',       'Efectivo');


-- ---------------------------------------------------------------------------
-- TABLA: accounts
-- ---------------------------------------------------------------------------
create table public.accounts (
    id          uuid primary key default uuid_generate_v4(),
    user_id     uuid not null references auth.users(id) on delete cascade,
    name        text not null,
    type        text not null references public.account_types(code),
    currency    text not null default 'PEN' references public.currencies(code),
    balance     numeric(15, 2) not null default 0,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

create index ix_accounts_user_id on public.accounts(user_id);


-- ---------------------------------------------------------------------------
-- TABLA: transactions
-- type: income | expense | transfer
-- transfer_peer_id: vincula los dos lados de una transferencia entre cuentas
-- ---------------------------------------------------------------------------
create table public.transactions (
    id                uuid primary key default uuid_generate_v4(),
    account_id        uuid not null references public.accounts(id) on delete cascade,
    user_id           uuid not null references auth.users(id) on delete cascade,
    amount            numeric(15, 2) not null check (amount > 0),
    type              text not null check (type in ('income', 'expense', 'transfer')),
    category          text not null,
    date              date not null,
    description       text,
    transfer_peer_id  uuid references public.transactions(id) on delete set null,
    created_at        timestamptz not null default now(),
    updated_at        timestamptz not null default now()
);

create index ix_transactions_account_id  on public.transactions(account_id);
create index ix_transactions_user_id     on public.transactions(user_id);
create index ix_transactions_date        on public.transactions(date);
create index ix_transactions_type        on public.transactions(type);


-- ---------------------------------------------------------------------------
-- TRIGGER: updated_at automático para accounts y transactions
-- ---------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger trg_accounts_updated_at
    before update on public.accounts
    for each row execute procedure public.set_updated_at();

create trigger trg_transactions_updated_at
    before update on public.transactions
    for each row execute procedure public.set_updated_at();


-- ---------------------------------------------------------------------------
-- ROW LEVEL SECURITY (RLS)
-- Cada usuario solo puede ver y modificar sus propios datos.
-- ---------------------------------------------------------------------------

alter table public.profiles     enable row level security;
alter table public.accounts     enable row level security;
alter table public.transactions enable row level security;


-- profiles: el usuario solo ve y edita su propio perfil
create policy "profiles: select own"
    on public.profiles for select
    using (auth.uid() = id);

create policy "profiles: update own"
    on public.profiles for update
    using (auth.uid() = id);


-- accounts: el usuario gestiona solo sus cuentas
create policy "accounts: select own"
    on public.accounts for select
    using (auth.uid() = user_id);

create policy "accounts: insert own"
    on public.accounts for insert
    with check (auth.uid() = user_id);

create policy "accounts: update own"
    on public.accounts for update
    using (auth.uid() = user_id);

create policy "accounts: delete own"
    on public.accounts for delete
    using (auth.uid() = user_id);


-- transactions: el usuario gestiona solo sus transacciones
-- user_id en la tabla evita hacer JOIN con accounts para cada política
create policy "transactions: select own"
    on public.transactions for select
    using (auth.uid() = user_id);

create policy "transactions: insert own"
    on public.transactions for insert
    with check (auth.uid() = user_id);

create policy "transactions: update own"
    on public.transactions for update
    using (auth.uid() = user_id);

create policy "transactions: delete own"
    on public.transactions for delete
    using (auth.uid() = user_id);


-- ---------------------------------------------------------------------------
-- TABLA: categories
-- Categorías predefinidas (is_default=true) compartidas para todos los usuarios.
-- ---------------------------------------------------------------------------
create table public.categories (
    id          uuid primary key default uuid_generate_v4(),
    name        text not null,
    type        text not null check (type in ('income', 'expense', 'transfer')),
    is_default  boolean not null default true,
    created_at  timestamptz not null default now(),
    unique (name, type)
);

create index ix_categories_type on public.categories(type);

-- Seed: categorías de gastos
insert into public.categories (name, type) values
    ('alimentación',   'expense'),
    ('supermercado',   'expense'),
    ('restaurantes',   'expense'),
    ('transporte',     'expense'),
    ('combustible',    'expense'),
    ('vivienda',       'expense'),
    ('alquiler',       'expense'),
    ('servicios',      'expense'),
    ('electricidad',   'expense'),
    ('agua',           'expense'),
    ('internet',       'expense'),
    ('teléfono',       'expense'),
    ('entretenimiento','expense'),
    ('streaming',      'expense'),
    ('cine',           'expense'),
    ('suscripciones',  'expense'),
    ('salud',          'expense'),
    ('farmacia',       'expense'),
    ('medicamentos',   'expense'),
    ('educación',      'expense'),
    ('ropa',           'expense'),
    ('regalos',        'expense'),
    ('donaciones',     'expense'),
    ('viajes',         'expense'),
    ('hotel',          'expense'),
    ('seguros',        'expense'),
    ('impuestos',      'expense'),
    ('otro',           'expense');

-- Seed: categorías de ingresos
insert into public.categories (name, type) values
    ('salario',         'income'),
    ('freelance',       'income'),
    ('inversiones',     'income'),
    ('dividendos',      'income'),
    ('intereses',       'income'),
    ('alquiler_ingreso','income'),
    ('regalo',          'income'),
    ('reembolso',       'income'),
    ('venta',           'income'),
    ('otro',            'income');

-- Seed: categoría de transferencias
insert into public.categories (name, type) values
    ('transferencia', 'transfer');

-- RLS: las categorías predefinidas son de solo lectura para todos los usuarios autenticados
alter table public.categories enable row level security;

create policy "categories: select all authenticated"
    on public.categories for select
    to authenticated
    using (true);

-- RLS: currencies y account_types son tablas de referencia, solo lectura
alter table public.currencies    enable row level security;
alter table public.account_types enable row level security;

create policy "currencies: select all authenticated"
    on public.currencies for select
    to authenticated
    using (true);

create policy "account_types: select all authenticated"
    on public.account_types for select
    to authenticated
    using (true);


-- ---------------------------------------------------------------------------
-- VISTA ÚTIL: resumen de gastos e ingresos por mes (excluye transferencias)
-- ---------------------------------------------------------------------------
create or replace view public.monthly_flow as
select
    user_id,
    extract(year  from date)::int as year,
    extract(month from date)::int as month,
    sum(case when type = 'income'  then amount else 0 end) as total_income,
    sum(case when type = 'expense' then amount else 0 end) as total_expenses,
    sum(case when type = 'income'  then amount else 0 end)
  - sum(case when type = 'expense' then amount else 0 end) as net
from public.transactions
where type != 'transfer'
group by user_id, year, month
order by year desc, month desc;
