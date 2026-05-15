# 🚀 Aliyda — Teknik Geliştirme Yol Haritası

> **Stack:** Gemini API · LangGraph · FastAPI · React + Tailwind · Supabase  
> **Süre:** 5 Gün Sprint  
> **Amaç:** PDF banka ekstresinden otomatik finansal içgörü üreten agentic sistem

---

## 📋 İçindekiler

- [Teknoloji Kararları](#teknoloji-kararları)
- [GÜN 1 — Altyapı, Supabase, Auth, LangGraph İskeleti](#gün-1--altyapı-supabase-auth-langgraph-i̇skeleti)
- [GÜN 2 — PDF Pipeline, Gemini, LangGraph Nodeları](#gün-2--pdf-pipeline-gemini-langgraph-nodeları)
- [GÜN 3 — Finansal Hesaplama, Anomali, Verification UI](#gün-3--finansal-hesaplama-anomali-verification-ui)
- [GÜN 4 — Dashboard, AI Özetler, Frontend](#gün-4--dashboard-ai-özetler-frontend)
- [GÜN 5 — Demo, Deploy, Sunum](#gün-5--demo-deploy-sunum)
- [Hızlı Başvuru](#hızlı-başvuru)

---

## Teknoloji Kararları

| Teknoloji | Görev | Neden |
|-----------|-------|-------|
| **Gemini API** | PDF okuma, kategori tahmini, doğal dil özeti | Yarışma zorunluluğu + multimodal güç |
| **LangGraph** | Agentic pipeline orchestration | Gerçek agentic yapı kriteri |
| **FastAPI** | Asenkron backend, finansal hesaplama | Performans + Pydantic validation |
| **Supabase** | PostgreSQL + Auth + RLS | Hızlı geliştirme + güvenlik |
| **React + TW** | Kullanıcı arayüzü, dashboard | Hız + mobil uyum |

> ⚠️ **Kritik Kural:** Finansal hesaplamalar LLM'e yaptırılmaz. Backend'de deterministik fonksiyonlarla hesaplanır. LLM yalnızca sonuçları yorumlar.

---

## GÜN 1 — Altyapı, Supabase, Auth, LangGraph İskeleti

**Hedef:** Backend ayakta, Supabase şeması kurulu, kullanıcı giriş yapabiliyor, LangGraph iskeleti tanımlı.

---

### Adım 1 — Monorepo Yapısı
**Süre:** ~30 dk

```
aliyda/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── services/
│   │   ├── agents/          <- LangGraph node'ları burada
│   │   ├── schemas/
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── App.jsx
│   ├── package.json
│   └── .env.example
├── docs/
└── .gitignore
```

**.gitignore:**

```gitignore
__pycache__/
*.pyc
venv/
.env
node_modules/
dist/
.env.local
.DS_Store
```

```bash
git add . && git commit -m "init: create monorepo structure and project folders"
```

---

### Adım 2 — Backend Kurulumu
**Süre:** ~45 dk

**`requirements.txt`:**

```txt
fastapi
uvicorn[standard]
python-dotenv
pydantic
pydantic-settings
python-multipart
supabase
PyJWT
langchain
langchain-google-genai
langgraph
google-generativeai
python-jose[cryptography]
httpx
pytest
pytest-asyncio
```

**`backend/app/core/config.py`:**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_JWT_SECRET: str
    GEMINI_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
```

**`.env.example`:**

```env
APP_ENV=development
FRONTEND_URL=http://localhost:5173
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SUPABASE_JWT_SECRET=
GEMINI_API_KEY=
```

**`backend/app/main.py`:**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import router

app = FastAPI(title="Aliyda API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router.api_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.APP_ENV}
```

```bash
git add . && git commit -m "setup: initialize fastapi backend with config and health endpoint"
```

---

### Adım 3 — Supabase Şeması
**Süre:** ~60 dk

Supabase → SQL Editor'da sırayla çalıştır:

**`users`:**

```sql
create table users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  name text,
  preferred_currency text default 'TRY',
  created_at timestamptz default now()
);
```

**`categories` + varsayılan kategoriler:**

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

**`pdf_uploads`:**

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

**`transactions`:**

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

**`category_rules`:**

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

**`goals`:**

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

**`budget_limits`:**

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

```bash
git add . && git commit -m "db: create full supabase schema with all tables and indexes"
```

---

### Adım 4 — Row Level Security
**Süre:** ~30 dk

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

```bash
git add . && git commit -m "security: enable row level security policies for all tables"
```

---

### Adım 5 — JWT Doğrulama
**Süre:** ~30 dk

**`backend/app/core/security.py`:**

```python
from jose import jwt, JWTError
from fastapi import HTTPException, status
from app.core.config import settings

def verify_supabase_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş oturum."
        )
```

**`backend/app/dependencies/auth.py`:**

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_supabase_token

bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    payload = verify_supabase_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı.")
    return {"user_id": user_id, "email": payload.get("email")}
```

```bash
git add . && git commit -m "backend: add jwt authentication dependency"
```

---

### Adım 6 — LangGraph Pipeline İskeleti
**Süre:** ~60 dk

**`backend/app/agents/state.py`:**

```python
from typing import TypedDict, Optional, List

class FinanceAgentState(TypedDict):
    pdf_bytes: Optional[bytes]
    user_id: str
    upload_id: str
    raw_transactions: Optional[List[dict]]
    extraction_error: Optional[str]
    valid_transactions: Optional[List[dict]]
    invalid_transactions: Optional[List[dict]]
    categorized_transactions: Optional[List[dict]]
    anomalies: Optional[List[dict]]
    financial_summary: Optional[dict]
    insight_text: Optional[str]
    retry_count: int
    status: str
```

**`backend/app/agents/graph.py`:**

```python
from langgraph.graph import StateGraph, END
from app.agents.state import FinanceAgentState
from app.agents.nodes import (
    pdf_reader_node, validation_node, category_node,
    anomaly_node, analytics_node, insight_node,
)

def should_retry(state: FinanceAgentState) -> str:
    if state.get("extraction_error"):
        if state.get("retry_count", 0) < 2:
            return "retry"
        return "needs_review"
    return "continue"

def build_finance_graph():
    graph = StateGraph(FinanceAgentState)

    graph.add_node("pdf_reader", pdf_reader_node)
    graph.add_node("validation", validation_node)
    graph.add_node("category",   category_node)
    graph.add_node("anomaly",    anomaly_node)
    graph.add_node("analytics",  analytics_node)
    graph.add_node("insight",    insight_node)

    graph.set_entry_point("pdf_reader")
    graph.add_conditional_edges(
        "pdf_reader", should_retry,
        {"retry": "pdf_reader", "needs_review": END, "continue": "validation"}
    )
    graph.add_edge("validation", "category")
    graph.add_edge("category",   "anomaly")
    graph.add_edge("anomaly",    "analytics")
    graph.add_edge("analytics",  "insight")
    graph.add_edge("insight",    END)

    return graph.compile()

finance_graph = build_finance_graph()
```

**`backend/app/agents/nodes.py` — boş iskelet:**

```python
from app.agents.state import FinanceAgentState

async def pdf_reader_node(state: FinanceAgentState) -> FinanceAgentState:
    # TODO: Gun 2 - Gemini ile PDF'ten islem cikar
    return {**state, "raw_transactions": [], "retry_count": state.get("retry_count", 0)}

async def validation_node(state: FinanceAgentState) -> FinanceAgentState:
    # TODO: Gun 2 - AI ciktisini dogrula
    return {**state, "valid_transactions": [], "invalid_transactions": []}

async def category_node(state: FinanceAgentState) -> FinanceAgentState:
    # TODO: Gun 2 - Kategori ata, kullanici kurallarini uygula
    return {**state, "categorized_transactions": []}

async def anomaly_node(state: FinanceAgentState) -> FinanceAgentState:
    # TODO: Gun 3 - Anormal harcamalari tespit et
    return {**state, "anomalies": []}

async def analytics_node(state: FinanceAgentState) -> FinanceAgentState:
    # TODO: Gun 3 - Deterministik finansal hesaplama (LLM kullanma!)
    return {**state, "financial_summary": {}}

async def insight_node(state: FinanceAgentState) -> FinanceAgentState:
    # TODO: Gun 4 - Gemini ile dogal dil ozeti uret
    return {**state, "insight_text": "", "status": "completed"}
```

```bash
git add . && git commit -m "ai: initialize langgraph pipeline structure with state and node definitions"
```

---

### Adım 7 — Frontend Kurulumu + Auth
**Süre:** ~60 dk

```bash
cd frontend
npm create vite@latest . -- --template react
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install @supabase/supabase-js @tanstack/react-query react-router-dom recharts lucide-react axios
```

**`src/services/supabaseClient.js`:**

```js
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)
```

**`src/context/AuthContext.jsx`:**

```jsx
import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '../services/supabaseClient'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setUser(data.session?.user ?? null)
      setLoading(false)
    })
    const { data: listener } = supabase.auth.onAuthStateChange((_e, session) => {
      setUser(session?.user ?? null)
    })
    return () => listener.subscription.unsubscribe()
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
```

**`src/components/ProtectedRoute.jsx`:**

```jsx
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center h-screen">Yukleniyor...</div>
  if (!user)   return <Navigate to="/login" replace />
  return children
}
```

```bash
git add . && git commit -m "auth: implement supabase login register and protected routes"
```

---

## GÜN 2 — PDF Pipeline, Gemini, LangGraph Nodeları

**Hedef:** `PDF yukle -> Gemini analiz et -> JSON dogrula -> DB'ye kaydet` akisi uctan uca calissin.

> ⚠️ Bu gun en kritik gundur. Demo PDF'ini bu gun Gemini ile test et.

---

### Adım 8 — Pydantic Şemaları
**Süre:** ~30 dk

**`backend/app/schemas/transaction.py`:**

```python
from pydantic import BaseModel, validator
from typing import Optional
from datetime import date

class TransactionCreate(BaseModel):
    date: date
    description: str
    amount: float
    direction: str
    category_id: Optional[str] = None
    source: str = "manual"

class TransactionUpdate(BaseModel):
    category_id: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    direction: Optional[str] = None
    date: Optional[date] = None
    is_verified: Optional[bool] = None

class PDFTransactionItem(BaseModel):
    date: str
    description: str
    amount: float
    direction: str
    estimated_category: str
    confidence: float
    raw_text: Optional[str] = None

    @validator('direction')
    def check_direction(cls, v):
        if v not in ('income', 'expense'):
            raise ValueError("direction must be income or expense")
        return v

    @validator('confidence')
    def check_confidence(cls, v):
        if not (0 <= v <= 1):
            raise ValueError("confidence must be between 0 and 1")
        return v
```

```bash
git add . && git commit -m "backend: define pydantic schemas for all finance entities"
```

---

### Adım 9 — PDF Upload Endpoint
**Süre:** ~30 dk

**`backend/app/api/pdf.py`:**

```python
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from app.dependencies.auth import get_current_user
from app.services.supabase_client import get_supabase
from app.agents.graph import finance_graph

router = APIRouter()
MAX_SIZE_MB = 10

@router.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Yalnizca PDF dosyasi kabul edilir.")

    contents = await file.read()
    if len(contents) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"Dosya boyutu {MAX_SIZE_MB}MB'i gecemez.")

    sb = get_supabase()
    upload = sb.table("pdf_uploads").insert({
        "user_id": user["user_id"],
        "file_name": file.filename,
        "status": "uploaded"
    }).execute()
    upload_id = upload.data[0]["id"]

    background_tasks.add_task(run_finance_pipeline, contents, user["user_id"], upload_id)
    return {"upload_id": upload_id, "status": "processing"}


async def run_finance_pipeline(pdf_bytes: bytes, user_id: str, upload_id: str):
    sb = get_supabase()
    sb.table("pdf_uploads").update({"status": "processing"}).eq("id", upload_id).execute()
    try:
        result = await finance_graph.ainvoke({
            "pdf_bytes": pdf_bytes, "user_id": user_id, "upload_id": upload_id,
            "retry_count": 0, "status": "processing"
        })
        sb.table("pdf_uploads").update(
            {"status": result.get("status", "completed")}
        ).eq("id", upload_id).execute()
    except Exception as e:
        sb.table("pdf_uploads").update(
            {"status": "failed", "error_message": str(e)}
        ).eq("id", upload_id).execute()


@router.get("/uploads")
async def list_uploads(user = Depends(get_current_user)):
    sb = get_supabase()
    return sb.table("pdf_uploads").select("*").eq(
        "user_id", user["user_id"]
    ).order("created_at", desc=True).execute().data

@router.get("/uploads/{upload_id}")
async def get_upload(upload_id: str, user = Depends(get_current_user)):
    sb = get_supabase()
    return sb.table("pdf_uploads").select("*").eq(
        "id", upload_id
    ).eq("user_id", user["user_id"]).single().execute().data
```

```bash
git add . && git commit -m "feat: add secure pdf upload endpoint with background processing"
```

---

### Adım 10 — Gemini Servisi + pdf_reader_node
**Süre:** ~90 dk

**`backend/app/services/gemini_service.py`:**

```python
import google.generativeai as genai
import json
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

EXTRACTION_PROMPT = """
Sen bir banka ekstresi analiz uzmanisın.

GÖREVIN:
- PDF içindeki tüm finansal işlemleri çıkar
- Her işlem için aşağıdaki JSON formatını kullan
- Emin olmadığın kategoriler için "Diger" yaz
- YALNIZCA JSON döndür, baska hiçbir şey yazma
- Yatırım tavsiyesi verme, finansal yorum yapma
- Toplam hesaplama yapma

ÇIKTI FORMATI:
{
  "transactions": [
    {
      "date": "YYYY-MM-DD",
      "description": "islem aciklamasi",
      "amount": 123.45,
      "direction": "expense",
      "estimated_category": "Market",
      "confidence": 0.92,
      "raw_text": "orijinal pdf satiri"
    }
  ]
}

direction: sadece "income" veya "expense"
Kategoriler: Market, Kira, Ulasim, Yemek, Fatura, Egitim, Saglik,
             Eglence, Abonelik, Giyim, Transfer, Maas, Freelance, Diger
"""

async def extract_transactions_from_pdf(pdf_bytes: bytes) -> dict:
    pdf_part = {"mime_type": "application/pdf", "data": pdf_bytes}
    response = model.generate_content([EXTRACTION_PROMPT, pdf_part])
    text = response.text.strip()
    # JSON fence temizle
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])
    return json.loads(text.strip())
```

**`nodes.py` — pdf_reader_node guncelle:**

```python
from app.services.gemini_service import extract_transactions_from_pdf

async def pdf_reader_node(state: FinanceAgentState) -> FinanceAgentState:
    try:
        result = await extract_transactions_from_pdf(state["pdf_bytes"])
        return {
            **state,
            "raw_transactions": result.get("transactions", []),
            "extraction_error": None,
        }
    except Exception as e:
        return {
            **state,
            "raw_transactions": [],
            "extraction_error": str(e),
            "retry_count": state.get("retry_count", 0) + 1,
        }
```

```bash
git add . && git commit -m "ai: integrate gemini service for pdf transaction extraction"
```

---

### Adım 11 — validation_node
**Süre:** ~45 dk

**`nodes.py` — validation_node guncelle:**

```python
from datetime import datetime

CONFIDENCE_THRESHOLD = 0.80
VALID_DIRECTIONS = {"income", "expense"}
VALID_CATEGORIES = {
    "Market","Kira","Ulasim","Yemek","Fatura","Egitim",
    "Saglik","Eglence","Abonelik","Giyim","Transfer",
    "Maas","Freelance","Diger"
}

async def validation_node(state: FinanceAgentState) -> FinanceAgentState:
    valid, invalid = [], []

    for item in state.get("raw_transactions", []):
        errors = []

        try:
            datetime.strptime(item.get("date", ""), "%Y-%m-%d")
        except ValueError:
            errors.append("invalid_date")

        if not isinstance(item.get("amount"), (int, float)) or item.get("amount") <= 0:
            errors.append("invalid_amount")

        if item.get("direction") not in VALID_DIRECTIONS:
            errors.append("invalid_direction")

        if not item.get("description", "").strip():
            errors.append("empty_description")

        confidence = item.get("confidence", 0)
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            confidence = 0.5
            item["confidence"] = confidence

        if item.get("estimated_category") not in VALID_CATEGORIES:
            item["estimated_category"] = "Diger"
            item["confidence"] = min(confidence, 0.5)

        if errors:
            item["validation_errors"] = errors
            invalid.append(item)
        else:
            item["is_verified"] = confidence >= CONFIDENCE_THRESHOLD
            valid.append(item)

    return {**state, "valid_transactions": valid, "invalid_transactions": invalid}
```

```bash
git add . && git commit -m "ai: implement validation node with full schema checks"
```

---

### Adım 12 — category_node + DB Kayıt + Duplicate Detection
**Süre:** ~45 dk

**`nodes.py` — category_node guncelle:**

```python
from app.services.supabase_client import get_supabase

async def category_node(state: FinanceAgentState) -> FinanceAgentState:
    sb = get_supabase()
    user_id = state["user_id"]

    # Ogrenilen kurallari cek
    rules_res = sb.table("category_rules").select("*").eq("user_id", user_id).execute()
    rules = {r["keyword"].lower(): r["category_id"] for r in rules_res.data}

    # Kategori adi -> id
    cats_res = sb.table("categories").select("id,name").execute()
    cat_name_to_id = {c["name"]: c["id"] for c in cats_res.data}

    # Duplicate kontrolu
    existing = sb.table("transactions").select("date,amount,description").eq("user_id", user_id).execute()
    existing_keys = {
        (r["date"], str(r["amount"]), r["description"].lower())
        for r in existing.data
    }

    categorized, to_insert = [], []
    for item in state.get("valid_transactions", []):
        # Once ogrenilen kurallar
        matched_cat_id = None
        for keyword, cat_id in rules.items():
            if keyword in item["description"].lower():
                matched_cat_id = cat_id
                item["confidence"] = min(item["confidence"] + 0.15, 1.0)
                break

        if not matched_cat_id:
            gemini_cat = item.get("estimated_category", "Diger")
            matched_cat_id = cat_name_to_id.get(gemini_cat, cat_name_to_id.get("Diger"))

        item["category_id"] = matched_cat_id
        categorized.append(item)

        # Duplicate degilse ekle
        key = (item["date"], str(item["amount"]), item["description"].lower())
        if key not in existing_keys:
            to_insert.append({
                "user_id":     user_id,
                "upload_id":   state["upload_id"],
                "date":        item["date"],
                "description": item["description"],
                "amount":      item["amount"],
                "direction":   item["direction"],
                "category_id": matched_cat_id,
                "source":      "pdf",
                "confidence":  item.get("confidence", 0.5),
                "is_verified": item.get("is_verified", False),
                "raw_text":    item.get("raw_text"),
            })

    if to_insert:
        sb.table("transactions").insert(to_insert).execute()

    return {**state, "categorized_transactions": categorized}
```

```bash
git add . && git commit -m "ai: implement category node with rule matching and duplicate detection"
git add . && git commit -m "ai: persist extracted pdf transactions to database"
```

---

### Adım 13 — Transaction API
**Süre:** ~45 dk

**`backend/app/api/transactions.py`:**

```python
from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.dependencies.auth import get_current_user
from app.services.supabase_client import get_supabase

router = APIRouter()

@router.get("/")
async def list_transactions(
    date_from:   Optional[str]  = Query(None),
    date_to:     Optional[str]  = Query(None),
    category_id: Optional[str]  = Query(None),
    direction:   Optional[str]  = Query(None),
    is_verified: Optional[bool] = Query(None),
    page:        int = Query(1, ge=1),
    per_page:    int = Query(50, le=200),
    user = Depends(get_current_user)
):
    sb = get_supabase()
    q = sb.table("transactions").select("*, categories(name,color)").eq("user_id", user["user_id"])
    if date_from:   q = q.gte("date", date_from)
    if date_to:     q = q.lte("date", date_to)
    if category_id: q = q.eq("category_id", category_id)
    if direction:   q = q.eq("direction", direction)
    if is_verified is not None: q = q.eq("is_verified", is_verified)
    offset = (page - 1) * per_page
    return q.order("date", desc=True).range(offset, offset + per_page - 1).execute().data

@router.patch("/{transaction_id}/verify")
async def verify_transaction(transaction_id: str, body: dict, user = Depends(get_current_user)):
    sb = get_supabase()
    update_data = {k: v for k, v in body.items()
                   if k in ("category_id","description","amount","direction","date")}
    update_data["is_verified"] = True
    result = sb.table("transactions").update(update_data).eq(
        "id", transaction_id
    ).eq("user_id", user["user_id"]).execute()

    # Kategori degisikliginde ogrenilen kural kaydet
    if "category_id" in body and "description" in body:
        keyword = body["description"][:30].lower().strip()
        sb.table("category_rules").upsert({
            "user_id": user["user_id"],
            "keyword": keyword,
            "category_id": body["category_id"]
        }, on_conflict="user_id,keyword").execute()

    return result.data

@router.patch("/bulk-verify")
async def bulk_verify(body: dict, user = Depends(get_current_user)):
    sb = get_supabase()
    ids = body.get("transaction_ids", [])
    if not ids: return {"updated": 0}
    result = sb.table("transactions").update({"is_verified": True}).in_(
        "id", ids
    ).eq("user_id", user["user_id"]).execute()
    return {"updated": len(result.data)}
```

```bash
git add . && git commit -m "feat: implement transaction crud and verification endpoints"
```

---

## GÜN 3 — Finansal Hesaplama, Anomali, Verification UI

**Hedef:** Tum analitik servisler calissin, Finansal Saglik Skoru hesaplaniyor, Verification UI hazir.

---

### Adım 14 — anomaly_node
**Süre:** ~45 dk

**`nodes.py` — anomaly_node guncelle:**

```python
from datetime import date, timedelta
from collections import defaultdict

async def anomaly_node(state: FinanceAgentState) -> FinanceAgentState:
    sb = get_supabase()
    anomalies = []

    three_months_ago = (date.today() - timedelta(days=90)).isoformat()
    history = sb.table("transactions").select(
        "direction,category_id,amount,categories(name)"
    ).eq("user_id", state["user_id"]).eq("direction", "expense").gte("date", three_months_ago).execute()

    monthly_totals = defaultdict(lambda: {"total": 0, "count": 0})
    for t in history.data:
        cat_name = t.get("categories", {}).get("name", "Diger")
        monthly_totals[cat_name]["total"] += t["amount"]
        monthly_totals[cat_name]["count"] += 1

    current_by_cat = defaultdict(float)
    for item in state.get("categorized_transactions", []):
        if item["direction"] == "expense":
            current_by_cat[item.get("estimated_category", "Diger")] += item["amount"]

    for cat, current_total in current_by_cat.items():
        if cat in monthly_totals:
            hist = monthly_totals[cat]
            avg = hist["total"] / max(hist["count"] / 30, 1)
            if current_total > avg * 1.25 and current_total > 500:
                pct = round((current_total - avg) / avg * 100, 1)
                anomalies.append({
                    "category": cat,
                    "current": current_total,
                    "average": round(avg, 2),
                    "increase_pct": pct,
                    "message": f"{cat} harcamalariniz gecmis ortalamanin %{pct} uzerinde."
                })

    return {**state, "anomalies": anomalies}
```

```bash
git add . && git commit -m "analytics: implement anomaly detection node"
```

---

### Adım 15 — analytics_node + Finansal Sağlık Skoru
**Süre:** ~60 dk

> ⚠️ Bu node'dan cikan hicbir sayi LLM tarafindan hesaplanmamistir.

**`backend/app/services/finance_summary_service.py`:**

```python
from datetime import date
from collections import defaultdict

def calculate_financial_summary(transactions: list, anomalies: list) -> dict:
    total_income  = sum(t["amount"] for t in transactions if t["direction"] == "income")
    total_expense = sum(t["amount"] for t in transactions if t["direction"] == "expense")
    net_balance   = total_income - total_expense

    cat_totals = defaultdict(float)
    for t in transactions:
        if t["direction"] == "expense":
            cat_totals[t.get("estimated_category", "Diger")] += t["amount"]

    categories = []
    for cat, amount in sorted(cat_totals.items(), key=lambda x: -x[1]):
        pct = round(amount / total_expense * 100, 1) if total_expense > 0 else 0
        categories.append({"name": cat, "amount": round(amount, 2), "percentage": pct})

    today          = date.today()
    days_passed    = today.day
    remaining_days = 30 - days_passed
    daily_expense  = total_expense / max(days_passed, 1)
    projected_end  = round(net_balance - (daily_expense * remaining_days), 2)

    return {
        "total_income":        round(total_income, 2),
        "total_expense":       round(total_expense, 2),
        "net_balance":         round(net_balance, 2),
        "categories":          categories,
        "top_category":        categories[0]["name"] if categories else None,
        "daily_expense_avg":   round(daily_expense, 2),
        "projected_month_end": projected_end,
        "anomalies":           anomalies,
        "health_score":        _health_score(total_income, total_expense, net_balance, categories),
    }

def _health_score(income, expense, net, categories) -> int:
    """
    Finansal Saglik Skoru (0-100):
      Gelir/Gider orani  : 40 puan
      Tasarruf orani     : 30 puan
      Kategori yogunlugu : 30 puan
    """
    score = 0
    if income > 0:
        score += min(40, int((net / income) * 80))
        score += min(30, int((max(0, net) / income) * 100))
    if categories and expense > 0:
        top_pct = categories[0]["percentage"]
        if top_pct < 30:   score += 30
        elif top_pct < 50: score += 20
        elif top_pct < 70: score += 10
    return max(0, min(100, score))
```

**`nodes.py` — analytics_node guncelle:**

```python
from app.services.finance_summary_service import calculate_financial_summary

async def analytics_node(state: FinanceAgentState) -> FinanceAgentState:
    summary = calculate_financial_summary(
        state.get("categorized_transactions", []),
        state.get("anomalies", [])
    )
    return {**state, "financial_summary": summary}
```

```bash
git add . && git commit -m "logic: implement deterministic financial summary and health score"
```

---

### Adım 16 — Analytics API
**Süre:** ~45 dk

**`backend/app/api/analytics.py`:**

```python
from fastapi import APIRouter, Depends, Query
from app.dependencies.auth import get_current_user
from app.services.supabase_client import get_supabase
from app.services.finance_summary_service import calculate_financial_summary
from datetime import date
from collections import defaultdict

router = APIRouter()

@router.get("/summary")
async def get_summary(month: str = Query(None), user = Depends(get_current_user)):
    sb = get_supabase()
    if not month:
        today = date.today()
        month = f"{today.year}-{today.month:02d}"
    txs = sb.table("transactions").select("*, categories(name)").eq(
        "user_id", user["user_id"]
    ).gte("date", f"{month}-01").lte("date", f"{month}-31").execute()
    transactions = [
        {**t, "estimated_category": t.get("categories", {}).get("name", "Diger")}
        for t in txs.data
    ]
    return calculate_financial_summary(transactions, [])

@router.get("/pending-review")
async def get_pending(user = Depends(get_current_user)):
    sb = get_supabase()
    result = sb.table("transactions").select("*, categories(name)").eq(
        "user_id", user["user_id"]
    ).eq("is_verified", False).order("confidence").execute()
    return {"pending": result.data, "count": len(result.data)}

@router.get("/monthly-trend")
async def monthly_trend(user = Depends(get_current_user)):
    sb = get_supabase()
    result = sb.table("transactions").select("date,amount,direction").eq(
        "user_id", user["user_id"]
    ).order("date").execute()
    monthly = defaultdict(lambda: {"income": 0, "expense": 0})
    for t in result.data:
        monthly[t["date"][:7]][t["direction"]] += t["amount"]
    return [
        {"month": k, **v, "net": round(v["income"] - v["expense"], 2)}
        for k, v in sorted(monthly.items())
    ]
```

```bash
git add . && git commit -m "analytics: add financial summary monthly trend and pending review endpoints"
```

---

### Adım 17 — Hedef Planlama API
**Süre:** ~30 dk

**`backend/app/api/goals.py`:**

```python
from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.services.supabase_client import get_supabase
from datetime import date

router = APIRouter()

@router.post("/")
async def create_goal(body: dict, user = Depends(get_current_user)):
    sb = get_supabase()
    return sb.table("goals").insert({
        "user_id":         user["user_id"],
        "name":            body["name"],
        "target_amount":   body["target_amount"],
        "current_savings": body.get("current_savings", 0),
        "target_date":     body["target_date"]
    }).execute().data[0]

@router.get("/{goal_id}/analysis")
async def analyze_goal(goal_id: str, user = Depends(get_current_user)):
    sb = get_supabase()
    goal = sb.table("goals").select("*").eq("id", goal_id).eq(
        "user_id", user["user_id"]
    ).single().execute().data

    remaining    = goal["target_amount"] - goal["current_savings"]
    today        = date.today()
    target       = date.fromisoformat(goal["target_date"])
    months_left  = max(1, (target.year - today.year) * 12 + (target.month - today.month))
    req_monthly  = round(remaining / months_left, 2)
    req_weekly   = round(req_monthly / 4.33, 2)

    month_key = f"{today.year}-{today.month:02d}"
    txs = sb.table("transactions").select("amount,direction").eq(
        "user_id", user["user_id"]
    ).like("date", f"{month_key}%").execute()
    income  = sum(t["amount"] for t in txs.data if t["direction"] == "income")
    expense = sum(t["amount"] for t in txs.data if t["direction"] == "expense")
    surplus = round(income - expense, 2)

    return {
        "goal":             goal,
        "remaining_amount": round(remaining, 2),
        "months_left":      months_left,
        "required_monthly": req_monthly,
        "required_weekly":  req_weekly,
        "current_surplus":  surplus,
        "achievable":       surplus >= req_monthly,
        "shortfall_monthly": round(max(0, req_monthly - surplus), 2)
    }
```

```bash
git add . && git commit -m "feat: add savings goal planning and analysis endpoint"
```

---

### Adım 18 — Verification Center UI
**Süre:** ~90 dk

**`src/pages/VerificationCenter.jsx`:**

```jsx
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../services/apiClient'

export default function VerificationCenter() {
  const qc = useQueryClient()
  const [filter, setFilter] = useState('all')

  const { data, isLoading } = useQuery({
    queryKey: ['pending'],
    queryFn: () => apiClient.get('/analytics/pending-review').then(r => r.data)
  })

  const verifyMutation = useMutation({
    mutationFn: ({ id, body }) => apiClient.patch(`/transactions/${id}/verify`, body),
    onSuccess: () => qc.invalidateQueries(['pending'])
  })

  const bulkMutation = useMutation({
    mutationFn: (ids) => apiClient.patch('/transactions/bulk-verify', { transaction_ids: ids }),
    onSuccess: () => qc.invalidateQueries(['pending'])
  })

  if (isLoading) return <div className="p-8 text-center text-gray-400">Yukleniyor...</div>

  const pending  = data?.pending || []
  const highConf = pending.filter(t => t.confidence >= 0.80)
  const lowConf  = pending.filter(t => t.confidence < 0.80)
  const shown    = filter === 'low' ? lowConf : pending

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Dogrulama Merkezi</h1>
          <p className="text-sm text-gray-500 mt-1">AI'in cikardigi islemleri kontrol et ve onayla</p>
        </div>
        <span className="bg-amber-100 text-amber-800 px-3 py-1 rounded-full text-sm font-medium">
          {pending.length} islem bekliyor
        </span>
      </div>

      <div className="flex gap-3 mb-6">
        {highConf.length > 0 && (
          <button
            onClick={() => bulkMutation.mutate(highConf.map(t => t.id))}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm"
          >
            Yuksek guvenilirlikli {highConf.length} islemi onayla
          </button>
        )}
        <button
          onClick={() => setFilter(filter === 'low' ? 'all' : 'low')}
          className="border px-4 py-2 rounded-lg text-sm hover:bg-gray-50"
        >
          {filter === 'low' ? 'Tumunu goster' : `Sadece belirsizleri goster (${lowConf.length})`}
        </button>
      </div>

      <div className="space-y-3">
        {shown.map(tx => (
          <TransactionCard
            key={tx.id}
            transaction={tx}
            onVerify={(body) => verifyMutation.mutate({ id: tx.id, body })}
          />
        ))}
        {shown.length === 0 && (
          <div className="text-center py-12 text-gray-400">Tum islemler onaylandi!</div>
        )}
      </div>
    </div>
  )
}
```

```bash
git add . && git commit -m "ui: build transaction verification center with bulk approve"
```

---

## GÜN 4 — Dashboard, AI Özetler, Frontend

**Hedef:** `PDF yukle -> onayla -> dashboard gor -> hedef ekle` tam akisi calisin.

---

### Adım 19 — insight_node (AI Finansal Özet)
**Süre:** ~45 dk

**`nodes.py` — insight_node guncelle:**

```python
import json
import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
insight_model = genai.GenerativeModel("gemini-1.5-flash")

async def insight_node(state: FinanceAgentState) -> FinanceAgentState:
    summary = state.get("financial_summary", {})
    prompt = f"""
Sen bir kisisel finans asistanisin.
Kullanicinin bu ayki finansal ozeti:

{json.dumps(summary, ensure_ascii=False, indent=2)}

KURALLARI:
- Maksimum 4 cumle yaz
- Teknik terim kullanma
- Yatirim, hisse, kripto, doviz onerisi yapma kesinlikle
- Son cumlede mutlaka su notu ekle: "Bu yatirim tavsiyesi degildir."
- Turkce yaz
- Anomalileri varsa bir cumlede belirt

Sadece ozet metni yaz, baska hicbir sey ekleme.
"""
    response = insight_model.generate_content(prompt)
    return {**state, "insight_text": response.text.strip(), "status": "completed"}
```

```bash
git add . && git commit -m "ai: implement insight node for natural language financial summary"
```

---

### Adım 20 — API Client
**Süre:** ~30 dk

**`src/services/apiClient.js`:**

```js
import axios from 'axios'
import { supabase } from './supabaseClient'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL + '/api/v1'
})

apiClient.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export { apiClient }
```

```bash
git add . && git commit -m "frontend: setup axios api client with auth interceptor"
```

---

### Adım 21 — Ana Dashboard
**Süre:** ~90 dk

**`src/components/HealthScoreGauge.jsx`:**

```jsx
export function HealthScoreGauge({ score }) {
  const color = score >= 70 ? '#16a34a' : score >= 40 ? '#d97706' : '#dc2626'
  const label = score >= 70 ? 'Iyi' : score >= 40 ? 'Orta' : 'Dusuk'
  const dash  = score * 2.51

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border">
      <h3 className="text-sm font-medium text-gray-500 mb-4">Finansal Saglik Skoru</h3>
      <div className="flex items-center gap-4">
        <div className="relative w-24 h-24">
          <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
            <circle cx="50" cy="50" r="40" fill="none" stroke="#f1f5f9" strokeWidth="12"/>
            <circle cx="50" cy="50" r="40" fill="none" stroke={color} strokeWidth="12"
              strokeDasharray={`${dash} 251`} strokeLinecap="round"/>
          </svg>
          <div className="absolute inset-0 flex items-center justify-center rotate-90">
            <span className="text-2xl font-bold" style={{ color }}>{score}</span>
          </div>
        </div>
        <div>
          <span className="text-lg font-semibold" style={{ color }}>{label}</span>
          <p className="text-xs text-gray-400 mt-1">100 uzerinden</p>
        </div>
      </div>
    </div>
  )
}
```

**`src/pages/Dashboard.jsx`:**

```jsx
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../services/apiClient'
import { HealthScoreGauge } from '../components/HealthScoreGauge'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
         LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts'
import { Link } from 'react-router-dom'

const COLORS = ['#1A56A0','#16a34a','#d97706','#dc2626','#7c3aed','#0891b2']
const fmt = (n) => `${n?.toLocaleString('tr-TR') ?? '-'} TL`

function SummaryCard({ title, value, sub, colorClass = 'text-gray-800' }) {
  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border">
      <p className="text-sm text-gray-500 mb-1">{title}</p>
      <p className={`text-2xl font-bold ${colorClass}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const { data: summary } = useQuery({ queryKey: ['summary'], queryFn: () => apiClient.get('/analytics/summary').then(r => r.data) })
  const { data: trend }   = useQuery({ queryKey: ['trend'],   queryFn: () => apiClient.get('/analytics/monthly-trend').then(r => r.data) })
  const { data: pending } = useQuery({ queryKey: ['pending'], queryFn: () => apiClient.get('/analytics/pending-review').then(r => r.data) })
  const { data: insight } = useQuery({ queryKey: ['insight'], queryFn: () => apiClient.get('/analytics/insight').then(r => r.data) })

  if (!summary) return <div className="p-8 text-center text-gray-400">Yukleniyor...</div>

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">

      {pending?.count > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex justify-between items-center">
          <span className="text-amber-800">{pending.count} islem onayini bekliyor.</span>
          <Link to="/verify" className="text-amber-700 font-medium hover:underline">Incele</Link>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SummaryCard title="Toplam Gelir"   value={fmt(summary.total_income)}   colorClass="text-green-600"/>
        <SummaryCard title="Toplam Gider"   value={fmt(summary.total_expense)}  colorClass="text-red-600"/>
        <SummaryCard title="Net Durum"      value={fmt(summary.net_balance)}    colorClass={summary.net_balance >= 0 ? "text-green-600" : "text-red-600"}/>
        <SummaryCard title="Ay Sonu Tahmin" value={fmt(summary.projected_month_end)} sub="tahmini"/>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <HealthScoreGauge score={summary.health_score}/>
        <div className="md:col-span-2 bg-white rounded-2xl p-5 shadow-sm border">
          <h3 className="text-sm font-medium text-gray-500 mb-3">Harcama Dagilimi</h3>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={summary.categories} dataKey="amount" nameKey="name" cx="50%" cy="50%" outerRadius={70}>
                {summary.categories.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]}/>)}
              </Pie>
              <Tooltip formatter={(v) => fmt(v)}/>
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {insight?.insight && (
        <div className="bg-blue-50 border-l-4 border-blue-500 rounded-xl p-5">
          <p className="text-xs font-medium text-blue-500 mb-2">Aliyda'nin Analizi</p>
          <p className="text-gray-700 leading-relaxed">{insight.insight}</p>
        </div>
      )}

      {trend && trend.length > 0 && (
        <div className="bg-white rounded-2xl p-5 shadow-sm border">
          <h3 className="text-sm font-medium text-gray-500 mb-3">Aylik Gelir / Gider Trendi</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9"/>
              <XAxis dataKey="month" tick={{ fontSize: 12 }}/>
              <YAxis tick={{ fontSize: 12 }}/>
              <Tooltip formatter={(v) => fmt(v)}/>
              <Line type="monotone" dataKey="income"  stroke="#16a34a" strokeWidth={2} dot={false}/>
              <Line type="monotone" dataKey="expense" stroke="#dc2626" strokeWidth={2} dot={false}/>
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
```

```bash
git add . && git commit -m "ui: create financial dashboard with health score gauge and charts"
git add . && git commit -m "ui: add ai financial insight card to dashboard"
```

---

### Adım 22 — PDF Upload UI
**Süre:** ~60 dk

**`src/pages/Upload.jsx`:**

```jsx
import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../services/apiClient'

export default function Upload() {
  const [status, setStatus] = useState('idle')
  const navigate = useNavigate()

  const handleFile = useCallback(async (file) => {
    if (!file?.name.endsWith('.pdf')) {
      alert('Lutfen PDF formatinda banka ekstresi yukleyin.')
      return
    }
    setStatus('uploading')
    const form = new FormData()
    form.append('file', file)

    const res = await apiClient.post('/pdf/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    setStatus('processing')

    const poll = setInterval(async () => {
      const s = await apiClient.get(`/pdf/uploads/${res.data.upload_id}`)
      if (['completed','needs_review','failed'].includes(s.data.status)) {
        clearInterval(poll)
        setStatus('done')
        setTimeout(() => navigate('/verify'), 800)
      }
    }, 2000)
  }, [navigate])

  const labels = {
    idle:       'PDF\'i surukle birak veya tikla',
    uploading:  'Yukleniyor...',
    processing: 'Aliyda analiz ediyor...',
    done:       'Tamamlandi! Yonlendiriliyor...',
  }

  return (
    <div className="max-w-xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-2">Ekstreni Yukle</h1>
      <p className="text-gray-500 mb-6">PDF formatinda banka ekstreni yukle, Aliyda analiz etsin.</p>
      <div
        className="border-2 border-dashed border-blue-300 rounded-2xl p-16 text-center cursor-pointer hover:bg-blue-50 transition-colors"
        onDrop={(e) => { e.preventDefault(); handleFile(e.dataTransfer.files[0]) }}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => document.getElementById('fi').click()}
      >
        <p className={`text-lg ${status !== 'idle' ? 'text-blue-500 animate-pulse' : 'text-gray-400'}`}>
          {labels[status]}
        </p>
        <input id="fi" type="file" accept=".pdf" className="hidden"
          onChange={(e) => handleFile(e.target.files[0])}/>
      </div>
      <p className="text-xs text-gray-400 text-center mt-4">Maksimum 10MB - Yalnizca PDF</p>
    </div>
  )
}
```

```bash
git add . && git commit -m "ui: build pdf upload flow with status polling"
```

---

### Adım 23 — Hedef Planlama UI
**Süre:** ~45 dk

**`src/pages/Goals.jsx`:**

```jsx
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../services/apiClient'

function GoalCard({ goal }) {
  const { data: a } = useQuery({
    queryKey: ['goal', goal.id],
    queryFn: () => apiClient.get(`/goals/${goal.id}/analysis`).then(r => r.data)
  })
  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border">
      <div className="flex justify-between items-start mb-3">
        <h3 className="font-semibold">{goal.name}</h3>
        {a && (
          <span className={`text-xs px-2 py-1 rounded-full ${a.achievable ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {a.achievable ? 'Ulasılabilir' : 'Eksik var'}
          </span>
        )}
      </div>
      {a && (
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div><p className="text-gray-400 text-xs">Hedef</p><p className="font-medium">{goal.target_amount.toLocaleString()} TL</p></div>
          <div><p className="text-gray-400 text-xs">Kalan sure</p><p className="font-medium">{a.months_left} ay</p></div>
          <div><p className="text-gray-400 text-xs">Aylik birikim</p><p className="font-medium text-blue-600">{a.required_monthly.toLocaleString()} TL</p></div>
          <div><p className="text-gray-400 text-xs">Mevcut arti</p><p className={`font-medium ${a.achievable ? 'text-green-600' : 'text-red-600'}`}>{a.current_surplus.toLocaleString()} TL</p></div>
          {!a.achievable && (
            <p className="col-span-2 text-xs text-red-600 bg-red-50 rounded-lg p-2 mt-1">
              Aylik {a.shortfall_monthly.toLocaleString()} TL eksik.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default function Goals() {
  const qc = useQueryClient()
  const [form, setForm] = useState({ name: '', target_amount: '', target_date: '' })
  const { data: goals } = useQuery({ queryKey: ['goals'], queryFn: () => apiClient.get('/goals').then(r => r.data) })
  const createMutation = useMutation({
    mutationFn: (d) => apiClient.post('/goals', d),
    onSuccess: () => { qc.invalidateQueries(['goals']); setForm({ name:'', target_amount:'', target_date:'' }) }
  })

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Birikim Hedefleri</h1>
      <div className="bg-white rounded-2xl p-6 shadow-sm border mb-6">
        <h2 className="font-semibold mb-4">Yeni Hedef</h2>
        <input className="w-full border rounded-lg p-2 mb-3" placeholder="Hedef adi"
          value={form.name} onChange={e => setForm({...form, name: e.target.value})}/>
        <input className="w-full border rounded-lg p-2 mb-3" placeholder="Hedef tutar (TL)" type="number"
          value={form.target_amount} onChange={e => setForm({...form, target_amount: e.target.value})}/>
        <input className="w-full border rounded-lg p-2 mb-4" type="date"
          value={form.target_date} onChange={e => setForm({...form, target_date: e.target.value})}/>
        <button onClick={() => createMutation.mutate(form)}
          className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700">
          Hedef Olustur
        </button>
      </div>
      <div className="space-y-4">
        {goals?.map(g => <GoalCard key={g.id} goal={g}/>)}
      </div>
    </div>
  )
}
```

```bash
git add . && git commit -m "ui: build savings goal planning interface with analysis"
git add . && git commit -m "ui: improve mobile responsiveness and user experience"
```

---

## GÜN 5 — Demo, Deploy, Sunum

**Hedef:** Urun deploy edilmis, demo PDF test edilmis, sunum akisi hazir.

---

### Adım 24 — Global Hata Yönetimi
**Süre:** ~30 dk

**`backend/app/core/error_handler.py`:**

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": "Gonderi verisi gecersiz.", "details": exc.errors()})

async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Beklenmeyen hata: {exc}", exc_info=True)
    messages = {
        "pdf":      "PDF analiz edilirken sorun olustu. Dosyanin banka ekstresi oldugunu dogrulayin.",
        "supabase": "Veritabani baglantisi kurulamadi. Lutfen tekrar deneyin.",
        "gemini":   "AI servisi su an yanit vermiyor. Birkaç dakika sonra tekrar deneyin.",
    }
    for key, msg in messages.items():
        if key in str(exc).lower():
            return JSONResponse(status_code=500, content={"error": msg})
    return JSONResponse(status_code=500, content={"error": "Beklenmeyen bir hata olustu."})

# main.py'ye ekle:
# from app.core.error_handler import validation_exception_handler, general_exception_handler
# app.add_exception_handler(RequestValidationError, validation_exception_handler)
# app.add_exception_handler(Exception, general_exception_handler)
```

```bash
git add . && git commit -m "fix: add global backend error handling"
```

---

### Adım 25 — Demo PDF + Gemini Testi
**Süre:** ~60 dk

> ⚠️ Deploy etmeden once bu testi mutlaka yap!

**Demo PDF icerigi** (kisisel veri icermeyen test ekstresi):

```
Islem Tarihi  Aciklama                Tutar
01.05.2026    MAAS YATISI             +18.500,00 TL
03.05.2026    A101 MARKET             -   430,50 TL
05.05.2026    IGDAS FATURA            -   620,00 TL
07.05.2026    NETFLIX TR              -   169,99 TL
09.05.2026    MIGROS MARKET           -   890,00 TL
11.05.2026    UBER                    -   145,00 TL
12.05.2026    AKBANKA KIRA ODEMESI   - 4.500,00 TL
13.05.2026    YEMEGE CIKMA ODEMESI   -   380,00 TL   <- belirsiz
15.05.2026    XYZ TRANSFER            - 1.200,00 TL   <- belirsiz (confidence < 0.80)
16.05.2026    TURK TELEKOM            -   249,00 TL
18.05.2026    CARREFOURSA             -   560,00 TL
22.05.2026    SPOTIFY                 -    49,99 TL
24.05.2026    PHARMACY ECZANE         -   230,00 TL
```

**`backend/test_gemini.py`:**

```python
import asyncio
from app.services.gemini_service import extract_transactions_from_pdf

async def test():
    with open("demo_ekstre.pdf", "rb") as f:
        pdf_bytes = f.read()
    result = await extract_transactions_from_pdf(pdf_bytes)
    for tx in result["transactions"]:
        label = "ONAYLANDI" if tx["confidence"] >= 0.80 else "ONAY GEREKIR"
        print(f"{label} | {tx['date']} | {tx['description'][:30]:30} | {tx['amount']:10.2f} TL | {tx['estimated_category']} ({tx['confidence']:.2f})")

asyncio.run(test())
```

```bash
python backend/test_gemini.py
```

```bash
git add . && git commit -m "demo: add sample bank statement data and gemini test script"
```

---

### Adım 26 — Render Backend Deploy
**Süre:** ~30 dk

**Render.com dashboard:**

```
Service Type:   Web Service
Root Directory: backend
Build Command:  pip install -r requirements.txt
Start Command:  uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**

```env
APP_ENV              = production
FRONTEND_URL         = https://aliyda.netlify.app
SUPABASE_URL         = <supabase proje url>
SUPABASE_SERVICE_KEY = <service role key>
SUPABASE_JWT_SECRET  = <jwt secret>
GEMINI_API_KEY       = <gemini api key>
```

**Kontrol:**

```bash
curl https://aliyda-api.onrender.com/health
# Beklenen: {"status":"ok","env":"production"}
```

```bash
git add . && git commit -m "deploy: configure render backend deployment"
```

---

### Adım 27 — Netlify Frontend Deploy
**Süre:** ~30 dk

**`netlify.toml`:**

```toml
[build]
  base    = "frontend"
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from   = "/*"
  to     = "/index.html"
  status = 200
```

**`frontend/.env.production`:**

```env
VITE_SUPABASE_URL      = https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY = eyJhbGciOiJ...
VITE_API_URL           = https://aliyda-api.onrender.com
```

```bash
git add . && git commit -m "deploy: configure netlify frontend deployment"
```

---

### Adım 28 — Uctan Uca Test Checklist
**Süre:** ~45 dk

| # | Test | Beklenen | Durum |
|---|------|----------|-------|
| 1 | Yeni kullanici kayit | Dashboard'a yonlendirme | `[ ]` |
| 2 | Giris yap | Session aktif | `[ ]` |
| 3 | Demo PDF yukle | Status: processing | `[ ]` |
| 4 | Analiz tamamlandi | Verification Center'a yonlendirme | `[ ]` |
| 5 | Belirsiz islemi onayla, kategori degistir | is_verified=true, kural kaydedildi | `[ ]` |
| 6 | Toplu onay | Yuksek guvenilirlikli islemler onaylandi | `[ ]` |
| 7 | Dashboard'a git | Kartlar + grafik + saglik skoru | `[ ]` |
| 8 | AI Ozet | Gemini metni, yatirim tavsiyesi YOK | `[ ]` |
| 9 | Hedef ekle: 3 ayda 15.000 TL | Aylik birikim analizi | `[ ]` |
| 10 | Mobil gorunum | Tum ekranlar okunabilir | `[ ]` |

```bash
git add . && git commit -m "test: verify full pdf to insight end-to-end user flow"
git add . && git commit -m "docs: prepare final technical demo flow and presentation notes"
```

---

### Adım 29 — Sunum Hazırlığı

**Acilis cumlesi:**

> Ayse her ay maasini aliyor ama ay sonunda para nereye gitti diye soruyor. Banka uygulamasinda 200 islem satiri var, hangisini inceleyecegini bilmiyor. Aliyda'da ekstreyi yukluyor, 30 saniyede tum harcamalarini goruyor, finansal saglik skorunun 62 oldugunu fark ediyor ve yemek harcamalarini biraz kisarsa hedefe ulasabilecegini anlıyor.

**Juriye vurgulanacak 7 teknik karar:**

| # | Karar | Kriter |
|---|-------|--------|
| 1 | Gemini multimodal PDF okuma | Kullanici Degeri + Teknik |
| 2 | LangGraph agentic pipeline — state, retry, graph | Agentic Yapilar |
| 3 | Finansal hesap LLM'e yaptirilmiyor | Performans ve Dogruluk |
| 4 | AI ciktisi dogrulama katmanindan geciyor | Teknik Puan |
| 5 | Ogrenen kategori kurallari | Yenilikcilik |
| 6 | Finansal Saglik Skoru (0-100) | Kullanici Degeri + Ozgunluk |
| 7 | Yatirim tavsiyesi yok — etik sinir | Sunum ve Iletisim |

---

## Hızlı Başvuru

### Backend Komutları

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest tests/ -v
```

### Frontend Komutları

```bash
cd frontend
npm install
npm run dev      # localhost:5173
npm run build
npm run preview
```

### Supabase Kontrol Sorguları

```sql
-- RLS aktif tablolar
select tablename, rowsecurity from pg_tables where schemaname = 'public';

-- Bekleyen islemler
select count(*) from transactions where is_verified = false;

-- Kategori kurallari
select cr.keyword, c.name as category
from category_rules cr join categories c on cr.category_id = c.id;
```

### Kritik Dosya Yolları

| Dosya | Icerik |
|-------|--------|
| `backend/app/agents/graph.py` | LangGraph graph tanimı |
| `backend/app/agents/nodes.py` | Tum node implementasyonları |
| `backend/app/agents/state.py` | Paylasimli state type |
| `backend/app/services/gemini_service.py` | Gemini API + prompt |
| `backend/app/services/finance_summary_service.py` | Deterministik hesaplama |
| `backend/app/api/pdf.py` | PDF upload + background task |
| `frontend/src/pages/Dashboard.jsx` | Ana dashboard |
| `frontend/src/pages/VerificationCenter.jsx` | Onay ekrani |
| `frontend/src/services/apiClient.js` | Axios + auth interceptor |

---

> **Aliyda** — PDF'ten finansal icgoriye. Gemini okur, LangGraph yonetir, backend hesaplar, kullanici karar verir.
