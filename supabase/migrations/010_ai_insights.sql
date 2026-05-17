-- ============================================================
-- ALIYDA DB SETUP - BLOCK 10
-- ai_insights table
-- Gemini-generated natural language insights based on DB summaries.
-- ============================================================

create table public.ai_insights (
  id uuid primary key default gen_random_uuid(),

  user_id uuid not null references auth.users(id) on delete cascade,

  month text not null check (month ~ '^[0-9]{4}-[0-9]{2}$'),

  insight_type text not null default 'monthly'
    check (insight_type in ('monthly', 'dashboard', 'warning', 'recommendation', 'chat_context')),

  provider text not null default 'gemini',
  model text,
  prompt_version text,

  input_summary jsonb,
  insight_text text not null,

  is_stale boolean not null default false,

  created_at timestamptz not null default now()
);

create index idx_ai_insights_user_month
on public.ai_insights(user_id, month);

create index idx_ai_insights_user_created
on public.ai_insights(user_id, created_at desc);

create index idx_ai_insights_stale
on public.ai_insights(user_id, month, is_stale);