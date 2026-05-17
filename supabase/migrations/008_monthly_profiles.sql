-- ============================================================
-- ALIYDA DB SETUP - BLOCK 8
-- monthly_profiles table
-- User-declared monthly income and monthly planning assumptions.
-- ============================================================

create table public.monthly_profiles (
  id uuid primary key default gen_random_uuid(),

  user_id uuid not null references auth.users(id) on delete cascade,

  month text not null check (month ~ '^[0-9]{4}-[0-9]{2}$'),

  declared_income numeric(14,2)
    check (declared_income is null or declared_income >= 0),

  income_source text not null default 'manual'
    check (income_source in ('manual', 'pdf', 'mixed', 'unknown')),

  savings_goal numeric(14,2)
    check (savings_goal is null or savings_goal >= 0),

  budget_goal numeric(14,2)
    check (budget_goal is null or budget_goal >= 0),

  notes text,

  is_finalized boolean not null default false,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  unique (user_id, month)
);

create trigger set_monthly_profiles_updated_at
before update on public.monthly_profiles
for each row
execute function public.set_updated_at();

create index idx_monthly_profiles_user_month
on public.monthly_profiles(user_id, month);