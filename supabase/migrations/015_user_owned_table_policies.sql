-- ============================================================
-- ALIYDA DB SETUP - BLOCK 15
-- Main RLS policies for user-owned tables
-- ============================================================

create policy "Users can manage own accounts"
on public.accounts
for all
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can manage own statements"
on public.statements
for all
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can manage own statement extractions"
on public.statement_extractions
for all
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can manage own transaction drafts"
on public.transaction_drafts
for all
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can manage own transactions"
on public.transactions
for all
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can manage own monthly profiles"
on public.monthly_profiles
for all
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can manage own monthly summaries"
on public.monthly_summaries
for all
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can manage own ai insights"
on public.ai_insights
for all
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can manage own chat sessions"
on public.chat_sessions
for all
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can manage own chat messages"
on public.chat_messages
for all
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can manage own category rules"
on public.category_rules
for all
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);