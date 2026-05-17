-- ============================================================
-- ALIYDA DB SETUP - BLOCK 25
-- Reject PDF draft transaction
-- ============================================================

create or replace function public.reject_transaction_draft(
  p_draft_id uuid,
  p_reason text default null
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

  update public.transaction_drafts
  set
    review_status = 'rejected',
    needs_review = false,
    user_notes = p_reason,
    updated_at = now()
  where id = p_draft_id
    and user_id = v_user_id
    and review_status = 'pending';

  if not found then
    raise exception 'Draft not found or already reviewed';
  end if;
end;
$$;

grant execute on function public.reject_transaction_draft(uuid, text) to authenticated;