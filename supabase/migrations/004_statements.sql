-- ============================================================
-- ALIYDA DB SETUP - BLOCK 4
-- statements table
-- ============================================================

create table public.statements (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  account_id uuid references public.accounts(id) on delete set null,

  month text not null check (month ~ '^[0-9]{4}-[0-9]{2}$'),

  source text not null default 'pdf'
    check (source in ('pdf', 'manual', 'import', 'demo')),

  file_name text,
  file_mime_type text,
  file_size_bytes bigint,

  status text not null default 'uploaded'
    check (status in (
      'uploaded',
      'extracting',
      'extracted',
      'pending_review',
      'approved',
      'saved',
      'failed',
      'cancelled',
      'deleted'
    )),

  extraction_confidence numeric(5,4)
    check (
      extraction_confidence is null
      or (extraction_confidence >= 0 and extraction_confidence <= 1)
    ),

  income_detected boolean,
  notes text,
  error_message text,

  is_deleted boolean not null default false,
  deleted_at timestamptz,
  deleted_reason text,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger set_statements_updated_at
before update on public.statements
for each row
execute function public.set_updated_at();

create index idx_statements_user_id on public.statements(user_id);
create index idx_statements_user_month on public.statements(user_id, month);
create index idx_statements_user_status on public.statements(user_id, status);
create index idx_statements_account_id on public.statements(account_id);
create index idx_statements_not_deleted on public.statements(user_id, is_deleted);