# Aliyda Supabase Kurulum ve Mimari Dokümantasyonu

Bu doküman, Aliyda projesinde Supabase tarafında kurulan veritabanı mimarisini, güvenlik yapısını, iş akışlarını ve proje dizinine eklenen SQL dosyalarının ne işe yaradığını açıklar.

Aliyda'nın temel hedefi, kullanıcının manuel olarak girdiği veya banka PDF ekstresinden çıkartılıp kullanıcı tarafından onaylanan finansal veriler üzerinden bütçe analizi ve chatbot deneyimi sunmaktır. Bu yüzden Supabase yapısı sadece tablo saklayan basit bir yapı olarak değil; PDF doğrulama, manuel giriş, aylık özet, AI yorumları, chatbot geçmişi ve kullanıcı güvenliği dahil olacak şekilde tasarlanmıştır.

---

## 1. Genel Mimari Kararı

Aliyda'da finansal verinin tek gerçek kaynağı Supabase'de kullanıcı tarafından onaylanmış verilerdir.

Ana prensip:

```text
PDF / Manuel Giriş
→ Kullanıcı doğrulaması
→ Supabase transactions tablosu
→ Backend deterministic hesaplama
→ Gemini doğal dil yorumlama / chatbot
```

Burada Gemini doğrudan finansal gerçek kabul edilmez. Gemini'nin görevi:

```text
1. PDF'den yapılandırılmış veri çıkarmak
2. DB'deki doğrulanmış özetlere göre yorum üretmek
3. Chatbot cevaplarını doğal dille oluşturmak
```

Toplam gelir, toplam gider, kategori toplamı, net bakiye gibi matematiksel hesaplar Gemini'ye bırakılmaz. Bunlar backend ve Supabase verisi üzerinden deterministik hesaplanır.

---

## 2. SQL Dosyalarının Projedeki Yeri

Supabase için yazılan SQL dosyaları proje içinde şu klasör altında tutulur:

```text
supabase/
  migrations/
  seed/
```

`migrations/` klasörü gerçek veritabanı kurulum dosyalarını içerir. Bu dosyalar sırayla çalıştırılarak Aliyda'nın Supabase yapısı baştan kurulabilir.

`seed/` klasörü test ve örnek veri dosyalarını içerir. Bu dosyalar production kurulumunun parçası değildir; yalnızca doğrulama ve demo için kullanılır.

Gerçek Supabase kullanıcı ID'si içeren lokal test dosyaları repoya eklenmemelidir. Seed dosyaları `.example.sql` formatında tutulmalıdır.

---

## 3. Mevcut Supabase Projesi Nasıl Kullanıldı?

Yeni Supabase projesi açmak yerine mevcut Aliyda Supabase projesi korunmuştur.

Bu sayede şu bilgiler değişmeden kalır:

```text
- Supabase Project URL
- Publishable / anon key
- Secret / service role key
- Auth ayarları
- Project ref
```

Sadece `public` schema temizlenmiş ve Aliyda için yeniden kurulmuştur. Auth, storage, realtime ve Supabase internal schema'larına dokunulmamıştır.

Önemli not: Daha önce secret/service key paylaşılmışsa canlıya çıkmadan önce Supabase panelinden rotate edilmesi önerilir. Bu key frontend tarafına konulmamalıdır.

---

## 4. Kurulan Ana Tablolar

Aşağıdaki tablolar Supabase üzerinde oluşturulmuştur.

### 4.1 `profiles`

Her Supabase Auth kullanıcısı için bir profil kaydı tutar.

Tutulan temel alanlar:

```text
- id
- email
- full_name
- avatar_url
- preferred_currency
- onboarding_completed
```

Kullanıcı kayıt olduğunda `auth.users` üzerinden otomatik profile oluşturulması için trigger yapısı kurulmuştur.

İlgili dosyalar:

```text
supabase/migrations/001_helper_functions.sql
supabase/migrations/002_profiles.sql
```

---

### 4.2 `accounts`

Kullanıcının banka hesabı, kredi kartı, nakit hesabı, cüzdanı veya manuel giriş hesabını temsil eder.

