-- ============================================================
-- ALIYDA DB TEST - BLOCK 36
-- Check confirmed transactions and pending drafts
-- ============================================================

select
  transaction_date,
  transaction_time,
  description,
  amount,
  direction,
  category,
  counterparty,
  source
from public.v_confirmed_transactions
where user_id = 'your-user-id-here'
order by transaction_date asc, transaction_time asc;


select
  transaction_date,
  transaction_time,
  description,
  amount,
  direction,
  category,
  counterparty,
  confidence,
  review_status
from public.v_pending_transaction_drafts
where user_id = 'your-user-id-here'
order by transaction_date asc;