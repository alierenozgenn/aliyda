-- ============================================================
-- ALIYDA DB SETUP - BLOCK 1
-- Helper functions
-- ============================================================

create extension if not exists "pgcrypto";

-- Automatically updates updated_at columns
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- Automatically creates a profile row after a new auth user signs up.
-- The trigger using this function will be created after profiles table exists.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, email, full_name)
  values (
    new.id,
    new.email,
    coalesce(
      new.raw_user_meta_data->>'full_name',
      new.raw_user_meta_data->>'name'
    )
  )
  on conflict (id) do nothing;

  return new;
end;
$$;