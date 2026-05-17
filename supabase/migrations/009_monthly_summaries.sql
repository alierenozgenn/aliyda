-- ============================================================
-- ALIYDA DB SETUP - BLOCK 9
-- monthly_summaries table
-- Cached deterministic summaries calculated by backend.
-- Gemini should interpret this, not calculate it.
-- ============================================================

create table public.monthly_summaries (
  id uuid primary key default gen_random_uuid(),

  user_id uuid not null references auth.users(id) on delete cascade,

  month text not null check (month ~ '^[0-9]{4}-[0-9]{2}$'),

  total_income numeric(14,2) not null default 0,
  total_expense numeric(14,2) not null default 0,
  total_transfer_in numeric(14,2) not null default 0,
  total_transfer_out numeric(14,2) not null default 0,
  net_balance numeric(14,2) not null default 0,

  transaction_count integer not null default 0,
  income_count integer not null default 0,
  expense_count integer not null default 0,

  top_categories jsonb not null default '[]'::jsonb,
  largest_transactions jsonb not null default '[]'::jsonb,
  recurring_candidates jsonb not null default '[]'::jsonb,

  is_stale boolean not null default false,

  calculated_at timestamptz not null default now(),

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  unique (user_id, month)
);

create trigger set_monthly_summaries_updated_at
before update on public.monthly_summaries
for each row
execute function public.set_updated_at();

create index idx_monthly_summaries_user_month
on public.monthly_summaries(user_id, month);

create index idx_monthly_summaries_stale
on public.monthly_summaries(user_id, month, is_stale);