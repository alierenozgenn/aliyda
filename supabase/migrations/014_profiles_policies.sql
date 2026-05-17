-- ============================================================
-- ALIYDA DB SETUP - BLOCK 14
-- profiles RLS policies
-- ============================================================

create policy "Users can view own profile"
on public.profiles
for select
to authenticated
using (auth.uid() = id);

create policy "Users can insert own profile"
on public.profiles
for insert
to authenticated
with check (auth.uid() = id);

create policy "Users can update own profile"
on public.profiles
for update
to authenticated
using (auth.uid() = id)
with check (auth.uid() = id);