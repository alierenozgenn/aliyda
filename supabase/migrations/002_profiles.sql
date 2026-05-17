-- ============================================================
-- ALIYDA DB SETUP - BLOCK 2
-- profiles table
-- ============================================================

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  full_name text,
  avatar_url text,

  preferred_currency text not null default 'TRY',
  onboarding_completed boolean not null default false,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger set_profiles_updated_at
before update on public.profiles
for each row
execute function public.set_updated_at();

drop trigger if exists on_auth_user_created on auth.users;

create trigger on_auth_user_created
after insert on auth.users
for each row
execute function public.handle_new_user();