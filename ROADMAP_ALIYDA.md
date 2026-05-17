# Aliyda Genel Proje Roadmap

Bu doküman, Aliyda projesinin yarışmaya hazır, güvenilir, sürdürülebilir ve teknik olarak anlatılabilir hale gelmesi için hazırlanmış yol haritasıdır.

Ana hedef:

> Kullanıcının doğrulanmış gelir-gider verilerine göre bütçe planlaması yapabilen, kullanıcının finansal durumuyla ilgili sorularına cevap verebilen kişisel bütçe chatbot'u geliştirmek.

Ekstra fark yaratan özellik:

> Kullanıcı banka ekstresini PDF olarak yükler. Gemini PDF'den işlemleri çıkarır. Kullanıcı tüm işlemleri doğrular. Sadece doğrulanmış veriler Supabase'e kaydedilir. Dashboard ve chatbot bu doğrulanmış veriler üzerinden çalışır.

---

## 1. Geliştirme Sırası Kararı

Önce backend'i sağlam bitirip, onu test edebilecek kadar minimum frontend yapmak; sonra tam frontend'e geçmek en doğru yaklaşımdır.

Neden?

- Bu projenin en riskli kısmı arayüz değil, veri akışıdır.
- PDF → Gemini → draft işlemler → kullanıcı onayı → transactions → summary → AI yorum → chatbot zinciri backend'de doğru çalışmalıdır.
- Frontend önce backend'i test edecek kadar sade olursa geliştirme daha hızlı ilerler.
- Backend sağlam olmadan güzel frontend yapmak, sonradan çok fazla düzeltme çıkarır.

Doğru sıra:

```text
Supabase hazırlandı
↓
Backend servisleri
↓
Backend endpointleri
↓
Backend testleri
↓
Minimal test frontend
↓
PDF doğrulama ekranı
↓
Dashboard
↓
Chatbot
↓
UI/UX polish
↓
Demo güvenliği
```

---

## 2. Projenin Ana Mimari Prensipleri

### 2.1. Supabase doğrulanmış veri kaynağıdır

Gemini'nin PDF'den çıkardığı veri doğrudan finansal gerçek kabul edilmez.

Doğru akış:

```text
PDF → Gemini extraction → transaction_drafts → kullanıcı doğrulaması → transactions
```

Manuel giriş akışı:

```text
Kullanıcı formu → backend validation → transactions
```

### 2.2. Matematik Gemini'ye bırakılmaz

Toplam gelir, toplam gider, kategori dağılımı, net bakiye, en büyük işlemler gibi hesaplamalar backend/Supabase tarafından yapılır.

Gemini'nin görevi:

```text
Doğal dil yorumlama
Finansal farkındalık önerisi
Chatbot cevabı üretme
```

### 2.3. Chatbot PDF'e değil DB'ye bakar

Chatbot her soruda PDF'i tekrar Gemini'ye göndermez. Bunun yerine:

```text
transactions
monthly_profiles
monthly_summaries
v_monthly_dashboard
```

üzerinden hazırlanmış context ile cevap üretir.

### 2.4. Kullanıcı her zaman veriyi düzeltebilir

Kullanıcı işlem geçmişinde şunları yapabilmelidir:

```text
Düzenle
Sil
Geri al
Kategori değiştir
Gelir/gider yönünü düzelt
```

Silme gerçek delete değil, soft delete olmalıdır:

```text
is_deleted = true
```

---

## 3. Supabase Durumu

Supabase tarafı kuruldu ve SQL dosyaları proje dizinine eklendi.

Konum:

```text
supabase/migrations/
supabase/seed/
```

Supabase detayları ayrıca şu dosyada açıklanmalıdır:

```text
SUPABASE.md
```

Kurulan ana tablolar:

```text
profiles
accounts
statements
statement_extractions
transaction_drafts
transactions
monthly_profiles
monthly_summaries
ai_insights
chat_sessions
chat_messages
category_rules
```

Kurulan ana view'lar:

```text
v_confirmed_transactions
v_pending_transaction_drafts
v_monthly_dashboard
```

Kurulan ana RPC fonksiyonları:

```text
create_user_account
create_statement
update_statement_status
save_statement_extraction
create_transaction_draft
approve_transaction_draft
reject_transaction_draft
create_manual_transaction
update_transaction_details
soft_delete_transaction
restore_transaction
soft_delete_statement
upsert_monthly_profile
recalculate_monthly_summary
```

