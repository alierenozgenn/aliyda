-- ============================================================
-- ALIYDA DB SETUP - BLOCK 035
-- Rewrite critical RPC functions to accept p_user_id parameter
-- so backend can call them with service role key (bypassing auth.uid())
-- ============================================================

-- 1. create_manual_transaction with p_user_id
create or replace function public.create_manual_transaction(
  p_user_id uuid,
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
  v_transaction_id uuid;
  v_month text;
begin
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
      and user_id = p_user_id
      and is_active = true;

    if not found then
      raise exception 'Account not found or does not belong to user';
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
    p_user_id,
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
  uuid, uuid, date, time, text, numeric, text, text, text, text, text, text
) to service_role;

grant execute on function public.create_manual_transaction(
  uuid, uuid, date, time, text, numeric, text, text, text, text, text, text
) to authenticated;


-- 2. approve_transaction_draft with p_user_id
create or replace function public.approve_transaction_draft(
  p_user_id uuid,
  p_draft_id uuid,
  p_transaction_date date default null,
  p_transaction_time time default null,
  p_description text default null,
  p_amount numeric default null,
  p_direction text default null,
  p_category text default null,
  p_subcategory text default null,
  p_counterparty text default null
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_draft record;
  v_transaction_id uuid;
  v_month text;
begin
  select *
  into v_draft
  from public.transaction_drafts
  where id = p_draft_id
    and user_id = p_user_id
    and review_status = 'pending';

  if not found then
    raise exception 'Draft not found or already reviewed';
  end if;

  if p_transaction_date is null and v_draft.transaction_date is null then
    raise exception 'Transaction date is required';
  end if;

  if coalesce(p_amount, v_draft.amount) is null or coalesce(p_amount, v_draft.amount) < 0 then
    raise exception 'Valid amount is required';
  end if;

  if coalesce(p_direction, v_draft.direction) not in ('income', 'expense', 'transfer_in', 'transfer_out', 'transfer') then
    raise exception 'Valid direction is required';
  end if;

  v_month := coalesce(
    v_draft.month,
    to_char(coalesce(p_transaction_date, v_draft.transaction_date), 'YYYY-MM')
  );

  insert into public.transactions (
    user_id,
    account_id,
    statement_id,
    draft_id,
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
    source,
    is_user_confirmed,
    metadata
  )
  values (
    p_user_id,
    v_draft.account_id,
    v_draft.statement_id,
    v_draft.id,
    v_month,
    coalesce(p_transaction_date, v_draft.transaction_date),
    coalesce(p_transaction_time, v_draft.transaction_time),
    coalesce(nullif(p_description, ''), v_draft.description, 'İsimsiz işlem'),
    coalesce(p_amount, v_draft.amount),
    coalesce(v_draft.currency, 'TRY'),
    coalesce(p_direction, v_draft.direction),
    coalesce(nullif(p_category, ''), v_draft.category),
    coalesce(nullif(p_subcategory, ''), v_draft.subcategory),
    coalesce(nullif(p_counterparty, ''), v_draft.counterparty),
    'pdf',
    true,
    jsonb_build_object(
      'approved_from_draft', true,
      'draft_confidence', v_draft.confidence,
      'original_description', v_draft.original_description
    )
  )
  returning id into v_transaction_id;

  update public.transaction_drafts
  set
    review_status = case
      when
        p_description is distinct from null
        or p_amount is distinct from null
        or p_direction is distinct from null
        or p_category is distinct from null
        or p_subcategory is distinct from null
        or p_counterparty is distinct from null
      then 'edited'
      else 'approved'
    end,
    needs_review = false,
    updated_at = now()
  where id = p_draft_id
    and user_id = p_user_id;

  return v_transaction_id;
end;
$$;

grant execute on function public.approve_transaction_draft(
  uuid, uuid, date, time, text, numeric, text, text, text, text
) to service_role;

grant execute on function public.approve_transaction_draft(
  uuid, uuid, date, time, text, numeric, text, text, text, text
) to authenticated;


-- 3. reject_transaction_draft with p_user_id
create or replace function public.reject_transaction_draft(
  p_user_id uuid,
  p_draft_id uuid,
  p_reason text default null
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.transaction_drafts
  set
    review_status = 'rejected',
    rejection_reason = p_reason,
    needs_review = false,
    updated_at = now()
  where id = p_draft_id
    and user_id = p_user_id
    and review_status = 'pending';

  if not found then
    raise exception 'Draft not found or already reviewed';
  end if;
end;
$$;

grant execute on function public.reject_transaction_draft(uuid, uuid, text) to service_role;
grant execute on function public.reject_transaction_draft(uuid, uuid, text) to authenticated;


-- 4. soft_delete_transaction with p_user_id
create or replace function public.soft_delete_transaction(
  p_user_id uuid,
  p_transaction_id uuid,
  p_reason text default 'User deleted'
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.transactions
  set
    is_deleted = true,
    deleted_at = now(),
    deleted_reason = p_reason,
    updated_at = now()
  where id = p_transaction_id
    and user_id = p_user_id
    and is_deleted = false;

  if not found then
    raise exception 'Transaction not found';
  end if;
end;
$$;

grant execute on function public.soft_delete_transaction(uuid, uuid, text) to service_role;
grant execute on function public.soft_delete_transaction(uuid, uuid, text) to authenticated;


-- 5. restore_transaction with p_user_id
create or replace function public.restore_transaction(
  p_user_id uuid,
  p_transaction_id uuid
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.transactions
  set
    is_deleted = false,
    deleted_at = null,
    deleted_reason = null,
    updated_at = now()
  where id = p_transaction_id
    and user_id = p_user_id
    and is_deleted = true;

  if not found then
    raise exception 'Transaction not found or not deleted';
  end if;
end;
$$;

grant execute on function public.restore_transaction(uuid, uuid) to service_role;
grant execute on function public.restore_transaction(uuid, uuid) to authenticated;


-- 6. recalculate_monthly_summary with p_user_id
-- (the existing one uses auth.uid() too, override it)
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
  v_total_income numeric := 0;
  v_total_expense numeric := 0;
  v_net_balance numeric := 0;
  v_transaction_count int := 0;
  v_top_categories jsonb := '[]'::jsonb;
  v_largest_transactions jsonb := '[]'::jsonb;
  v_declared_income numeric;
  v_detected_income numeric;
  v_income_basis text;
  v_profile record;
begin
  -- Aggregate from confirmed non-deleted transactions
  select
    coalesce(sum(case when direction = 'income' then amount else 0 end), 0),
    coalesce(sum(case when direction in ('expense','transfer_out','transfer') then amount else 0 end), 0),
    count(*)
  into v_total_income, v_total_expense, v_transaction_count
  from public.transactions
  where user_id = p_user_id
    and month = p_month
    and is_user_confirmed = true
    and is_deleted = false
    and is_excluded_from_budget = false;

  v_net_balance := v_total_income - v_total_expense;

  -- Top categories by expense
  select jsonb_agg(row_to_json(cat) order by cat.total desc)
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

  -- Largest transactions (top 10 by amount)
  select jsonb_agg(row_to_json(tx) order by tx.amount desc)
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
    order by amount desc
    limit 10
  ) tx;

  -- Monthly profile (for declared income)
  select * into v_profile
  from public.monthly_profiles
  where user_id = p_user_id and month = p_month;

  v_declared_income := v_profile.declared_income;
  v_detected_income := v_total_income;

  if v_declared_income is not null and v_declared_income > 0 then
    v_income_basis := 'declared';
    v_net_balance := v_declared_income - v_total_expense;
  elsif v_total_income > 0 then
    v_income_basis := 'detected';
  else
    v_income_basis := 'none';
  end if;

  -- Upsert monthly_summaries
  insert into public.monthly_summaries (
    user_id, month,
    total_income, total_expense, net_balance,
    transaction_count, top_categories, largest_transactions,
    declared_income, detected_income, income_basis,
    is_stale, updated_at
  )
  values (
    p_user_id, p_month,
    v_total_income, v_total_expense, v_net_balance,
    v_transaction_count, coalesce(v_top_categories, '[]'::jsonb), coalesce(v_largest_transactions, '[]'::jsonb),
    v_declared_income, v_detected_income, v_income_basis,
    false, now()
  )
  on conflict (user_id, month) do update set
    total_income = excluded.total_income,
    total_expense = excluded.total_expense,
    net_balance = excluded.net_balance,
    transaction_count = excluded.transaction_count,
    top_categories = excluded.top_categories,
    largest_transactions = excluded.largest_transactions,
    declared_income = excluded.declared_income,
    detected_income = excluded.detected_income,
    income_basis = excluded.income_basis,
    is_stale = false,
    updated_at = now();
end;
$$;

grant execute on function public.recalculate_monthly_summary(uuid, text) to service_role;
grant execute on function public.recalculate_monthly_summary(uuid, text) to authenticated;