Örnek hesaplar:

```text
- Ziraat Vadesiz
- Enpara Kredi Kartı
- Nakit
- Manuel Giriş
- Papara
```

Bir kullanıcının birden fazla hesabı olabilir. Aynı ayda birden fazla PDF bu hesaplara bağlanabilir.

İlgili dosya:

```text
supabase/migrations/003_accounts.sql
```

---

### 4.3 `statements`

Her PDF yüklemesini veya manuel aylık veri setini temsil eder.

Örnek:

```text
Mayıs 2026 Ziraat PDF
Mayıs 2026 Enpara PDF
Mayıs 2026 Manuel Veri Girişi
```

Durum takibi için `status` alanı vardır:

```text
uploaded
extracting
extracted
pending_review
approved
saved
failed
cancelled
deleted
```

Ayrıca `is_deleted`, `deleted_at`, `deleted_reason` alanlarıyla soft delete desteklenir.

İlgili dosya:

```text
supabase/migrations/004_statements.sql
```

---

### 4.4 `statement_extractions`

Gemini'nin PDF'den çıkardığı ham ve parse edilmiş çıktıyı saklar.

Bu tablo final finansal veri değildir. Debug ve izlenebilirlik için kullanılır.

Tutulan bilgiler:

```text
- provider
- model
- prompt_version
- raw_output
- parsed_output
- request_count
- token tahminleri
- status
- error_message
```

İlgili dosya:

```text
supabase/migrations/005_statement_extractions.sql
```

---

### 4.5 `transaction_drafts`

PDF'den Gemini ile çıkarılmış fakat henüz kullanıcı tarafından onaylanmamış işlemleri tutar.

Bu tablo Aliyda'nın güvenli AI doğrulama akışının temelidir.

Akış:

```text
PDF → Gemini extraction → transaction_drafts → kullanıcı onayı → transactions
```

Kullanıcı onay ekranında bu tablodaki verileri görür:

```text
- tarih
- saat
- açıklama
- tutar
- gelir/gider/transfer yönü
- kategori
- alt kategori
- karşı taraf
- Gemini güven skoru
```

Kullanıcı işlemi onaylayabilir, düzenleyip onaylayabilir veya reddedebilir.

İlgili dosya:

```text
supabase/migrations/006_transaction_drafts.sql
```

---

### 4.6 `transactions`

Aliyda'nın asıl finansal veri kaynağıdır.

Bu tablo yalnızca kullanıcı tarafından onaylanmış veya manuel girilmiş kesin işlemleri tutar.

Kaynaklar:

```text
PDF'den gelen işlem:
transaction_drafts → kullanıcı onayı → transactions

Manuel işlem:
frontend form → backend validation → transactions
```

Dashboard, grafikler, aylık özetler, Gemini yorumları ve chatbot bu tabloyu kaynak alır.

Önemli alanlar:

```text
- user_id
- account_id
- statement_id
- draft_id
- month
- transaction_date
- transaction_time
- description
- amount
- direction
- category
- subcategory
- counterparty
- source
- is_user_confirmed
- is_deleted
```

`month` alanı doğrudan tutulur. Böylece ay bazlı sorgular hızlı ve basit yapılır.

Silme işlemi hard delete ile değil soft delete ile yapılır:

```text
is_deleted = true
deleted_at = now()
deleted_reason = açıklama
```

İlgili dosya:

```text
supabase/migrations/007_transactions.sql
```

---

### 4.7 `monthly_profiles`

Kullanıcının aylık gelir ve hedef bilgilerini tutar.

Bu tablo özellikle PDF gelir bilgisi içermediğinde kullanılır.

Örnek:

```text
month: 2026-05
declared_income: 25000
income_source: manual
savings_goal: 5000
budget_goal: 18000
```

Ekstrede gelir yoksa kullanıcıdan manuel gelir alınır ve buraya kaydedilir.

İlgili dosya:

```text
supabase/migrations/008_monthly_profiles.sql
```

---

### 4.8 `monthly_summaries`

