-- ============================================================
-- ALIYDA DB SETUP - BLOCK 19
-- Recalculate monthly summary for current authenticated user
-- ============================================================

create or replace function public.recalculate_monthly_summary(
  p_month text
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_user_id uuid;
  v_summary_id uuid;

  v_detected_income numeric(14,2) := 0;
  v_declared_income numeric(14,2) := 0;
  v_total_income numeric(14,2) := 0;
  v_total_expense numeric(14,2) := 0;
  v_total_transfer_in numeric(14,2) := 0;
  v_total_transfer_out numeric(14,2) := 0;
  v_net_balance numeric(14,2) := 0;

  v_transaction_count integer := 0;
  v_income_count integer := 0;
  v_expense_count integer := 0;

  v_income_basis text := 'none';

  v_top_categories jsonb := '[]'::jsonb;
  v_largest_transactions jsonb := '[]'::jsonb;
begin
  v_user_id := auth.uid();

  if v_user_id is null then
    raise exception 'Not authenticated';
  end if;

  if p_month !~ '^[0-9]{4}-[0-9]{2}$' then
    raise exception 'Invalid month format. Expected YYYY-MM';
  end if;

  -- Income detected from confirmed transactions
  select coalesce(sum(amount), 0), count(*)
  into v_detected_income, v_income_count
  from public.transactions
  where user_id = v_user_id
    and month = p_month
    and direction = 'income'
    and is_user_confirmed = true
    and is_deleted = false
    and is_excluded_from_budget = false;

  -- Declared/manual income from monthly profile
  select coalesce(declared_income, 0)
  into v_declared_income
  from public.monthly_profiles
  where user_id = v_user_id
    and month = p_month;

  v_declared_income := coalesce(v_declared_income, 0);

  -- Expense total
  select coalesce(sum(amount), 0), count(*)
  into v_total_expense, v_expense_count
  from public.transactions
  where user_id = v_user_id
    and month = p_month
    and direction = 'expense'
    and is_user_confirmed = true
    and is_deleted = false
    and is_excluded_from_budget = false;

  -- Transfers
  select coalesce(sum(amount), 0)
  into v_total_transfer_in
  from public.transactions
  where user_id = v_user_id
    and month = p_month
    and direction = 'transfer_in'
    and is_user_confirmed = true
    and is_deleted = false;

  select coalesce(sum(amount), 0)
  into v_total_transfer_out
  from public.transactions
  where user_id = v_user_id
    and month = p_month
    and direction = 'transfer_out'
    and is_user_confirmed = true
    and is_deleted = false;

  -- Count all confirmed, not deleted transactions
  select count(*)
  into v_transaction_count
  from public.transactions
  where user_id = v_user_id
    and month = p_month
    and is_user_confirmed = true
    and is_deleted = false;

  -- Decide effective income
  if v_detected_income > 0 and v_declared_income > 0 then
    v_total_income := greatest(v_detected_income, v_declared_income);
    v_income_basis := 'mixed';
  elsif v_detected_income > 0 then
    v_total_income := v_detected_income;
    v_income_basis := 'pdf';
  elsif v_declared_income > 0 then
    v_total_income := v_declared_income;
    v_income_basis := 'manual';
  else
    v_total_income := 0;
    v_income_basis := 'none';
  end if;

  v_net_balance := v_total_income - v_total_expense;

  -- Top categories
  select coalesce(jsonb_agg(row_to_json(x)), '[]'::jsonb)
  into v_top_categories
  from (
    select
      coalesce(category, 'Diğer') as category,
      sum(amount) as amount,
      count(*) as transaction_count
    from public.transactions
    where user_id = v_user_id
      and month = p_month
      and direction = 'expense'
      and is_user_confirmed = true
      and is_deleted = false
      and is_excluded_from_budget = false
    group by coalesce(category, 'Diğer')
    order by sum(amount) desc
    limit 10
  ) x;

  -- Largest transactions
  select coalesce(jsonb_agg(row_to_json(x)), '[]'::jsonb)
  into v_largest_transactions
  from (
    select
      id,
      transaction_date,
      transaction_time,
      description,
      amount,
      direction,
      category,
      counterparty,
      source
    from public.transactions
    where user_id = v_user_id
      and month = p_month
      and is_user_confirmed = true
      and is_deleted = false
      and direction in ('expense', 'transfer_out')
    order by amount desc
    limit 10
  ) x;

  insert into public.monthly_summaries (
    user_id,
    month,
    detected_income,
    declared_income,
    income_basis,
    total_income,
    total_expense,
    total_transfer_in,
    total_transfer_out,
    net_balance,
    transaction_count,
    income_count,
    expense_count,
    top_categories,
    largest_transactions,
    recurring_candidates,
    is_stale,
    calculated_at
  )
  values (
    v_user_id,
    p_month,
    v_detected_income,
    v_declared_income,
    v_income_basis,
    v_total_income,
    v_total_expense,
    v_total_transfer_in,
    v_total_transfer_out,
    v_net_balance,
    v_transaction_count,
    v_income_count,
    v_expense_count,
    v_top_categories,
    v_largest_transactions,
    '[]'::jsonb,
    false,
    now()
  )
  on conflict (user_id, month)
  do update set
    detected_income = excluded.detected_income,
    declared_income = excluded.declared_income,
    income_basis = excluded.income_basis,
    total_income = excluded.total_income,
    total_expense = excluded.total_expense,
    total_transfer_in = excluded.total_transfer_in,
    total_transfer_out = excluded.total_transfer_out,
    net_balance = excluded.net_balance,
    transaction_count = excluded.transaction_count,
    income_count = excluded.income_count,
    expense_count = excluded.expense_count,
    top_categories = excluded.top_categories,
    largest_transactions = excluded.largest_transactions,
    recurring_candidates = excluded.recurring_candidates,
    is_stale = false,
    calculated_at = now(),
    updated_at = now()
  returning id into v_summary_id;

  -- Existing AI comments are now stale because numbers may have changed.
  update public.ai_insights
  set is_stale = true
  where user_id = v_user_id
    and month = p_month;

  return v_summary_id;
end;
$$;

grant execute on function public.recalculate_monthly_summary(text) to authenticated;