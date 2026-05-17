-- ============================================================
-- ALIYDA DB SETUP - BLOCK 27
-- Update existing confirmed transaction
-- ============================================================

create or replace function public.update_transaction_details(
  p_transaction_id uuid,
  p_transaction_date date default null,
  p_transaction_time time default null,
  p_description text default null,
  p_amount numeric default null,
  p_direction text default null,
  p_category text default null,
  p_subcategory text default null,
  p_counterparty text default null,
  p_payment_method text default null,
  p_location text default null,
  p_is_excluded_from_budget boolean default null
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_user_id uuid;
  v_existing record;
  v_new_date date;
  v_new_month text;
begin
  v_user_id := auth.uid();

  if v_user_id is null then
    raise exception 'Not authenticated';
  end if;

  select *
  into v_existing
  from public.transactions
  where id = p_transaction_id
    and user_id = v_user_id
    and is_deleted = false;

  if not found then
    raise exception 'Transaction not found';
  end if;

  if p_amount is not null and p_amount < 0 then
    raise exception 'Amount cannot be negative';
  end if;

  if p_direction is not null and p_direction not in ('income', 'expense', 'transfer_in', 'transfer_out', 'transfer') then
    raise exception 'Invalid direction';
  end if;

  v_new_date := coalesce(p_transaction_date, v_existing.transaction_date);
  v_new_month := to_char(v_new_date, 'YYYY-MM');

  update public.transactions
  set
    transaction_date = v_new_date,
    transaction_time = coalesce(p_transaction_time, transaction_time),
    month = v_new_month,
    description = coalesce(nullif(p_description, ''), description),
    amount = coalesce(p_amount, amount),
    direction = coalesce(p_direction, direction),
    category = coalesce(nullif(p_category, ''), category),
    subcategory = coalesce(nullif(p_subcategory, ''), subcategory),
    counterparty = coalesce(nullif(p_counterparty, ''), counterparty),
    payment_method = coalesce(nullif(p_payment_method, ''), payment_method),
    location = coalesce(nullif(p_location, ''), location),
    is_excluded_from_budget = coalesce(p_is_excluded_from_budget, is_excluded_from_budget),
    updated_at = now()
  where id = p_transaction_id
    and user_id = v_user_id;
end;
$$;

grant execute on function public.update_transaction_details(
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
  text,
  boolean
) to authenticated;