Backend tarafından hesaplanan aylık finansal özetleri saklar.

Gemini'nin tüm transaction listesini tekrar tekrar okuması yerine bu özetler kullanılır.

Tutulan bilgiler:

```text
- detected_income
- declared_income
- income_basis
- total_income
- total_expense
- total_transfer_in
- total_transfer_out
- net_balance
- transaction_count
- income_count
- expense_count
- top_categories
- largest_transactions
- recurring_candidates
- is_stale
- calculated_at
```

`is_stale` alanı veri değiştiğinde eski özetin güncellenmesi gerektiğini belirtir.

İlgili dosyalar:

```text
supabase/migrations/009_monthly_summaries.sql
supabase/migrations/018_monthly_summary_income_fields.sql
supabase/migrations/019_recalculate_monthly_summary_function.sql
```

---

### 4.9 `ai_insights`

Gemini'nin DB özetine göre ürettiği doğal dil yorumları saklanır.

Örnek kullanım:

```text
- aylık dashboard yorumu
- tasarruf önerisi
- uyarı
- chatbot context özeti
```

Veri değiştiğinde eski insight'lar `is_stale = true` yapılabilir.

İlgili dosya:

```text
supabase/migrations/010_ai_insights.sql
```

---

### 4.10 `chat_sessions` ve `chat_messages`

Chatbot konuşmalarını saklar.

`chat_sessions` konuşma oturumunu, `chat_messages` ise kullanıcı ve asistan mesajlarını tutar.

Her mesaj için istenirse o cevabı üretirken kullanılan context snapshot da saklanabilir.

İlgili dosya:

```text
supabase/migrations/011_chat_sessions_and_messages.sql
```

---

### 4.11 `category_rules`

Kullanıcının kategori düzeltmelerinden öğrenilecek kuralları tutar.

Örnek:

```text
MIGROS → Market
BİM → Market
YEMEKSEPETİ → Yemek
UBER → Ulaşım
```

Bu tablo sonraki PDF'lerde kategori tahminlerini iyileştirmek için kullanılabilir.

İlgili dosya:

```text
supabase/migrations/012_category_rules.sql
```

---

## 5. Row Level Security Yapısı

Tüm kullanıcı verisi içeren tablolarda RLS açılmıştır.

Amaç:

```text
Her kullanıcı yalnızca kendi verisini görebilir ve yönetebilir.
```

Temel policy mantığı:

```sql
auth.uid() = user_id
```

`profiles` tablosunda ise:

```sql
auth.uid() = id
```

RLS açılan tablolar:

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

İlgili dosyalar:

```text
supabase/migrations/013_enable_rls.sql
supabase/migrations/014_profiles_policies.sql
supabase/migrations/015_user_owned_table_policies.sql
```

---

## 6. View Yapısı

Frontend ve backend karmaşık join sorguları yazmadan temiz veri alabilsin diye view'lar oluşturulmuştur.

### 6.1 `v_confirmed_transactions`

Geçmiş işlemler ekranı için kullanılır.

Yalnızca şu işlemleri gösterir:

```text
is_user_confirmed = true
is_deleted = false
```

Bu view üzerinden kullanıcı geçmiş işlemlerini görebilir.

İlgili dosyalar:

```text
supabase/migrations/016_initial_confirmed_transactions_view.sql
supabase/migrations/023_secure_transaction_views.sql
```

---

### 6.2 `v_pending_transaction_drafts`

PDF sonrası onaylama ekranı için kullanılır.

Yalnızca `review_status = 'pending'` olan draft işlemleri gösterir.

Bu ekranda kullanıcı Gemini'nin çıkardığı işlemleri kontrol eder.

İlgili dosya:

```text
supabase/migrations/023_secure_transaction_views.sql
```

---

### 6.3 `v_monthly_dashboard`

Dashboard ekranı için aylık özet ve aylık profil bilgilerini birleştirir.

Gösterilebilecek alanlar:

```text
- toplam gelir
- toplam gider
- net bakiye
- en yüksek kategoriler
- en büyük işlemler
- tasarruf hedefi
- bütçe hedefi
- özet stale mi?
```

