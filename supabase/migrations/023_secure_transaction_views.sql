-- ============================================================
-- ALIYDA DB SETUP - BLOCK 23
-- Secure views for confirmed transactions and pending drafts
-- ============================================================

drop view if exists public.v_confirmed_transactions;
drop view if exists public.v_pending_transaction_drafts;

create view public.v_confirmed_transactions
with (security_invoker = true)
as
select
  t.id,
  t.user_id,
  t.account_id,
  a.name as account_name,
  a.institution_name,
  a.account_type,
  t.statement_id,
  s.file_name as statement_file_name,
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
  t.payment_method,
  t.location,
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

create view public.v_pending_transaction_drafts
with (security_invoker = true)
as
select
  d.id,
  d.user_id,
  d.statement_id,
  s.file_name as statement_file_name,
  s.month as statement_month,
  d.account_id,
  a.name as account_name,
  a.institution_name,
  d.month,
  d.transaction_date,
  d.transaction_time,
  d.description,
  d.original_description,
  d.amount,
  d.currency,
  d.direction,
  d.category,
  d.subcategory,
  d.counterparty,
  d.confidence,
  d.needs_review,
  d.review_status,
  d.user_notes,
  d.created_at,
  d.updated_at
from public.transaction_drafts d
left join public.statements s on s.id = d.statement_id
left join public.accounts a on a.id = d.account_id
where
  d.review_status = 'pending';

grant select on public.v_confirmed_transactions to authenticated;
grant select on public.v_pending_transaction_drafts to authenticated;
grant select on public.v_confirmed_transactions to service_role;
grant select on public.v_pending_transaction_drafts to service_role;