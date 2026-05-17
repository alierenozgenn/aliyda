-- ============================================================
-- ALIYDA DB SETUP - BLOCK 18
-- Strengthen monthly_summaries income fields
-- ============================================================

alter table public.monthly_summaries
add column detected_income numeric(14,2) not null default 0;

alter table public.monthly_summaries
add column declared_income numeric(14,2) not null default 0;

alter table public.monthly_summaries
add column income_basis text not null default 'none'
check (income_basis in ('pdf', 'manual', 'mixed', 'none'));