İlgili dosya:

```text
supabase/migrations/028_monthly_dashboard_view.sql
```

---

## 7. RPC / Database Function Yapısı

Backend ve frontend bazı işlemleri doğrudan güvenli database function'ları üzerinden yapabilir.

Bu fonksiyonlar iş kurallarını merkezi hale getirir.

### 7.1 Hesap oluşturma

```text
create_user_account()
```

Kullanıcı için banka, kredi kartı, nakit veya manuel hesap oluşturur.

İlgili dosya:

```text
supabase/migrations/029_create_user_account_function.sql
```

---

### 7.2 Aylık profil / gelir kaydetme

```text
upsert_monthly_profile()
```

Kullanıcının aylık gelirini, tasarruf hedefini ve bütçe hedefini kaydeder.

İlgili dosya:

```text
supabase/migrations/030_upsert_monthly_profile_function.sql
```

---

### 7.3 Statement oluşturma

```text
create_statement()
```

PDF yüklemesi veya manuel aylık veri girişi için statement kaydı oluşturur.

İlgili dosya:

```text
supabase/migrations/031_create_statement_function.sql
```

---

### 7.4 Statement durum güncelleme

```text
update_statement_status()
```

PDF işleme durumunu günceller.

Örnek durumlar:

```text
uploaded
extracting
extracted
pending_review
approved
saved
failed
cancelled
deleted
```

İlgili dosya:

```text
supabase/migrations/032_update_statement_status_function.sql
```

---

### 7.5 Transaction draft oluşturma

```text
create_transaction_draft()
```

Gemini PDF'den işlem çıkardıktan sonra onay bekleyen draft kaydı oluşturur.

İlgili dosya:

```text
supabase/migrations/033_create_transaction_draft_function.sql
```

---

### 7.6 Gemini extraction kaydetme

```text
save_statement_extraction()
```

Gemini'nin PDF için döndürdüğü ham ve parse edilmiş çıktıyı saklar.

İlgili dosya:

```text
supabase/migrations/034_save_statement_extraction_function.sql
```

---

### 7.7 Draft onaylama

```text
approve_transaction_draft()
```

Kullanıcının onayladığı veya düzenleyip onayladığı draft işlemi `transactions` tablosuna aktarır.

İlgili dosya:

```text
supabase/migrations/024_approve_transaction_draft_function.sql
```

---

### 7.8 Draft reddetme

```text
reject_transaction_draft()
```

Kullanıcının yanlış veya gereksiz bulduğu draft işlemi reddeder.

İlgili dosya:

```text
supabase/migrations/025_reject_transaction_draft_function.sql
```

---

### 7.9 Manuel işlem oluşturma

```text
create_manual_transaction()
```

Kullanıcının siteden manuel gelir, gider veya transfer eklemesini sağlar.

Bu işlem doğrudan `transactions` tablosuna gider çünkü kullanıcı veriyi kendisi girmiştir.

İlgili dosya:

```text
supabase/migrations/026_create_manual_transaction_function.sql
```

---

### 7.10 İşlem güncelleme

```text
update_transaction_details()
```

Kullanıcı geçmiş işlemler ekranından bir işlemi sonradan düzeltebilir.

Düzenlenebilecek alanlar:

```text
- tarih
- saat
- açıklama
- tutar
- yön
- kategori
- alt kategori
- karşı taraf
- ödeme yöntemi
- konum
- bütçeden hariç mi?
```

İlgili dosya:

```text
supabase/migrations/027_update_transaction_details_function.sql
```

---

### 7.11 Soft delete / restore

```text
soft_delete_transaction()
restore_transaction()
soft_delete_statement()
```

Kullanıcı işlem veya PDF'i sonradan silebilir. Silinen veriler hard delete yapılmaz, soft delete ile işaretlenir.

İlgili dosya:

```text
supabase/migrations/017_soft_delete_functions.sql
```

---

### 7.12 Aylık özet hesaplama

```text
recalculate_monthly_summary()
```

