-- ============================================================
-- ALIYDA DB SETUP - BLOCK 28
-- Dashboard monthly overview view
-- ============================================================

drop view if exists public.v_monthly_dashboard;

create view public.v_monthly_dashboard
with (security_invoker = true)
as
select
  ms.user_id,
  ms.month,

  ms.detected_income,
  ms.declared_income,
  ms.income_basis,

  ms.total_income,
  ms.total_expense,
  ms.total_transfer_in,
  ms.total_transfer_out,
  ms.net_balance,

  ms.transaction_count,
  ms.income_count,
  ms.expense_count,

  ms.top_categories,
  ms.largest_transactions,
  ms.recurring_candidates,

  ms.is_stale,
  ms.calculated_at,

  mp.savings_goal,
  mp.budget_goal,
  mp.notes as monthly_notes,
  mp.is_finalized
from public.monthly_summaries ms
left join public.monthly_profiles mp
  on mp.user_id = ms.user_id
  and mp.month = ms.month;

grant select on public.v_monthly_dashboard to authenticated;
grant select on public.v_monthly_dashboard to service_role;