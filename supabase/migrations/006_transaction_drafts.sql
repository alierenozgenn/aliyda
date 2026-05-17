-- ============================================================
-- ALIYDA DB SETUP - BLOCK 6
-- transaction_drafts table
-- ============================================================

create table public.transaction_drafts (
  id uuid primary key default gen_random_uuid(),

  user_id uuid not null references auth.users(id) on delete cascade,
  statement_id uuid references public.statements(id) on delete cascade,
  account_id uuid references public.accounts(id) on delete set null,

  month text check (month is null or month ~ '^[0-9]{4}-[0-9]{2}$'),

  transaction_date date,
  transaction_time time,

  description text,
  original_description text,

  amount numeric(14,2) check (amount is null or amount >= 0),
  currency text not null default 'TRY',

  direction text
    check (direction in ('income', 'expense', 'transfer_in', 'transfer_out', 'transfer', 'unknown')),

  category text,
  subcategory text,
  counterparty text,

  confidence numeric(5,4)
    check (
      confidence is null
      or (confidence >= 0 and confidence <= 1)
    ),

  needs_review boolean not null default true,

  review_status text not null default 'pending'
    check (review_status in ('pending', 'approved', 'edited', 'rejected')),

  user_notes text,
  raw_item jsonb,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger set_transaction_drafts_updated_at
before update on public.transaction_drafts
for each row
execute function public.set_updated_at();

create index idx_transaction_drafts_user_id
on public.transaction_drafts(user_id);

create index idx_transaction_drafts_statement_id
on public.transaction_drafts(statement_id);

create index idx_transaction_drafts_review_status
on public.transaction_drafts(user_id, review_status);

create index idx_transaction_drafts_month
on public.transaction_drafts(user_id, month);

create index idx_transaction_drafts_date
on public.transaction_drafts(user_id, transaction_date);