Kullanıcının belirli bir ay için gelir/gider toplamlarını, net bakiyesini, en yüksek kategorilerini ve en büyük işlemlerini hesaplar.

Backend bu fonksiyonu veri değişikliklerinden sonra çağırabilir.

İlgili dosya:

```text
supabase/migrations/019_recalculate_monthly_summary_function.sql
```

---

## 8. Stale / Yeniden Hesaplama Mantığı

Kullanıcı bir transaction ekler, siler veya düzenlerse aylık özet ve AI yorumları eski kabul edilir.

Bunun için şu yapılar kuruldu:

```text
mark_month_as_stale()
transactions_mark_summary_stale trigger
monthly_profiles_mark_summary_stale trigger
```

İlgili dosyalar:

```text
supabase/migrations/020_mark_month_as_stale_function.sql
supabase/migrations/021_transactions_stale_trigger.sql
supabase/migrations/022_monthly_profiles_stale_trigger.sql
```

Beklenen akış:

```text
Kullanıcı işlem ekler/siler/düzenler
→ monthly_summaries.is_stale = true
→ ai_insights.is_stale = true
→ backend summary'yi yeniden hesaplar
→ kullanıcı isterse Gemini yorumu yenilenir
```

Her küçük değişiklikte Gemini'ye otomatik istek atmak yerine, önce summary güncellenir. Gemini yorumu gerektiğinde yenilenir.

---

## 9. PDF İş Akışı

PDF akışı şu şekilde tasarlanmıştır:

```text
1. Kullanıcı PDF yükler
2. Backend create_statement() ile statement oluşturur
3. Statement status = extracting yapılır
4. Backend PDF'i Gemini'ye tek istekle gönderir
5. Gemini yapılandırılmış transaction listesi döndürür
6. Backend save_statement_extraction() ile Gemini çıktısını kaydeder
7. Backend her işlem için create_transaction_draft() çağırır
8. Statement status = pending_review yapılır
9. Kullanıcı v_pending_transaction_drafts üzerinden işlemleri görür
10. Kullanıcı her işlemi onaylar, düzenler veya reddeder
11. Onaylanan işlemler approve_transaction_draft() ile transactions tablosuna geçer
12. Kullanıcı tüm PDF'leri ve gelir bilgisini tamamlayınca dashboard aşamasına geçilir
13. Backend recalculate_monthly_summary() çağırır
14. Gemini yalnızca doğrulanmış DB özetine göre yorum üretir
```

Bu akışta PDF'den gelen hiçbir veri kullanıcı onayı olmadan gerçek finansal veri sayılmaz.

---

## 10. Manuel Giriş İş Akışı

Kullanıcı PDF yüklemek istemezse veya eksik veriyi tamamlamak isterse manuel giriş yapabilir.

Akış:

```text
1. Kullanıcı manuel gelir/gider/transfer formunu doldurur
2. Backend veya frontend create_manual_transaction() çağırır
3. Veri doğrudan transactions tablosuna kaydedilir
4. Summary stale olur
5. Backend recalculate_monthly_summary() çağırır
6. Dashboard ve chatbot güncel veriye göre çalışır
```

Manuel girişte transaction_drafts kullanılmaz çünkü veri doğrudan kullanıcı tarafından girilmiştir.

---

## 11. Birden Çok Hesap / PDF Senaryosu

Kullanıcı aynı ay için birden fazla hesap veya PDF ekleyebilir.

Örnek:

```text
2026-05 Ziraat PDF
2026-05 Enpara PDF
2026-05 Kredi Kartı PDF
2026-05 Nakit Manuel Harcamalar
```

Her PDF ayrı `statement` olarak tutulur. Her işlem ilgili `account_id` ve `statement_id` ile ilişkilendirilir.

Dashboard ve chatbot ise aynı ay içindeki tüm doğrulanmış işlemleri birleştirerek analiz yapar.

Kullanıcı PDF yükleme ve doğrulama işlemlerini tamamlamadan dashboard/chatbot aşamasına geçmemelidir. Bu kontrol backend/frontend iş akışında uygulanır.

