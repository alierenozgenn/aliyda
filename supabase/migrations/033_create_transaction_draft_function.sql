-- ============================================================
-- ALIYDA DB SETUP - BLOCK 33
-- Create transaction draft from PDF extraction
-- ============================================================

create or replace function public.create_transaction_draft(
  p_statement_id uuid,
  p_account_id uuid,
  p_month text,
  p_transaction_date date default null,
  p_transaction_time time default null,
  p_description text default null,
  p_original_description text default null,
  p_amount numeric default null,
  p_direction text default 'unknown',
  p_category text default null,
  p_subcategory text default null,
  p_counterparty text default null,
  p_confidence numeric default null,
  p_raw_item jsonb default '{}'::jsonb
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_user_id uuid;
  v_draft_id uuid;
begin
  v_user_id := auth.uid();

  if v_user_id is null then
    raise exception 'Not authenticated';
  end if;

  if p_month is not null and p_month !~ '^[0-9]{4}-[0-9]{2}$' then
    raise exception 'Invalid month format. Expected YYYY-MM';
  end if;

  if p_amount is not null and p_amount < 0 then
    raise exception 'Amount cannot be negative';
  end if;

  if p_direction is not null and p_direction not in (
    'income',
    'expense',
    'transfer_in',
    'transfer_out',
    'transfer',
    'unknown'
  ) then
    raise exception 'Invalid direction';
  end if;

  if p_confidence is not null and (p_confidence < 0 or p_confidence > 1) then
    raise exception 'Confidence must be between 0 and 1';
  end if;

  perform 1
  from public.statements
  where id = p_statement_id
    and user_id = v_user_id
    and is_deleted = false;

  if not found then
    raise exception 'Statement not found';
  end if;

  if p_account_id is not null then
    perform 1
    from public.accounts
    where id = p_account_id
      and user_id = v_user_id
      and is_active = true;

    if not found then
      raise exception 'Account not found';
    end if;
  end if;

  insert into public.transaction_drafts (
    user_id,
    statement_id,
    account_id,
    month,
    transaction_date,
    transaction_time,
    description,
    original_description,
    amount,
    direction,
    category,
    subcategory,
    counterparty,
    confidence,
    needs_review,
    review_status,
    raw_item
  )
  values (
    v_user_id,
    p_statement_id,
    p_account_id,
    p_month,
    p_transaction_date,
    p_transaction_time,
    nullif(p_description, ''),
    nullif(p_original_description, ''),
    p_amount,
    coalesce(p_direction, 'unknown'),
    nullif(p_category, ''),
    nullif(p_subcategory, ''),
    nullif(p_counterparty, ''),
    p_confidence,
    true,
    'pending',
    coalesce(p_raw_item, '{}'::jsonb)
  )
  returning id into v_draft_id;

  return v_draft_id;
end;
$$;

grant execute on function public.create_transaction_draft(
  uuid,
  uuid,
  text,
  date,
  time,
  text,
  text,
  numeric,
  text,
  text,
  text,
  text,
  numeric,
  jsonb
) to authenticated;