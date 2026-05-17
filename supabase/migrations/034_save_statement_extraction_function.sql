-- ============================================================
-- ALIYDA DB SETUP - BLOCK 34
-- Save Gemini statement extraction metadata/output
-- ============================================================

create or replace function public.save_statement_extraction(
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
  v_user_id uuid;
  v_extraction_id uuid;
begin
  v_user_id := auth.uid();

  if v_user_id is null then
    raise exception 'Not authenticated';
  end if;

  if p_status not in ('success', 'partial', 'failed') then
    raise exception 'Invalid extraction status';
  end if;

  perform 1
  from public.statements
  where id = p_statement_id
    and user_id = v_user_id
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
    v_user_id,
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