---

# 4. Teknik Roadmap

## Aşama 1 — Proje Temizliği ve Standartlaştırma

### 1. Klasör yapısını netleştir

Önerilen yapı:

```text
backend/
  app/
    api/
    core/
    services/
    schemas/
    utils/
    tests/

frontend/
  src/
    components/
    pages/
    services/
    hooks/
    lib/
    types/

supabase/
  migrations/
  seed/

docs/
```

### 2. Environment dosyalarını ayır

Frontend `.env`:

```env
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_API_BASE_URL=
```

Backend `.env`:

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_ANON_KEY=
GEMINI_API_KEY=
GEMINI_MODEL_EXTRACTION=
GEMINI_MODEL_CHAT=
```

### 3. `.env.example` oluştur

Gerçek keyler asla repoya girmemelidir. Sadece örnek değişken isimleri yer almalıdır.

### 4. `.gitignore` kontrol et

Şunlar git'e girmemeli:

```text
.env
.env.local
*.local.sql
node_modules/
.venv/
__pycache__/
dist/
build/
uploads/
temp/
```

### 5. Mevcut eski kodu işaretle

Eski pipeline içinde kullanılmayacak, hatalı veya eski endpointler varsa silinmeden önce işaretlenmelidir.

Özellikle kontrol edilecekler:

```text
validation_node valid_transactions alanı
category_node eksik değişkenleri
tekrarlı Gemini insight çağrıları
PDF sonrası direkt DB write yapan eski kodlar
```

---

## Aşama 2 — Backend Core Altyapı

### 6. Backend config modülü yaz

Dosya:

```text
backend/app/core/config.py
```

İçermeli:

```text
Supabase URL
Supabase keys
Gemini key
Model isimleri
Upload limitleri
Environment bilgisi
```

### 7. Supabase client modülü yaz

Dosya:

```text
backend/app/core/supabase.py
```

İki mantık olabilir:

```text
service_role client
user scoped client/token doğrulama
```

### 8. Auth middleware yaz

Dosya:

```text
backend/app/core/auth.py
```

Görev:

```text
Authorization header oku
JWT doğrula
user_id çıkar
Endpointlere current_user_id ver
```

### 9. Standart API response yapısı oluştur

Başarılı response:

```json
{
  "success": true,
  "data": {},
  "message": null
}
```

Hata response:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Kullanıcıya gösterilecek mesaj"
  }
}
```

### 10. Pydantic schema dosyalarını oluştur

Klasör:

```text
backend/app/schemas/
```

Gerekli şemalar:

```text
AccountCreate
StatementCreate
PDFUploadResponse
TransactionDraftResponse
ApproveDraftRequest
RejectDraftRequest
ManualTransactionCreate
TransactionUpdateRequest
MonthlyProfileUpsert
MonthlyDashboardResponse
InsightResponse
ChatRequest
ChatResponse
```

---

## Aşama 3 — Backend Servis Katmanı

### 11. Account service yaz

Dosya:

```text
backend/app/services/account_service.py
```

Fonksiyonlar:

```text
create_account
list_accounts
update_account
archive_account
```

Supabase RPC:

```text
create_user_account()
```

### 12. Statement service yaz

Dosya:

```text
backend/app/services/statement_service.py
```

Fonksiyonlar:

```text
create_statement
update_statement_status
list_statements_by_month
soft_delete_statement
```

### 13. Statement extraction service yaz

Dosya:

```text
backend/app/services/extraction_service.py
```

Görev:

```text
Gemini'den gelen raw/parsed çıktıyı statement_extractions tablosuna kaydetmek
```

RPC:

```text
save_statement_extraction()
```

### 14. Draft service yaz

Dosya:

```text
backend/app/services/draft_service.py
```

Fonksiyonlar:

```text
create_drafts_from_extraction
list_pending_drafts
approve_draft
reject_draft
approve_all_safe_drafts
```

### 15. Transaction service yaz

Dosya:

```text
backend/app/services/transaction_service.py
```

Fonksiyonlar:

```text
create_manual_transaction
list_transactions
update_transaction
soft_delete_transaction
restore_transaction
```

### 16. Monthly profile service yaz

Dosya:

```text
backend/app/services/monthly_profile_service.py
```

Fonksiyonlar:

```text
upsert_monthly_profile
get_monthly_profile
finalize_month_profile
```

