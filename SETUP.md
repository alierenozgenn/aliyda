# Aliyda — Kurulum Rehberi

Bu dosya projeyi sıfırdan kurmak için tüm adımları içerir.  
Her iki geliştirici de bu adımları takip ederek aynı ortamı elde edebilir.

---

## Gerekli Araçlar

Başlamadan önce bilgisayarında şunların kurulu olduğunu kontrol et:

| Araç | Sürüm | İndirme |
|------|-------|---------|
| Python | 3.11 veya üzeri | https://python.org/downloads |
| Node.js | 18 veya üzeri | https://nodejs.org |
| Git | Herhangi bir sürüm | https://git-scm.com |

Kontrol komutları:
```bash
python --version   # 3.11+ olmalı
node --version     # v18+ olmalı
git --version
```

---

## 1. Repoyu Klonla

```bash
git clone https://github.com/ilaydakyldzz/aliyda.git
cd aliyda
```

---

## 2. Supabase Kurulumu (Manuel — Her kişi ayrı yapar)

Her geliştirici kendi Supabase projesini oluşturur veya aynı projeyi paylaşır.

### 2.1 Proje Oluştur

1. https://supabase.com adresine git
2. "New Project" tıkla
3. Proje adı: `aliyda` (ya da istediğin bir isim)
4. Veritabanı şifresi oluştur ve bir yere yaz
5. Region: Europe (Frankfurt) seç
6. "Create new project" tıkla — birkaç dakika bekle

### 2.2 Tabloları Oluştur

Supabase Dashboard → **SQL Editor** → "New query" ile aşağıdaki SQL'leri **sırayla** çalıştır:

**1. users tablosu:**
```sql
create table users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  name text,
  preferred_currency text default 'TRY',
  created_at timestamptz default now()
);
```

**2. categories tablosu + varsayılan kategoriler:**
```sql
create table categories (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  name text not null,
  type text not null check (type in ('income','expense','both')),
  is_default boolean default false,
  color text default '#64748B',
  created_at timestamptz default now()
);

insert into categories (name, type, is_default) values
  ('Market', 'expense', true), ('Kira', 'expense', true),
  ('Ulaşım', 'expense', true), ('Yemek', 'expense', true),
  ('Fatura', 'expense', true), ('Eğitim', 'expense', true),
  ('Sağlık', 'expense', true), ('Eğlence', 'expense', true),
  ('Abonelik', 'expense', true), ('Giyim', 'expense', true),
  ('Transfer', 'both', true), ('Maaş', 'income', true),
  ('Freelance', 'income', true), ('Diğer', 'both', true);
```

**3. pdf_uploads tablosu:**
```sql
create table pdf_uploads (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  file_name text not null,
  bank_name text,
  status text not null default 'uploaded'
    check (status in ('uploaded','processing','completed','failed','needs_review')),
  error_message text,
  transaction_count int default 0,
  pending_count int default 0,
  created_at timestamptz default now()
);
```

**4. transactions tablosu:**
```sql
create table transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  upload_id uuid references pdf_uploads(id) on delete set null,
  category_id uuid references categories(id) on delete set null,
  date date not null,
  description text not null,
  amount numeric(12,2) not null,
  direction text not null check (direction in ('income','expense')),
  source text not null check (source in ('pdf','manual','system')),
  confidence numeric(4,3) check (confidence between 0 and 1),
  is_verified boolean default false,
  raw_text text,
  is_recurring boolean default false,
  created_at timestamptz default now()
);

create index idx_transactions_user_date on transactions(user_id, date desc);
create index idx_transactions_category on transactions(user_id, category_id);
```

**5. category_rules tablosu:**
```sql
create table category_rules (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  keyword text not null,
  category_id uuid not null references categories(id) on delete cascade,
  match_count int default 1,
  created_at timestamptz default now(),
  unique(user_id, keyword)
);
```

**6. goals tablosu:**
```sql
create table goals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  name text not null,
  target_amount numeric(12,2) not null,
  current_savings numeric(12,2) default 0,
  target_date date not null,
  is_active boolean default true,
  created_at timestamptz default now()
);
```

**7. budget_limits tablosu:**
```sql
create table budget_limits (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  category_id uuid not null references categories(id) on delete cascade,
  monthly_limit numeric(12,2) not null,
  created_at timestamptz default now(),
  unique(user_id, category_id)
);
```

### 2.3 Row Level Security (RLS) Aktif Et

Aynı SQL Editor'da aşağıdakileri çalıştır:

