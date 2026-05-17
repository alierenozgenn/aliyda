-- ============================================================
-- ALIYDA DB SETUP - BLOCK 32
-- Update statement status
-- ============================================================

create or replace function public.update_statement_status(
  p_statement_id uuid,
  p_status text,
  p_extraction_confidence numeric default null,
  p_income_detected boolean default null,
  p_error_message text default null
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_user_id uuid;
begin
  v_user_id := auth.uid();

  if v_user_id is null then
    raise exception 'Not authenticated';
  end if;

  if p_status not in (
    'uploaded',
    'extracting',
    'extracted',
    'pending_review',
    'approved',
    'saved',
    'failed',
    'cancelled',
    'deleted'
  ) then
    raise exception 'Invalid statement status';
  end if;

  if p_extraction_confidence is not null
     and (p_extraction_confidence < 0 or p_extraction_confidence > 1) then
    raise exception 'Extraction confidence must be between 0 and 1';
  end if;

  update public.statements
  set
    status = p_status,
    extraction_confidence = coalesce(p_extraction_confidence, extraction_confidence),
    income_detected = coalesce(p_income_detected, income_detected),
    error_message = p_error_message,
    updated_at = now()
  where id = p_statement_id
    and user_id = v_user_id
    and is_deleted = false;

  if not found then
    raise exception 'Statement not found';
  end if;
end;
$$;

grant execute on function public.update_statement_status(
  uuid,
  text,
  numeric,
  boolean,
  text
) to authenticated;