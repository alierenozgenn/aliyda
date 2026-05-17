-- ============================================================
-- ALIYDA DB SETUP - BLOCK 17
-- Soft delete helper functions
-- ============================================================

create or replace function public.soft_delete_transaction(
  p_transaction_id uuid,
  p_deleted_reason text default null
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
    deleted_reason = p_deleted_reason,
    updated_at = now()
  where
    id = p_transaction_id
    and user_id = auth.uid();
end;
$$;

create or replace function public.restore_transaction(
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
  where
    id = p_transaction_id
    and user_id = auth.uid();
end;
$$;

create or replace function public.soft_delete_statement(
  p_statement_id uuid,
  p_deleted_reason text default null
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.statements
  set
    is_deleted = true,
    deleted_at = now(),
    deleted_reason = p_deleted_reason,
    status = 'deleted',
    updated_at = now()
  where
    id = p_statement_id
    and user_id = auth.uid();

  update public.transaction_drafts
  set
    review_status = 'rejected',
    updated_at = now()
  where
    statement_id = p_statement_id
    and user_id = auth.uid();

  update public.transactions
  set
    is_deleted = true,
    deleted_at = now(),
    deleted_reason = coalesce(p_deleted_reason, 'Statement deleted'),
    updated_at = now()
  where
    statement_id = p_statement_id
    and user_id = auth.uid();
end;
$$;

grant execute on function public.soft_delete_transaction(uuid, text) to authenticated;
grant execute on function public.restore_transaction(uuid) to authenticated;
grant execute on function public.soft_delete_statement(uuid, text) to authenticated;