### 17. Summary service yaz

Dosya:

```text
backend/app/services/summary_service.py
```

Fonksiyonlar:

```text
recalculate_monthly_summary
get_monthly_dashboard
ensure_summary_fresh
```

### 18. Insight service yaz

Dosya:

```text
backend/app/services/insight_service.py
```

Görev:

```text
monthly_summaries verisini Gemini'ye vererek doğal dil yorumu oluşturmak
ai_insights tablosuna kaydetmek
stale insight kontrolü yapmak
```

### 19. Chat service yaz

Dosya:

```text
backend/app/services/chat_service.py
```

Görev:

```text
chat session oluşturmak
chat message kaydetmek
DB context hazırlamak
Gemini cevabı üretmek
cevabı kaydetmek
```

---

## Aşama 4 — Gemini PDF Extraction

### 20. Gemini service modülü oluştur

Dosya:

```text
backend/app/services/gemini_service.py
```

Fonksiyonlar:

```text
extract_transactions_from_pdf
generate_monthly_insight
answer_chat_question
```

Bu üç fonksiyon farklı promptlarla çalışmalıdır.

### 21. PDF extraction promptunu netleştir

PDF aşamasında Gemini sadece veri çıkarmalıdır. Yorum yapmamalıdır.

Çıktı formatı:

```json
{
  "statement_month": "YYYY-MM",
  "income_detected": true,
  "transactions": [
    {
      "transaction_date": "YYYY-MM-DD",
      "transaction_time": "HH:mm",
      "description": "...",
      "original_description": "...",
      "amount": 100.50,
      "currency": "TRY",
      "direction": "expense",
      "category": "Market",
      "subcategory": null,
      "counterparty": "Migros",
      "confidence": 0.91,
      "raw_text": "..."
    }
  ],
  "warnings": []
}
```

### 22. Tek PDF için tek extraction isteği kuralını uygula

Yapılmayacaklar:

```text
Her sayfa için ayrı Gemini isteği
Her işlem için ayrı kategori isteği
PDF sonrası hemen ayrı insight isteği
```

Doğru akış:

```text
PDF → 1 Gemini extraction → transaction_drafts
```

### 23. Gemini çıktısını validate et

Kontrol edilecekler:

```text
amount boş mu?
date boş mu?
direction geçerli mi?
confidence var mı?
currency yoksa TRY yapılmalı mı?
category boşsa Diğer mi olmalı?
```

Eksik veri varsa draft yine oluşturulabilir ama `needs_review=true` olmalıdır.

### 24. Gemini sonucunu statement_extractions tablosuna kaydet

Her extraction denemesi kaydedilmelidir:

```text
raw_output
parsed_output
model
prompt_version
status
error_message
```

### 25. Transaction draft kayıtlarını oluştur

Gemini transactions listesi için her item:

```text
create_transaction_draft()
```

ile DB'ye yazılmalıdır.

### 26. Statement status akışını bağla

Durum sırası:

```text
uploaded
extracting
extracted
pending_review
saved
failed
```

Başarısız olursa:

```text
status = failed
error_message dolu
```

---

## Aşama 5 — Backend API Endpointleri

### 27. Account endpointleri

```text
GET    /api/v1/accounts
POST   /api/v1/accounts
PATCH  /api/v1/accounts/{account_id}
DELETE /api/v1/accounts/{account_id}
```

### 28. PDF upload endpointi

```text
POST /api/v1/statements/upload
```

Görev:

```text
PDF dosyasını al
statement oluştur
Gemini extraction başlat
draft kayıtlarını oluştur
pending_review dön
```

### 29. Statement liste endpointi

```text
GET /api/v1/statements?month=YYYY-MM
```

Bir ayda kaç PDF/manual batch var gösterir.

### 30. Pending draft endpointi

```text
GET /api/v1/statements/{statement_id}/drafts
```

PDF doğrulama ekranını besler.

### 31. Draft approve endpointi

```text
POST /api/v1/drafts/{draft_id}/approve
```

Backend:

```text
approve_transaction_draft()
recalculate_monthly_summary(month)
```

### 32. Draft reject endpointi

```text
POST /api/v1/drafts/{draft_id}/reject
```

Backend:

```text
reject_transaction_draft()
```

### 33. Statement finalize endpointi

```text
POST /api/v1/statements/{statement_id}/finalize
```

Kontrol:

