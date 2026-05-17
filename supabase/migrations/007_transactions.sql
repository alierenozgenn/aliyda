-- ============================================================
-- ALIYDA DB SETUP - BLOCK 7
-- transactions table
-- Final, user-confirmed financial records.
-- Dashboard and chatbot use this as source of truth.
-- ============================================================

create table public.transactions (
  id uuid primary key default gen_random_uuid(),

  user_id uuid not null references auth.users(id) on delete cascade,

  account_id uuid references public.accounts(id) on delete set null,
  statement_id uuid references public.statements(id) on delete set null,
  draft_id uuid references public.transaction_drafts(id) on delete set null,

  month text not null check (month ~ '^[0-9]{4}-[0-9]{2}$'),

  transaction_date date not null,
  transaction_time time,

  description text not null,

  amount numeric(14,2) not null check (amount >= 0),
  currency text not null default 'TRY',

  direction text not null
    check (direction in ('income', 'expense', 'transfer_in', 'transfer_out', 'transfer')),

  category text,
  subcategory text,
  counterparty text,

  payment_method text,
  location text,

  source text not null default 'manual'
    check (source in ('pdf', 'manual', 'import', 'demo', 'system')),

  is_user_confirmed boolean not null default true,

  is_recurring boolean not null default false,
  is_excluded_from_budget boolean not null default false,

  is_deleted boolean not null default false,
  deleted_at timestamptz,
  deleted_reason text,

  metadata jsonb not null default '{}'::jsonb,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger set_transactions_updated_at
before update on public.transactions
for each row
execute function public.set_updated_at();

create index idx_transactions_user_id
on public.transactions(user_id);

create index idx_transactions_user_month
on public.transactions(user_id, month);

create index idx_transactions_user_date
on public.transactions(user_id, transaction_date desc);

create index idx_transactions_user_direction
on public.transactions(user_id, direction);

create index idx_transactions_user_category
on public.transactions(user_id, category);

create index idx_transactions_account_id
on public.transactions(account_id);

create index idx_transactions_statement_id
on public.transactions(statement_id);

create index idx_transactions_source
on public.transactions(user_id, source);

create index idx_transactions_not_deleted
on public.transactions(user_id, month, is_deleted);