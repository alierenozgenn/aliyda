-- ============================================================
-- ALIYDA DB SETUP - BLOCK 16
-- Confirmed transactions view
-- ============================================================

create or replace view public.v_confirmed_transactions as
select
  t.id,
  t.user_id,
  t.account_id,
  a.name as account_name,
  a.institution_name,
  t.statement_id,
  s.month as statement_month,
  t.month,
  t.transaction_date,
  t.transaction_time,
  t.description,
  t.amount,
  t.currency,
  t.direction,
  t.category,
  t.subcategory,
  t.counterparty,
  t.source,
  t.is_recurring,
  t.is_excluded_from_budget,
  t.created_at,
  t.updated_at
from public.transactions t
left join public.accounts a on a.id = t.account_id
left join public.statements s on s.id = t.statement_id
where
  t.is_user_confirmed = true
  and t.is_deleted = false;

grant select on public.v_confirmed_transactions to authenticated;
grant select on public.v_confirmed_transactions to service_role;