---

## 12. Silme ve Düzeltme Senaryosu

Kullanıcı bir işlemi yanlış girdiyse veya PDF yanlış yüklendiyse sonradan düzeltebilir ya da silebilir.

Desteklenen durumlar:

```text
- Yanlış transaction düzenleme
- Yanlış transaction silme
- Silinen transaction geri alma
- Yanlış PDF/statement silme
- Statement silinince ona bağlı draft ve transactions kayıtlarını etkisizleştirme
```

Silme işlemi hard delete değildir. Soft delete kullanılır.

Dashboard ve chatbot yalnızca şu kayıtları kullanır:

```text
is_user_confirmed = true
is_deleted = false
```

---

## 13. Chatbot Veri Kullanım Mantığı

Chatbot doğrudan PDF'e veya Gemini'nin eski özetine bakmaz.

Doğru akış:

```text
Kullanıcı soru sorar
→ Backend kullanıcının ayını ve bağlamını belirler
→ Supabase'den ilgili transactions / monthly_summaries verisi çekilir
→ Backend gerekli özetleri hazırlar
→ Gemini'ye sadece gerekli context verilir
→ Gemini doğal dil cevabı üretir
→ Soru ve cevap chat_messages tablosuna kaydedilir
```

Chatbot'a tüm işlem geçmişini her seferinde göndermek yerine ilgili özet veya sınırlı transaction listesi gönderilmelidir.

Örnek:

```text
Soru: Bu ay en çok nereye harcamışım?
Backend: top_categories bilgisini monthly_summaries içinden alır.
Gemini: Bu bilgiyi kullanıcıya açıklayıcı şekilde yorumlar.
```

---

## 14. Test / Seed Dosyaları

Test dosyaları `supabase/seed/` altında tutulur.

Önerilen dosyalar:

```text
supabase/seed/035_seed_test_user_data.example.sql
supabase/seed/036_check_transactions_and_drafts.example.sql
supabase/seed/037_create_test_monthly_summary.example.sql
supabase/seed/038_check_monthly_dashboard.example.sql
```

Bu dosyalar production migration değildir. Sadece geliştirme ve doğrulama içindir.

İçlerinde gerçek kullanıcı ID'si tutulmamalıdır. Bunun yerine placeholder kullanılmalıdır:

```text
your-user-id-here
```

Lokal gerçek test dosyası gerekiyorsa `.local.sql` şeklinde tutulmalı ve `.gitignore` ile dışarıda bırakılmalıdır.

Önerilen `.gitignore` ekleri:

```gitignore
*.local.sql
supabase/seed/local/
.env
.env.local
```

---

## 15. Backend'e Kalan İşler

Supabase tarafı güçlü bir temel sağlar ama backend hâlâ kritik işlere sahiptir.

Backend'in görevleri:

```text
- PDF dosyasını almak
- PDF'i Gemini'ye tek istekle göndermek
- Gemini structured JSON çıktısını parse etmek
- Çıktıyı validate etmek
- save_statement_extraction() çağırmak
- create_transaction_draft() ile draft kayıtları oluşturmak
- update_statement_status() ile PDF durumunu yönetmek
- Kullanıcının draft onay/red işlemlerini endpointlere bağlamak
- Manuel işlem endpointlerini create_manual_transaction() ile bağlamak
- Transaction değişikliklerinden sonra recalculate_monthly_summary() çağırmak
- Gemini insight üretirken monthly_summaries verisini kullanmak
- Chatbot için DB context hazırlamak
- Chatbot mesajlarını chat_sessions ve chat_messages tablolarına kaydetmek
- API auth kontrolü yapmak
- Rate limit, retry, hata yönetimi ve logging yapmak
```

Yani Supabase her şeyi tek başına yapmaz. Supabase veri omurgasıdır; backend iş akışını ve AI entegrasyonunu yönetir.

---

## 16. Frontend'e Kalan İşler

Frontend tarafında bu Supabase mimarisine göre şu ekranlar bağlanmalıdır:

