-- ============================================================
-- ALIYDA DB SETUP - BLOCK 11
-- chat_sessions and chat_messages
-- ============================================================

create table public.chat_sessions (
  id uuid primary key default gen_random_uuid(),

  user_id uuid not null references auth.users(id) on delete cascade,

  month text check (month is null or month ~ '^[0-9]{4}-[0-9]{2}$'),
  title text,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger set_chat_sessions_updated_at
before update on public.chat_sessions
for each row
execute function public.set_updated_at();

create index idx_chat_sessions_user_id
on public.chat_sessions(user_id);

create index idx_chat_sessions_user_updated
on public.chat_sessions(user_id, updated_at desc);


create table public.chat_messages (
  id uuid primary key default gen_random_uuid(),

  user_id uuid not null references auth.users(id) on delete cascade,
  session_id uuid not null references public.chat_sessions(id) on delete cascade,

  role text not null check (role in ('user', 'assistant', 'system')),
  content text not null,

  context_snapshot jsonb,
  provider text,
  model text,

  created_at timestamptz not null default now()
);

create index idx_chat_messages_user_id
on public.chat_messages(user_id);

create index idx_chat_messages_session_id
on public.chat_messages(session_id);

create index idx_chat_messages_created_at
on public.chat_messages(session_id, created_at);