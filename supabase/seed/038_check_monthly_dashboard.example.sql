-- ============================================================
-- ALIYDA DB TEST - BLOCK 38
-- Check dashboard monthly overview
-- ============================================================

select
  month,
  detected_income,
  declared_income,
  income_basis,
  total_income,
  total_expense,
  net_balance,
  transaction_count,
  income_count,
  expense_count,
  top_categories,
  largest_transactions,
  savings_goal,
  budget_goal,
  is_stale,
  calculated_at
from public.v_monthly_dashboard
where user_id = 'your-user-id-here'
  and month = '2026-05';