```text
- Auth ekranları
- Hesap oluşturma ekranı
- PDF yükleme ekranı
- PDF işlem doğrulama ekranı
- Manuel gelir/gider ekleme ekranı
- Geçmiş işlemler ekranı
- İşlem düzenleme/silme/geri alma ekranı
- Aylık gelir/hedef ekranı
- Dashboard
- AI yorum ekranı
- Chatbot ekranı
```

Frontend doğrudan veya backend üzerinden şu view ve RPC'leri kullanabilir:

```text
v_pending_transaction_drafts
v_confirmed_transactions
v_monthly_dashboard
create_manual_transaction()
approve_transaction_draft()
reject_transaction_draft()
update_transaction_details()
soft_delete_transaction()
restore_transaction()
upsert_monthly_profile()
```

Production güvenliği için kritik işlemlerin backend üzerinden yapılması önerilir.

---

## 17. Güvenlik Notları

- Service role key frontend'e konulmamalıdır.
- Secret key GitHub'a pushlanmamalıdır.
- `.env` dosyaları repoya eklenmemelidir.
- RLS açık kalmalıdır.
- Kullanıcı verisi her zaman `user_id` ile ayrılmalıdır.
- Public view'larda `security_invoker = true` kullanılmıştır.
- Test seed dosyalarında gerçek kullanıcı ID'si tutulmamalıdır.
- Gerçek banka PDF'leri repoya eklenmemelidir.
- Gemini'ye gönderilen context mümkün olduğunca özetlenmiş ve gerekli alanlarla sınırlı olmalıdır.

---

## 18. Kurulum Sırası

Yeni veya temizlenmiş bir Supabase public schema üzerinde kurulum yapılacaksa migration dosyaları sırayla çalıştırılmalıdır:

```text
001 → 034
```

Test verisi için seed dosyaları ayrıca ve dikkatli çalıştırılır:

```text
035 → 038
```

Seed dosyaları production ortamında çalıştırılmamalıdır.

---

## 19. Şu Anki Supabase Durumu

Kurulum sırasında aşağıdaki yapılar başarıyla oluşturulmuş ve test edilmiştir:

```text
✅ public schema temizlendi
✅ ana tablolar kuruldu
✅ ilişkiler kuruldu
✅ indexler kuruldu
✅ RLS açıldı
✅ policy'ler kuruldu
✅ view'lar kuruldu
✅ soft delete desteklendi
✅ PDF draft → transaction onay akışı kuruldu
✅ manuel transaction akışı kuruldu
✅ monthly profile ve monthly summary yapısı kuruldu
✅ Gemini insight tablosu kuruldu
✅ chatbot tabloları kuruldu
✅ test verisi eklendi
✅ dashboard view doğru sonuç döndürdü
```

Test sonucunda örnek Mayıs 2026 verisi için beklenen değerler dönmüştür:

```text
total_income: 25000
total_expense: 9570
net_balance: 15430
transaction_count: 5
income_count: 1
expense_count: 4
```

Bu, Supabase veri modelinin ve dashboard view yapısının çalıştığını göstermektedir.

---

## 20. Sonuç

Aliyda'nın Supabase tarafı, sadece minimum MVP için değil, gerçekçi ve sürdürülebilir bir finansal ürün mimarisi için hazırlanmıştır.

Bu yapı şunları destekler:

```text
- PDF ekstre yükleme
- Gemini ile işlem çıkarma
- Kullanıcı doğrulama ekranı
- Manuel gelir/gider girişi
- Birden çok hesap ve PDF desteği
- Aylık birleşik bütçe analizi
- Sonradan işlem düzeltme/silme
- Soft delete ve geri alma
- Deterministik finansal özetler
- Gemini ile doğal dil yorumlama
- DB verisine dayalı chatbot
- Kullanıcı bazlı güvenli veri izolasyonu
```

Backend ve frontend bu yapıya göre bağlandığında Aliyda, doğrulanmış finansal veriye dayanan güvenilir bir bütçe chatbot'u ve PDF destekli finans asistanı olarak çalışacaktır.
