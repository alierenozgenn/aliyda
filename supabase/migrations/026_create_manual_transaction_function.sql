-- ============================================================
-- ALIYDA DB SETUP - BLOCK 26
-- Create manual transaction
-- ============================================================

create or replace function public.create_manual_transaction(
  p_account_id uuid,
  p_transaction_date date,
  p_transaction_time time default null,
  p_description text default null,
  p_amount numeric default null,
  p_direction text default null,
  p_category text default null,
  p_subcategory text default null,
  p_counterparty text default null,
  p_payment_method text default null,
  p_location text default null
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_user_id uuid;
  v_transaction_id uuid;
  v_month text;
begin
  v_user_id := auth.uid();

  if v_user_id is null then
    raise exception 'Not authenticated';
  end if;

  if p_transaction_date is null then
    raise exception 'Transaction date is required';
  end if;

  if p_amount is null or p_amount < 0 then
    raise exception 'Valid amount is required';
  end if;

  if p_direction not in ('income', 'expense', 'transfer_in', 'transfer_out', 'transfer') then
    raise exception 'Valid direction is required';
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

  v_month := to_char(p_transaction_date, 'YYYY-MM');

  insert into public.transactions (
    user_id,
    account_id,
    month,
    transaction_date,
    transaction_time,
    description,
    amount,
    currency,
    direction,
    category,
    subcategory,
    counterparty,
    payment_method,
    location,
    source,
    is_user_confirmed
  )
  values (
    v_user_id,
    p_account_id,
    v_month,
    p_transaction_date,
    p_transaction_time,
    coalesce(nullif(p_description, ''), 'Manuel işlem'),
    p_amount,
    'TRY',
    p_direction,
    nullif(p_category, ''),
    nullif(p_subcategory, ''),
    nullif(p_counterparty, ''),
    nullif(p_payment_method, ''),
    nullif(p_location, ''),
    'manual',
    true
  )
  returning id into v_transaction_id;

  return v_transaction_id;
end;
$$;

grant execute on function public.create_manual_transaction(
  uuid,
  date,
  time,
  text,
  numeric,
  text,
  text,
  text,
  text,
  text,
  text
) to authenticated;