```sql
alter table transactions enable row level security;
create policy "users_own_transactions" on transactions
  for all using (auth.uid() = user_id);

alter table categories enable row level security;
create policy "default_categories_readable" on categories
  for select using (is_default = true or auth.uid() = user_id);
create policy "users_own_categories" on categories
  for insert with check (auth.uid() = user_id);
create policy "users_modify_own_categories" on categories
  for all using (auth.uid() = user_id and is_default = false);

alter table category_rules enable row level security;
create policy "users_own_rules" on category_rules
  for all using (auth.uid() = user_id);

alter table pdf_uploads enable row level security;
create policy "users_own_uploads" on pdf_uploads
  for all using (auth.uid() = user_id);

alter table goals enable row level security;
create policy "users_own_goals" on goals
  for all using (auth.uid() = user_id);

alter table budget_limits enable row level security;
create policy "users_own_limits" on budget_limits
  for all using (auth.uid() = user_id);
```

### 2.4 API Anahtarlarını Al

Supabase Dashboard → **Project Settings** → **API** sayfasında:

- `Project URL` → `SUPABASE_URL` olarak kopyala
- `service_role` (secret) key → `SUPABASE_SERVICE_KEY` olarak kopyala
- `anon` (public) key → Frontend için `VITE_SUPABASE_ANON_KEY` olarak kopyala

Supabase Dashboard → **Project Settings** → **JWT Settings**:

- `JWT Secret` → `SUPABASE_JWT_SECRET` olarak kopyala

---

## 3. Gemini API Key Al (Manuel)

1. https://aistudio.google.com adresine git
2. Sol menüden **Get API key** tıkla
3. **Create API key** → "Create API key in new project" seç
4. Oluşturulan key'i kopyala → `GEMINI_API_KEY` olarak kaydet

---

## 4. Backend Kurulumu

### 4.1 Sanal Ortam Oluştur

**Windows:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
```

### 4.2 Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

### 4.3 .env Dosyasını Oluştur

`backend/` klasörü içinde `.env` adında bir dosya oluştur:

```env
APP_ENV=development
FRONTEND_URL=http://localhost:5173
SUPABASE_URL=https://xxxxxxxxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGci...
SUPABASE_JWT_SECRET=your-jwt-secret
GEMINI_API_KEY=AIzaSy...
```

> `.env` dosyasına asla gerçek değerlerle commit atma. `.gitignore`'da zaten var.

### 4.4 Backend'i Başlat

```bash
uvicorn app.main:app --reload --port 8000
```

Çalıştığını doğrulamak için: http://localhost:8000/health  
Beklenen yanıt: `{"status":"ok","env":"development"}`

---

## 5. Frontend Kurulumu

### 5.1 Bağımlılıkları Yükle

```bash
cd frontend
npm install
```

### 5.2 .env Dosyasını Oluştur

`frontend/` klasörü içinde `.env.local` adında bir dosya oluştur:

```env
VITE_SUPABASE_URL=https://xxxxxxxxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGci...
VITE_API_URL=http://localhost:8000
```

> `.env.local` dosyası Vite tarafından otomatik yüklenir ve `.gitignore`'da zaten var.

### 5.3 Frontend'i Başlat

```bash
npm run dev
```

Uygulama: http://localhost:5173

---

## 6. Her Şeyin Çalıştığını Doğrula

Backend:
```bash
# Windows
curl http://localhost:8000/health

# PowerShell
Invoke-RestMethod http://localhost:8000/health
```

Supabase bağlantısı (backend venv aktifken):
```bash
python -c "
from app.services.supabase_client import get_supabase
sb = get_supabase()
tables = ['users','categories','transactions','pdf_uploads','category_rules','goals','budget_limits']
for t in tables:
    try:
        sb.table(t).select('id').limit(1).execute()
        print(f'  {t}: OK')
    except Exception as e:
        print(f'  {t}: HATA - {e}')
"
```

LangGraph pipeline:
```bash
python -c "
from app.agents.graph import finance_graph
print('Graph node sayisi:', len(finance_graph.nodes))
print('Graph derlendi: OK')
"
```

---

## 7. Mevcut Durum (15 Mayıs 2026)

Son commit: **Adım 15 tamamlandı** (`logic: implement deterministic financial summary and health score`)

**Tamamlanan adımlar:** 1–15  
**Sonraki adım:** Adım 16 — Analytics API

Hangi adımın yapılıp yapılmadığını görmek için:
```bash
git log --oneline -20
```

---

## Hızlı Başlangıç (Her İki Geliştirici İçin)

Kurulum tamamlandıktan sonra her oturumda:

```bash
# Terminal 1 — Backend
cd backend
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Ardından Claude Code'a `PROMPT.md` içeriğini yapıştır ve "Devam et" de.
