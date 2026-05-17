-- ============================================================
-- ALIYDA DB SETUP - BLOCK 30
-- Upsert monthly profile / declared income / goals
-- ============================================================

create or replace function public.upsert_monthly_profile(
  p_month text,
  p_declared_income numeric default null,
  p_income_source text default 'manual',
  p_savings_goal numeric default null,
  p_budget_goal numeric default null,
  p_notes text default null,
  p_is_finalized boolean default false
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_user_id uuid;
  v_profile_id uuid;
begin
  v_user_id := auth.uid();

  if v_user_id is null then
    raise exception 'Not authenticated';
  end if;

  if p_month !~ '^[0-9]{4}-[0-9]{2}$' then
    raise exception 'Invalid month format. Expected YYYY-MM';
  end if;

  if p_declared_income is not null and p_declared_income < 0 then
    raise exception 'Declared income cannot be negative';
  end if;

  if p_savings_goal is not null and p_savings_goal < 0 then
    raise exception 'Savings goal cannot be negative';
  end if;

  if p_budget_goal is not null and p_budget_goal < 0 then
    raise exception 'Budget goal cannot be negative';
  end if;

  if p_income_source not in ('manual', 'pdf', 'mixed', 'unknown') then
    raise exception 'Invalid income source';
  end if;

  insert into public.monthly_profiles (
    user_id,
    month,
    declared_income,
    income_source,
    savings_goal,
    budget_goal,
    notes,
    is_finalized
  )
  values (
    v_user_id,
    p_month,
    p_declared_income,
    p_income_source,
    p_savings_goal,
    p_budget_goal,
    nullif(p_notes, ''),
    p_is_finalized
  )
  on conflict (user_id, month)
  do update set
    declared_income = excluded.declared_income,
    income_source = excluded.income_source,
    savings_goal = excluded.savings_goal,
    budget_goal = excluded.budget_goal,
    notes = excluded.notes,
    is_finalized = excluded.is_finalized,
    updated_at = now()
  returning id into v_profile_id;

  return v_profile_id;
end;
$$;

grant execute on function public.upsert_monthly_profile(
  text,
  numeric,
  text,
  numeric,
  numeric,
  text,
  boolean
) to authenticated;