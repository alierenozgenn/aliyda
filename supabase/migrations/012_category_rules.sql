-- ============================================================
-- ALIYDA DB SETUP - BLOCK 12
-- category_rules table
-- User-specific categorization rules learned from corrections.
-- ============================================================

create table public.category_rules (
  id uuid primary key default gen_random_uuid(),

  user_id uuid not null references auth.users(id) on delete cascade,

  pattern text not null,
  category text not null,
  subcategory text,

  match_type text not null default 'contains'
    check (match_type in ('contains', 'starts_with', 'exact', 'regex')),

  priority integer not null default 100,
  is_active boolean not null default true,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  unique (user_id, pattern, category)
);

create trigger set_category_rules_updated_at
before update on public.category_rules
for each row
execute function public.set_updated_at();

create index idx_category_rules_user_id
on public.category_rules(user_id);

create index idx_category_rules_user_active
on public.category_rules(user_id, is_active);