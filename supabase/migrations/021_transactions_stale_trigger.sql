-- ============================================================
-- ALIYDA DB SETUP - BLOCK 21
-- Trigger: mark monthly summary stale when transactions change
-- ============================================================

create or replace function public.handle_transaction_summary_stale()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if tg_op = 'DELETE' then
    perform public.mark_month_as_stale(old.user_id, old.month);
    return old;
  end if;

  perform public.mark_month_as_stale(new.user_id, new.month);

  if tg_op = 'UPDATE' and old.month is distinct from new.month then
    perform public.mark_month_as_stale(old.user_id, old.month);
  end if;

  return new;
end;
$$;

create trigger transactions_mark_summary_stale
after insert or update or delete on public.transactions
for each row
execute function public.handle_transaction_summary_stale();