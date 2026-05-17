-- ============================================================
-- ALIYDA DB SETUP - BLOCK 5
-- statement_extractions table
-- ============================================================

create table public.statement_extractions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  statement_id uuid not null references public.statements(id) on delete cascade,

  provider text not null default 'gemini',
  model text,
  prompt_version text,

  raw_output jsonb,
  parsed_output jsonb,

  request_count integer not null default 1,
  input_token_estimate integer,
  output_token_estimate integer,

  status text not null default 'success'
    check (status in ('success', 'partial', 'failed')),

  error_message text,

  created_at timestamptz not null default now()
);

create index idx_statement_extractions_user_id
on public.statement_extractions(user_id);

create index idx_statement_extractions_statement_id
on public.statement_extractions(statement_id);

create index idx_statement_extractions_created_at
on public.statement_extractions(created_at desc);