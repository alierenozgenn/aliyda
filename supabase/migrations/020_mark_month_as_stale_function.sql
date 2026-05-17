-- ============================================================
-- ALIYDA DB SETUP - BLOCK 20
-- Mark monthly summary and AI insights as stale
-- ============================================================

create or replace function public.mark_month_as_stale(
  p_user_id uuid,
  p_month text
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_user_id is null or p_month is null then
    return;
  end if;

  insert into public.monthly_summaries (
    user_id,
    month,
    is_stale
  )
  values (
    p_user_id,
    p_month,
    true
  )
  on conflict (user_id, month)
  do update set
    is_stale = true,
    updated_at = now();

  update public.ai_insights
  set is_stale = true
  where user_id = p_user_id
    and month = p_month;
end;
$$;