-- ============================================================
-- ALIYDA DB SETUP - BLOCK 036
-- Service-role safe PDF extraction/draft RPC overloads.
-- Backend passes p_user_id explicitly because auth.uid() is null
-- when using the Supabase service role key.
-- ============================================================

create or replace function public.save_statement_extraction(
  p_user_id uuid,
  p_statement_id uuid,
  p_provider text default 'gemini',
  p_model text default null,
  p_prompt_version text default null,
  p_raw_output jsonb default null,
  p_parsed_output jsonb default null,
  p_request_count integer default 1,
  p_input_token_estimate integer default null,
  p_output_token_estimate integer default null,
  p_status text default 'success',
  p_error_message text default null
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_extraction_id uuid;
begin
  if p_user_id is null then
    raise exception 'User id is required';
  end if;

  if p_status not in ('success', 'partial', 'failed') then
    raise exception 'Invalid extraction status';
  end if;

  perform 1
  from public.statements
  where id = p_statement_id
    and user_id = p_user_id
    and is_deleted = false;

  if not found then
    raise exception 'Statement not found';
  end if;

  insert into public.statement_extractions (
    user_id,
    statement_id,
    provider,
    model,
    prompt_version,
    raw_output,
    parsed_output,
    request_count,
    input_token_estimate,
    output_token_estimate,
    status,
    error_message
  )
  values (
    p_user_id,
    p_statement_id,
    coalesce(nullif(p_provider, ''), 'gemini'),
    nullif(p_model, ''),
    nullif(p_prompt_version, ''),
    p_raw_output,
    p_parsed_output,
    coalesce(p_request_count, 1),
    p_input_token_estimate,
    p_output_token_estimate,
    p_status,
    p_error_message
  )
  returning id into v_extraction_id;

  return v_extraction_id;
end;
$$;

grant execute on function public.save_statement_extraction(
  uuid,
  uuid,
  text,
  text,
  text,
  jsonb,
  jsonb,
  integer,
  integer,
  integer,
  text,
  text
) to service_role;

grant execute on function public.save_statement_extraction(
  uuid,
  uuid,
  text,
  text,
  text,
  jsonb,
  jsonb,
  integer,
  integer,
  integer,
  text,
  text
) to authenticated;


create or replace function public.create_transaction_draft(
  p_user_id uuid,
  p_account_id uuid default null,
  p_statement_id uuid default null,
  p_month text default null,
  p_transaction_date date default null,
  p_transaction_time time default null,
  p_description text default null,
  p_original_description text default null,
  p_amount numeric default null,
  p_currency text default 'TRY',
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
  v_draft_id uuid;
begin
  if p_user_id is null then
    raise exception 'User id is required';
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

  if p_statement_id is not null then
    perform 1
    from public.statements
    where id = p_statement_id
      and user_id = p_user_id
      and is_deleted = false;

    if not found then
      raise exception 'Statement not found';
    end if;
  end if;

  if p_account_id is not null then
    perform 1
    from public.accounts
    where id = p_account_id
      and user_id = p_user_id
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
    currency,
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
    p_user_id,
    p_statement_id,
    p_account_id,
    p_month,
    p_transaction_date,
    p_transaction_time,
    nullif(p_description, ''),
    nullif(p_original_description, ''),
    p_amount,
    coalesce(nullif(p_currency, ''), 'TRY'),
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
  text,
  numeric,
  jsonb
) to service_role;

grant execute on function public.create_transaction_draft(
  uuid,
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
  text,
  numeric,
  jsonb
) to authenticated;
