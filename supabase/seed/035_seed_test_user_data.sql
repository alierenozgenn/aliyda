-- ============================================================
-- ALIYDA DB TEST - BLOCK 35
-- Insert test data for one auth user
-- Replace v_user_id with your real auth.users.id
-- ============================================================

do $$
declare
  v_user_id uuid := 'your-user-id-here';
  v_account_id uuid;
  v_statement_id uuid;
  v_draft_id uuid;
begin
  -- Ensure profile exists
  insert into public.profiles (
    id,
    email,
    full_name,
    preferred_currency,
    onboarding_completed
  )
  values (
    v_user_id,
    'test@aliyda.app',
    'Aliyda Test Kullanıcısı',
    'TRY',
    true
  )
  on conflict (id) do update set
    email = excluded.email,
    full_name = excluded.full_name,
    onboarding_completed = true,
    updated_at = now();

  -- Create account
  insert into public.accounts (
    user_id,
    name,
    institution_name,
    account_type,
    currency
  )
  values (
    v_user_id,
    'Manuel Test Hesabı',
    'Aliyda',
    'manual',
    'TRY'
  )
  on conflict (user_id, name)
  do update set
    institution_name = excluded.institution_name,
    account_type = excluded.account_type,
    currency = excluded.currency,
    is_active = true,
    updated_at = now()
  returning id into v_account_id;

  -- Create example PDF statement
  insert into public.statements (
    user_id,
    account_id,
    month,
    source,
    file_name,
    file_mime_type,
    file_size_bytes,
    status,
    income_detected
  )
  values (
    v_user_id,
    v_account_id,
    '2026-05',
    'pdf',
    'demo-ekstre.pdf',
    'application/pdf',
    123456,
    'pending_review',
    false
  )
  returning id into v_statement_id;

  -- Create one pending PDF draft
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
    direction,
    category,
    counterparty,
    confidence,
    needs_review,
    review_status,
    raw_item
  )
  values (
    v_user_id,
    v_statement_id,
    v_account_id,
    '2026-05',
    '2026-05-12',
    '14:35',
    'Migros Market Alışverişi',
    'MIGROS TICARET A.S.',
    845.90,
    'expense',
    'Market',
    'Migros',
    0.91,
    true,
    'pending',
    '{"source":"gemini_test","line":"MIGROS TICARET A.S. 845.90 TL"}'::jsonb
  )
  returning id into v_draft_id;

  -- User declared monthly income because PDF did not include income
  insert into public.monthly_profiles (
    user_id,
    month,
    declared_income,
    income_source,
    savings_goal,
    budget_goal,
    notes,
    is_finalized
  )
  values (
    v_user_id,
    '2026-05',
    25000,
    'manual',
    5000,
    18000,
    'PDF gelir içermediği için kullanıcı manuel gelir girdi.',
    true
  )
  on conflict (user_id, month)
  do update set
    declared_income = excluded.declared_income,
    income_source = excluded.income_source,
    savings_goal = excluded.savings_goal,
    budget_goal = excluded.budget_goal,
    notes = excluded.notes,
    is_finalized = excluded.is_finalized,
    updated_at = now();

  -- Manual income transaction
  insert into public.transactions (
    user_id,
    account_id,
    month,
    transaction_date,
    transaction_time,
    description,
    amount,
    direction,
    category,
    counterparty,
    source,
    is_user_confirmed
  )
  values (
    v_user_id,
    v_account_id,
    '2026-05',
    '2026-05-01',
    '09:00',
    'Mayıs maaşı',
    25000,
    'income',
    'Gelir',
    'İşveren',
    'manual',
    true
  );

  -- Manual expenses
  insert into public.transactions (
    user_id,
    account_id,
    month,
    transaction_date,
    transaction_time,
    description,
    amount,
    direction,
    category,
    counterparty,
    source,
    is_user_confirmed
  )
  values
  (
    v_user_id,
    v_account_id,
    '2026-05',
    '2026-05-03',
    '18:20',
    'Yemeksepeti siparişi',
    420,
    'expense',
    'Yemek',
    'Yemeksepeti',
    'manual',
    true
  ),
  (
    v_user_id,
    v_account_id,
    '2026-05',
    '2026-05-05',
    '21:10',
    'Trendyol alışverişi',
    1350,
    'expense',
    'Alışveriş',
    'Trendyol',
    'manual',
    true
  ),
  (
    v_user_id,
    v_account_id,
    '2026-05',
    '2026-05-08',
    '08:30',
    'Otobüs kart dolumu',
    300,
    'expense',
    'Ulaşım',
    'Ulaşım Kartı',
    'manual',
    true
  ),
  (
    v_user_id,
    v_account_id,
    '2026-05',
    '2026-05-10',
    '12:00',
    'Kira ödemesi',
    7500,
    'expense',
    'Kira',
    'Ev Sahibi',
    'manual',
    true
  );

end $$;