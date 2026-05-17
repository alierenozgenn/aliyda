-- ============================================================
-- ALIYDA DB SETUP - BLOCK 31
-- Create statement record for uploaded PDF or manual batch
-- ============================================================

create or replace function public.create_statement(
  p_account_id uuid,
  p_month text,
  p_source text default 'pdf',
  p_file_name text default null,
  p_file_mime_type text default null,
  p_file_size_bytes bigint default null
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_user_id uuid;
  v_statement_id uuid;
begin
  v_user_id := auth.uid();

  if v_user_id is null then
    raise exception 'Not authenticated';
  end if;

  if p_month !~ '^[0-9]{4}-[0-9]{2}$' then
    raise exception 'Invalid month format. Expected YYYY-MM';
  end if;

  if p_source not in ('pdf', 'manual', 'import', 'demo') then
    raise exception 'Invalid statement source';
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

  insert into public.statements (
    user_id,
    account_id,
    month,
    source,
    file_name,
    file_mime_type,
    file_size_bytes,
    status
  )
  values (
    v_user_id,
    p_account_id,
    p_month,
    p_source,
    nullif(p_file_name, ''),
    nullif(p_file_mime_type, ''),
    p_file_size_bytes,
    'uploaded'
  )
  returning id into v_statement_id;

  return v_statement_id;
end;
$$;

grant execute on function public.create_statement(
  uuid,
  text,
  text,
  text,
  text,
  bigint
) to authenticated;