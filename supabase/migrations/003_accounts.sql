-- ============================================================
-- ALIYDA DB SETUP - BLOCK 3
-- accounts table
-- ============================================================

create table public.accounts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,

  name text not null,
  institution_name text,

  account_type text not null default 'bank'
    check (account_type in ('bank', 'credit_card', 'cash', 'manual', 'wallet', 'other')),

  currency text not null default 'TRY',
  is_active boolean not null default true,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  unique (user_id, name)
);

create trigger set_accounts_updated_at
before update on public.accounts
for each row
execute function public.set_updated_at();

create index idx_accounts_user_id on public.accounts(user_id);
create index idx_accounts_user_active on public.accounts(user_id, is_active);