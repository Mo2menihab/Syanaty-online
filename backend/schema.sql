-- ════════════════════════════════════════════
-- SYANATY — Supabase Database Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ════════════════════════════════════════════

-- Supabase Auth already provides the `auth.users` table.
-- We link every row below to auth.users.id via user_id.

-- ── CARS ─────────────────────────────────────
create table if not exists cars (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references auth.users(id) on delete cascade not null,
  name        text not null default 'My Car',
  year        int  not null default 2020,
  emoji       text not null default '🚗',
  odometer    int  not null default 0,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- ── PARTS CATALOG ────────────────────────────
create table if not exists parts (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid references auth.users(id) on delete cascade not null,
  car_id            uuid references cars(id) on delete cascade not null,
  name              text not null,
  interval_km       int  not null,
  interval_months   int  not null,
  last_replaced_km  int  not null default 0,
  last_replaced_date date not null default current_date,
  cost_new          numeric(10,2) not null default 0,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

-- ── MAINTENANCE HISTORY ──────────────────────
create table if not exists history (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references auth.users(id) on delete cascade not null,
  car_id      uuid references cars(id) on delete cascade not null,
  date        date not null,
  mileage     int  not null,
  service     text not null,
  cost        numeric(10,2) not null default 0,
  urgent      boolean not null default false,
  created_at  timestamptz not null default now()
);

-- ── EXPENSES (fuel + maintenance transactions) ─
create table if not exists expenses (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references auth.users(id) on delete cascade not null,
  car_id      uuid references cars(id) on delete cascade not null,
  type        text not null check (type in ('fuel','maintenance')),
  amount      numeric(10,2) not null,
  note        text,
  date        date not null,
  created_at  timestamptz not null default now()
);

-- ════════════════════════════════════════════
-- ROW LEVEL SECURITY (RLS)
-- Ensures each user can only ever see/edit their own rows.
-- Without this, anyone with the API key could read everyone's data.
-- ════════════════════════════════════════════

alter table cars     enable row level security;
alter table parts    enable row level security;
alter table history  enable row level security;
alter table expenses enable row level security;

create policy "Users manage their own cars"
  on cars for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Users manage their own parts"
  on parts for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Users manage their own history"
  on history for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Users manage their own expenses"
  on expenses for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- ════════════════════════════════════════════
-- AUTO-UPDATE updated_at TIMESTAMP
-- ════════════════════════════════════════════

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger cars_updated_at  before update on cars  for each row execute function set_updated_at();
create trigger parts_updated_at before update on parts for each row execute function set_updated_at();