```text
Pending draft kaldı mı?
Gelir tespit edildi mi?
Gelir yoksa monthly profile var mı?
Summary hesaplandı mı?
```

### 34. Manuel transaction endpointi

```text
POST /api/v1/transactions/manual
```

Backend:

```text
create_manual_transaction()
recalculate_monthly_summary(month)
```

### 35. Transaction liste endpointi

```text
GET /api/v1/transactions?month=YYYY-MM
```

Kaynak:

```text
v_confirmed_transactions
```

### 36. Transaction update endpointi

```text
PATCH /api/v1/transactions/{transaction_id}
```

Eğer tarih değişip ay değişirse eski ve yeni ay summary'leri güncellenmelidir.

### 37. Transaction soft delete endpointi

```text
DELETE /api/v1/transactions/{transaction_id}
```

Backend:

```text
soft_delete_transaction()
recalculate_monthly_summary(month)
```

### 38. Transaction restore endpointi

```text
POST /api/v1/transactions/{transaction_id}/restore
```

### 39. Monthly profile endpointi

```text
PUT /api/v1/monthly-profile/{month}
```

Gelir yoksa kullanıcıdan alınan gelir buradan kaydedilir.

### 40. Dashboard endpointi

```text
GET /api/v1/dashboard?month=YYYY-MM
```

Backend:

```text
ensure_summary_fresh()
v_monthly_dashboard sorgula
recent transactions ekle
ai insight ekle
```

### 41. AI insight endpointi

```text
POST /api/v1/insights/monthly
```

Gemini'ye yalnızca summary/context gönderilir.

### 42. Chat endpointleri

```text
POST /api/v1/chat/sessions
GET  /api/v1/chat/sessions
GET  /api/v1/chat/sessions/{session_id}/messages
POST /api/v1/chat
```

---

## Aşama 6 — Chatbot Tasarımı

### 43. Chat context builder yaz

Dosya:

```text
backend/app/services/chat_context_service.py
```

Sorulara göre context seçmelidir.

Örnek:

```text
"Bu ay en çok nereye harcamışım?" → top_categories
"En büyük harcamalarım neler?" → largest_transactions
"Ay sonunda ne kadar kalır?" → total_income, total_expense, net_balance
```

### 44. Chatbot promptunu güvenli hale getir

Prompt kuralları:

```text
Sadece verilen doğrulanmış veriye dayan.
Uydurma işlem veya tutar söyleme.
Finansal yatırım tavsiyesi verme.
Kullanıcıya bütçe farkındalığı ve tasarruf önerisi sun.
Eksik veri varsa bunu açıkça söyle.
```

### 45. Chat messages kaydını yap

Her konuşmada:

```text
user message kaydet
context_snapshot kaydet
assistant answer kaydet
```

Bu debug için önemlidir.

---

## Aşama 7 — Minimal Frontend

### 46. Login/Register ekranını çalıştır

Önce auth kesin çalışmalı.

Gerekli ekranlar:

```text
Register
Login
Logout
Session persistence
```

### 47. Backend token gönderimini bağla

Frontend her backend isteğinde Supabase access token göndermelidir:

```text
Authorization: Bearer <access_token>
```

### 48. Account test ekranı yap

Sade ekran yeterlidir:

```text
Hesap oluştur
Hesapları listele
```

### 49. Manuel işlem ekleme ekranı yap

Alanlar:

```text
Tarih
Saat
Açıklama
Tutar
Gelir/Gider/Transfer
Kategori
Karşı taraf
Hesap
```

Bu akış PDF'ten önce tamamen çalışmalıdır.

### 50. İşlemlerim ekranını yap

Kaynak:

```text
GET /transactions?month=YYYY-MM
```

Özellikler:

```text
Listele
Düzenle
Sil
Geri al
Filtrele
```

### 51. Minimal dashboard yap

Gösterilecekler:

```text
Toplam gelir
Toplam gider
Net bakiye
En yüksek kategoriler
En büyük işlemler
Gelir eksik uyarısı
AI yorum alanı
```

---

## Aşama 8 — PDF Frontend

### 52. PDF upload ekranı yap

Alanlar:

```text
Ay seç
Hesap seç
PDF seç
Yükle
```

### 53. PDF durum ekranı yap

Statement status göster:

```text
uploaded
extracting
pending_review
failed
saved
```

### 54. PDF doğrulama ekranı yap

Kaynak:

