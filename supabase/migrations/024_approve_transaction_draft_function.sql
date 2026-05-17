-- ============================================================
-- ALIYDA DB SETUP - BLOCK 24
-- Approve PDF draft and convert it into a confirmed transaction
-- ============================================================

create or replace function public.approve_transaction_draft(
  p_draft_id uuid,
  p_transaction_date date,
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
  v_user_id uuid;
  v_draft record;
  v_transaction_id uuid;
  v_month text;
begin
  v_user_id := auth.uid();

  if v_user_id is null then
    raise exception 'Not authenticated';
  end if;

  select *
  into v_draft
  from public.transaction_drafts
  where id = p_draft_id
    and user_id = v_user_id
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
    v_user_id,
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
    and user_id = v_user_id;

  return v_transaction_id;
end;
$$;

grant execute on function public.approve_transaction_draft(
  uuid,
  date,
  time,
  text,
  numeric,
  text,
  text,
  text,
  text
) to authenticated;