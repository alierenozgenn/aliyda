-- ============================================================
-- ALIYDA DB SETUP - BLOCK 13
-- Enable Row Level Security
-- ============================================================

alter table public.profiles enable row level security;
alter table public.accounts enable row level security;
alter table public.statements enable row level security;
alter table public.statement_extractions enable row level security;
alter table public.transaction_drafts enable row level security;
alter table public.transactions enable row level security;
alter table public.monthly_profiles enable row level security;
alter table public.monthly_summaries enable row level security;
alter table public.ai_insights enable row level security;
alter table public.chat_sessions enable row level security;
alter table public.chat_messages enable row level security;
alter table public.category_rules enable row level security;