```text
v_pending_transaction_drafts
```

Her satırda:

```text
Tarih
Saat
Açıklama
Tutar
Yön
Kategori
Karşı taraf
Confidence
Onayla
Reddet
Düzenle ve onayla
```

### 55. Gelir yoksa gelir ekranı göster

PDF gelir içermiyorsa:

```text
Bu ekstrede gelir bilgisi bulunamadı.
Aylık gelirini gir.
```

Kaydetme:

```text
upsert_monthly_profile()
```

### 56. Çoklu PDF akışını destekle

Kullanıcı aynı ay için birden çok PDF ekleyebilir.

Kural:

```text
Tüm PDF'ler ve doğrulamalar bitmeden nihai yorum/chatbot aşamasına geçilmez.
```

---

## Aşama 9 — Dashboard ve Insight

### 57. Dashboard grafiklerini ekle

Grafikler:

```text
Kategori bazlı gider dağılımı
Gelir-gider karşılaştırması
Günlük harcama trendi
En büyük işlemler
Hesap bazlı dağılım
```

### 58. AI insight üretimini kontrollü yap

Her dashboard açıldığında Gemini çağırma.

Doğru akış:

```text
Önce eski insight var mı bak
is_stale=false ise göster
stale ise kullanıcıya "Yorumu yenile" butonu göster
```

### 59. Veri değişince eski yorumu stale kabul et

Transaction eklendi/silindi/düzenlendiğinde:

```text
monthly_summaries stale
ai_insights stale
```

Bu altyapı Supabase'de kuruldu.

---

## Aşama 10 — Chatbot Frontend

### 60. Chat UI oluştur

Alanlar:

```text
Mesaj listesi
Input
Gönder butonu
Ay seçici
Önerilen sorular
```

### 61. Önerilen soruları ekle

```text
Bu ay en çok nereye harcamışım?
Nereden tasarruf edebilirim?
Ay sonunda ne kadar kalır?
En büyük harcamalarım neler?
Yemek harcamam fazla mı?
```

### 62. Veri yoksa yönlendirme yap

Eğer ilgili ayda veri yoksa:

```text
Bu ay için henüz veri yok. Manuel işlem ekleyebilir veya PDF yükleyebilirsin.
```

---

## Aşama 11 — Test Planı

### 63. Backend unit testleri

Test edilecekler:

```text
account create
manual transaction create
transaction update
soft delete
restore
monthly profile upsert
summary recalculation
draft approve
draft reject
```

### 64. Backend integration testleri

Akışlar:

```text
Manuel gelir/gider → summary → dashboard
PDF statement → draft → approve → transaction → summary
Gelir yok → monthly_profile → summary
Transaction sil → summary stale → recalculate
Chat question → context → Gemini response
```

### 65. Frontend manuel akış testi

```text
Login
Hesap oluştur
Gelir ekle
Gider ekle
Dashboard kontrol
Chatbot soru sor
İşlem düzenle/sil
Dashboard güncelle
```

### 66. Frontend PDF akış testi

```text
PDF yükle
Draftlar oluştu mu
Draft onayla
Draft reddet
Gelir yoksa gelir gir
Ayı finalize et
Dashboard kontrol
Chatbot kontrol
```

### 67. RLS güvenlik testi

İki kullanıcı ile test:

```text
Kullanıcı A, B'nin verisini görememeli.
Kullanıcı B, A'nın transaction_id'sini bilse bile işlem yapamamalı.
```

### 68. Gemini hata testi

Test:

```text
Gemini timeout
Gemini invalid JSON
Gemini quota error
PDF okunamadı
```

Her durumda statement status doğru güncellenmelidir.

---

## Aşama 12 — Demo Güvenliği

### 69. Demo seed hazırla

Gerçek banka verisi kullanmadan demo verisi oluştur.

Örnek:

```text
Gelir: 25.000 TL
Gider: 9.570 TL
En yüksek gider: Kira
Kategoriler: Market, Yemek, Ulaşım, Alışveriş
```

### 70. Demo PDF fallback hazırla

Canlı PDF extraction patlarsa demo bozulmamalı.

Plan:

```text
Canlı PDF çalışırsa göster
Çalışmazsa demo PDF/demo extraction kullan
Doğrulama ekranı ve chatbot yine gösterilebilir olsun
```

### 71. Sunum anlatımını hazırla

Anlatım:

