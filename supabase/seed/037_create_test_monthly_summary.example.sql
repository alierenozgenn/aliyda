-- ============================================================
-- ALIYDA DB TEST - BLOCK 37
-- Manually create monthly summary for SQL Editor test
-- ============================================================

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
select
  'your-user-id-here'::uuid as user_id,
  '2026-05' as month,

  coalesce(sum(amount) filter (where direction = 'income'), 0) as detected_income,

  coalesce((
    select declared_income
    from public.monthly_profiles mp
    where mp.user_id = 'your-user-id-here'
      and mp.month = '2026-05'
  ), 0) as declared_income,

  'mixed' as income_basis,

  greatest(
    coalesce(sum(amount) filter (where direction = 'income'), 0),
    coalesce((
      select declared_income
      from public.monthly_profiles mp
      where mp.user_id = 'your-user-id-here'
        and mp.month = '2026-05'
    ), 0)
  ) as total_income,

  coalesce(sum(amount) filter (where direction = 'expense'), 0) as total_expense,
  coalesce(sum(amount) filter (where direction = 'transfer_in'), 0) as total_transfer_in,
  coalesce(sum(amount) filter (where direction = 'transfer_out'), 0) as total_transfer_out,

  greatest(
    coalesce(sum(amount) filter (where direction = 'income'), 0),
    coalesce((
      select declared_income
      from public.monthly_profiles mp
      where mp.user_id = 'your-user-id-here'
        and mp.month = '2026-05'
    ), 0)
  ) - coalesce(sum(amount) filter (where direction = 'expense'), 0) as net_balance,

  count(*) as transaction_count,
  count(*) filter (where direction = 'income') as income_count,
  count(*) filter (where direction = 'expense') as expense_count,

  (
    select coalesce(jsonb_agg(row_to_json(x)), '[]'::jsonb)
    from (
      select
        coalesce(category, 'Diğer') as category,
        sum(amount) as amount,
        count(*) as transaction_count
      from public.transactions
      where user_id = 'your-user-id-here'
        and month = '2026-05'
        and direction = 'expense'
        and is_deleted = false
        and is_user_confirmed = true
      group by coalesce(category, 'Diğer')
      order by sum(amount) desc
      limit 10
    ) x
  ) as top_categories,

  (
    select coalesce(jsonb_agg(row_to_json(x)), '[]'::jsonb)
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
      where user_id = 'your-user-id-here'
        and month = '2026-05'
        and direction in ('expense', 'transfer_out')
        and is_deleted = false
        and is_user_confirmed = true
      order by amount desc
      limit 10
    ) x
  ) as largest_transactions,

  '[]'::jsonb as recurring_candidates,
  false as is_stale,
  now() as calculated_at

from public.transactions
where user_id = 'your-user-id-here'
  and month = '2026-05'
  and is_deleted = false
  and is_user_confirmed = true

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
  updated_at = now();