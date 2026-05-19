-- ============================================================
-- Fix dashboard/monthly summary consistency.
--
-- total_income, total_expense and net_balance must be calculated
-- from the same confirmed transaction set. If a user declared income,
-- total_income uses the greater of declared income and detected inflow.
-- Outgoing transfers are counted in total_expense because they appear as
-- outgoing money in the user's transaction list and dashboard.
-- ============================================================

create or replace function public.recalculate_monthly_summary(
  p_user_id uuid,
  p_month text
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_detected_income numeric(14,2) := 0;
  v_declared_income numeric(14,2) := 0;
  v_total_income numeric(14,2) := 0;
  v_total_expense numeric(14,2) := 0;
  v_total_transfer_in numeric(14,2) := 0;
  v_total_transfer_out numeric(14,2) := 0;
  v_net_balance numeric(14,2) := 0;
  v_transaction_count int := 0;
  v_income_count int := 0;
  v_expense_count int := 0;
  v_top_categories jsonb := '[]'::jsonb;
  v_largest_transactions jsonb := '[]'::jsonb;
  v_income_basis text := 'none';
begin
  select
    coalesce(sum(case when direction in ('income', 'transfer_in') then amount else 0 end), 0),
    coalesce(sum(case when direction in ('expense', 'transfer_out', 'transfer') then amount else 0 end), 0),
    coalesce(sum(case when direction = 'transfer_in' then amount else 0 end), 0),
    coalesce(sum(case when direction = 'transfer_out' then amount else 0 end), 0),
    count(*),
    count(*) filter (where direction in ('income', 'transfer_in')),
    count(*) filter (where direction in ('expense', 'transfer_out', 'transfer'))
  into
    v_detected_income,
    v_total_expense,
    v_total_transfer_in,
    v_total_transfer_out,
    v_transaction_count,
    v_income_count,
    v_expense_count
  from public.transactions
  where user_id = p_user_id
    and month = p_month
    and is_user_confirmed = true
    and is_deleted = false
    and is_excluded_from_budget = false;

  select coalesce(declared_income, 0)
  into v_declared_income
  from public.monthly_profiles
  where user_id = p_user_id
    and month = p_month;

  v_declared_income := coalesce(v_declared_income, 0);
  v_total_income := greatest(v_declared_income, v_detected_income);
  v_net_balance := v_total_income - v_total_expense;

  if v_declared_income > 0 and v_detected_income > 0 then
    v_income_basis := 'mixed';
  elsif v_declared_income > 0 then
    v_income_basis := 'manual';
  elsif v_detected_income > 0 then
    v_income_basis := 'pdf';
  else
    v_income_basis := 'none';
  end if;

  select coalesce(jsonb_agg(row_to_json(cat) order by cat.total desc), '[]'::jsonb)
  into v_top_categories
  from (
    select
      coalesce(category, 'Diğer') as category,
      sum(amount) as total
    from public.transactions
    where user_id = p_user_id
      and month = p_month
      and direction in ('expense', 'transfer_out', 'transfer')
      and is_user_confirmed = true
      and is_deleted = false
      and is_excluded_from_budget = false
    group by category
    order by total desc
    limit 10
  ) cat;

  select coalesce(jsonb_agg(row_to_json(tx) order by tx.amount desc), '[]'::jsonb)
  into v_largest_transactions
  from (
    select
      id,
      description,
      amount,
      direction,
      category,
      transaction_date::text
    from public.transactions
    where user_id = p_user_id
      and month = p_month
      and is_user_confirmed = true
      and is_deleted = false
      and is_excluded_from_budget = false
    order by amount desc
    limit 10
  ) tx;

  insert into public.monthly_summaries (
    user_id,
    month,
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
    detected_income,
    declared_income,
    income_basis,
    is_stale,
    calculated_at,
    updated_at
  )
  values (
    p_user_id,
    p_month,
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
    v_detected_income,
    v_declared_income,
    v_income_basis,
    false,
    now(),
    now()
  )
  on conflict (user_id, month) do update set
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
    detected_income = excluded.detected_income,
    declared_income = excluded.declared_income,
    income_basis = excluded.income_basis,
    is_stale = false,
    calculated_at = now(),
    updated_at = now();
end;
$$;

grant execute on function public.recalculate_monthly_summary(uuid, text) to service_role;
grant execute on function public.recalculate_monthly_summary(uuid, text) to authenticated;

update public.monthly_summaries
set is_stale = true,
    updated_at = now();