```text
Problem: Kullanıcı finansal verisini anlamakta zorlanıyor.
Çözüm: Aliyda doğrulanmış verilerle bütçe asistanı sunuyor.
Fark: PDF ekstre okuma + kullanıcı doğrulaması + chatbot.
Güven: AI çıktısı doğrudan gerçek sayılmıyor.
Teknik: Supabase source of truth, Gemini yorum katmanı.
```

---

## Aşama 13 — Son Temizlik

### 72. README güncelle

Ana README şunları içermeli:

```text
Proje amacı
Teknoloji stack
Kurulum
Environment değişkenleri
Supabase kurulumu
Backend çalıştırma
Frontend çalıştırma
Demo akışı
```

### 73. SUPABASE.md ve ROADMAP.md linkle

README içinden şu dosyalara link ver:

```text
SUPABASE.md
ROADMAP.md
```

### 74. Loglama ekle

Backend logları:

```text
PDF upload başladı
Gemini extraction başladı/bitti
Draft sayısı
Onaylanan draft sayısı
Summary recalculated
Insight generated
Chat answer generated
```

Hassas veri loglanmamalıdır.

### 75. Final demo checklist oluştur

```text
Supabase çalışıyor
Backend çalışıyor
Frontend çalışıyor
Login çalışıyor
Manuel işlem çalışıyor
PDF upload çalışıyor
Draft approval çalışıyor
Dashboard doğru
AI insight doğru
Chatbot doğru
Soft delete çalışıyor
Demo fallback hazır
```

---

# Önceliklendirilmiş Sprint Sırası

Gerçek çalışma sırası:

```text
1. Backend auth + Supabase client
2. Account endpointleri
3. Manuel transaction endpointleri
4. Monthly profile + summary endpointleri
5. Minimal frontend: login + manual transaction + dashboard
6. PDF upload backend
7. Gemini extraction
8. Draft review backend
9. Draft review frontend
10. Insight generation
11. Chatbot backend
12. Chatbot frontend
13. Transaction edit/delete/restore
14. Multi-PDF monthly finalize flow
15. UI polish
16. Test + demo fallback
```

---

# Kritik Başarı Senaryoları

## Senaryo 1 — Manuel kullanıcı

```text
Kullanıcı kayıt olur.
Gelirini girer.
Giderlerini manuel ekler.
Dashboard görür.
Chatbot'a "Bu ay en çok nereye harcadım?" diye sorar.
Doğru cevap alır.
```

## Senaryo 2 — PDF kullanıcı

```text
Kullanıcı PDF yükler.
Gemini işlemleri çıkarır.
Kullanıcı tüm işlemleri doğrular.
Gelir yoksa manuel gelir girer.
Veriler DB'ye kaydolur.
Dashboard güncellenir.
Gemini aylık yorum üretir.
Chatbot doğrulanmış verilere göre cevap verir.
```

## Senaryo 3 — Hata düzeltme

```text
Kullanıcı yanlış işlem fark eder.
İşlemlerim ekranından düzenler veya siler.
Summary yeniden hesaplanır.
Eski AI insight stale olur.
Kullanıcı yeni yorum ister.
Chatbot yeni veriye göre cevap verir.
```

## Senaryo 4 — Çoklu PDF

```text
Kullanıcı aynı ay için birden fazla PDF yükler.
Her PDF ayrı statement olur.
Her PDF'in draftları ayrı doğrulanır.
Hepsi aynı ay summary'sinde birleşir.
Dashboard ve chatbot birleşik ay verisini kullanır.
```

---

# Final Ürün Tanımı

Aliyda'nın doğru konumlandırması:

```text
Ana ürün:
Doğrulanmış gelir-gider verisine dayalı kişisel bütçe chatbot'u.

Fark yaratan özellik:
PDF banka ekstresi okuyarak işlemleri otomatik başlatma.

Güven katmanı:
AI çıktıları kullanıcı doğrulamasından geçmeden finansal gerçek sayılmaz.

Teknik temel:
Supabase doğrulanmış veri kaynağıdır.
Backend hesaplama ve akış yönetimidir.
Gemini yorumlama ve sohbet katmanıdır.
Frontend doğrulama, dashboard ve chatbot deneyimidir.
```

Bu yol haritası tamamlandığında proje sadece çalışan bir demo değil; teknik olarak güçlü, savunulabilir, geliştirilebilir ve yarışmada anlatılabilir bir ürün haline gelir.
