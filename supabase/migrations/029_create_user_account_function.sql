-- ============================================================
-- ALIYDA DB SETUP - BLOCK 29
-- Create account helper
-- ============================================================

create or replace function public.create_user_account(
  p_name text,
  p_institution_name text default null,
  p_account_type text default 'bank',
  p_currency text default 'TRY'
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_user_id uuid;
  v_account_id uuid;
begin
  v_user_id := auth.uid();

  if v_user_id is null then
    raise exception 'Not authenticated';
  end if;

  if p_name is null or length(trim(p_name)) = 0 then
    raise exception 'Account name is required';
  end if;

  if p_account_type not in ('bank', 'credit_card', 'cash', 'manual', 'wallet', 'other') then
    raise exception 'Invalid account type';
  end if;

  insert into public.accounts (
    user_id,
    name,
    institution_name,
    account_type,
    currency,
    is_active
  )
  values (
    v_user_id,
    trim(p_name),
    nullif(trim(coalesce(p_institution_name, '')), ''),
    p_account_type,
    coalesce(nullif(trim(p_currency), ''), 'TRY'),
    true
  )
  on conflict (user_id, name)
  do update set
    institution_name = excluded.institution_name,
    account_type = excluded.account_type,
    currency = excluded.currency,
    is_active = true,
    updated_at = now()
  returning id into v_account_id;

  return v_account_id;
end;
$$;

grant execute on function public.create_user_account(text, text, text, text) to authenticated;