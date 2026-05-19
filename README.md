# Aliyda - Kişisel Finansal Analiz Sitesi

Aliyda, kullanıcıların banka ekstrelerini PDF olarak yükleyip işlemlerini doğrulayarak kişisel finans durumlarını anlaşılır biçimde analiz edebildiği yapay zeka destekli bir web uygulamasıdır.

Bu proje **BTK Akademi Hackathon 2026** için **Ali Eren Özgen** ve **İlayda Akyıldız** tarafından geliştirilmiştir.

## Canlı Demo

```text
[https://your-netlify-link.netlify.app](https://aliydaa.netlify.app/)
```

## Projenin Amacı

Kişisel finans takibi çoğu kullanıcı için zahmetli, dağınık ve sürdürülemez bir süreçtir. Banka ekstrelerinde bulunan işlem bilgileri genellikle PDF formatında kalır; kullanıcı bu verileri manuel olarak tabloya geçirmek, kategorize etmek ve yorumlamak zorunda kalır.

Aliyda bu süreci daha kolay ve güvenilir hale getirmek için geliştirilmiştir. Kullanıcı PDF ekstresini yükler, yapay zeka işlem satırlarını çıkarır, kullanıcı bu işlemleri kontrol edip onaylar ve uygulama yalnızca doğrulanmış veriler üzerinden analiz üretir.

Temel hedef, kullanıcının finansal durumunu teknik detaylarla uğraşmadan anlayabilmesidir:

- Gelir ve giderlerini ay bazında görebilmek
- Harcama kategorilerini takip edebilmek
- Büyük işlemleri kolayca inceleyebilmek
- PDF ekstresinden otomatik işlem çıkarabilmek
- Yapay zeka çıktısını kullanıcı onayıyla güvenilir veriye dönüştürebilmek
- Doğal dilde finansal sorular sorabilmek

## Nasıl Çalışır?

Aliyda'nın ana akışı doğrulanmış veri prensibi üzerine kuruludur.

1. Kullanıcı banka ekstresini PDF olarak yükler.
2. Backend dosyayı Google Gemini API ile analiz eder.
3. Gemini PDF içerisindeki işlem satırlarını yapılandırılmış JSON formatında çıkarır.
4. Çıkarılan işlemler doğrudan kesin veri kabul edilmez; önce `transaction_drafts` tablosuna taslak olarak kaydedilir.
5. Kullanıcı Doğrulama Merkezi'nde her işlemi inceler.
6. Kullanıcı işlemi düzenleyebilir, onaylayabilir veya reddedebilir.
7. Sadece onaylanan işlemler `transactions` tablosuna aktarılır.
8. Dashboard, İşlemlerim ekranı ve Chatbot yalnızca doğrulanmış işlemleri kullanır.

Bu yapı sayesinde yapay zeka çıktısı ile gerçek kullanıcı verisi birbirinden ayrılır. Gemini finansal hesaplama yapmak için değil, PDF'den işlem çıkarmak ve doğrulanmış veriye dayalı doğal dil cevapları üretmek için kullanılır.

## Öne Çıkan Özellikler

### PDF Ekstre Analizi

Kullanıcı banka ekstresini PDF olarak yükler. Backend dosyayı işler ve Google Gemini üzerinden işlem bilgilerini çıkarır. Çıkarılan her işlem tarih, açıklama, tutar, yön, kategori tahmini, karşı taraf ve güven skoru gibi alanlarla taslak olarak saklanır.

### Doğrulama Merkezi

PDF'den gelen işlemler kullanıcıya tek tek gösterilir. Kullanıcı işlemleri onaylayabilir, reddedebilir veya düzenleyerek onaylayabilir. Onaylanmayan hiçbir işlem finansal analizlere dahil edilmez.

Bu ekran, yapay zeka çıktısının kullanıcı kontrolünden geçmesini sağlar.

### Dashboard

Dashboard ekranı kullanıcının doğrulanmış verilerinden canlı özet üretir:

- Toplam gelir
- Toplam gider
- Net bakiye
- Gelir / gider oranı
- Harcama kategorileri
- En büyük işlemler

Transfer, gelir ve gider yönleri ayrı ele alınır. Böylece dashboard, işlem listesi ve chatbot cevapları aynı doğrulanmış veri setine dayanır.

### İşlemlerim

Kullanıcı doğrulanmış tüm işlemlerini ay bazında görüntüleyebilir. Manuel işlem ekleme, düzenleme, silme ve geri alma akışları desteklenir. Manuel eklenen işlemler de doğrulanmış veri olarak sisteme dahil edilir.

### Aliyda Chatbot

Chatbot, kullanıcının seçtiği aya ait doğrulanmış finansal verilerle cevap verir. Kullanıcı doğal dilde şu tarz sorular sorabilir:

- Bu ay en çok nereye harcamışım?
- Faturalarımı tek tek gösterir misin?
- En büyük harcamalarım neler?
- Nereden tasarruf edebilirim?
- Belirli bir kişi bana ne kadar para göndermiş?

Veri yoksa chatbot tahmin üretmez; kullanıcıyı PDF yükleme veya işlem doğrulama akışına yönlendirir.

### Aylık Hedefler

Kullanıcı aylık gelirini, tasarruf hedefini ve bütçe hedefini tanımlayabilir. Bu bilgiler dashboard ve chatbot yorumlarının daha anlamlı hale gelmesini sağlar.

## Teknik Mimari

Aliyda monorepo yapısında geliştirilmiştir.

```text
aliyda/
  backend/      FastAPI tabanlı API servisi
  frontend/     React + Vite kullanıcı arayüzü
  supabase/     Veritabanı migration dosyaları
```

### Frontend

Frontend tarafında React ve Vite kullanılmıştır. Arayüz; dashboard, PDF yükleme, doğrulama merkezi, işlem listesi, chatbot, hedefler ve hesap yönetimi ekranlarından oluşur.

Kullanılan başlıca teknolojiler:

- React
- Vite
- React Router
- Axios
- Supabase JS
- Tailwind CSS
- Lucide React ikonları
- Recharts

### Backend

Backend tarafında FastAPI kullanılmıştır. API katmanı kullanıcı kimlik doğrulama, PDF işleme, taslak işlem yönetimi, işlem onaylama, dashboard verisi ve chatbot context üretimi gibi görevleri yönetir.

Kullanılan başlıca teknolojiler:

- Python
- FastAPI
- Uvicorn
- Supabase Python Client
- Google GenAI SDK
- Pydantic
- Python Multipart

### Veritabanı

Veri katmanında Supabase PostgreSQL kullanılmıştır.

Temel tablolar:

- `accounts`
- `statements`
- `statement_extractions`
- `transaction_drafts`
- `transactions`
- `monthly_summaries`
- `monthly_profiles`
- `chat_sessions`
- `chat_messages`

Backend service role ile çalıştığı için kullanıcıya ait tüm kritik işlemlerde `user_id` parametresi ve filtreleri kullanılır. Kullanıcı izolasyonu hem API katmanında hem de veritabanı fonksiyonlarında korunur.

## Gemini Kullanımı

Projede Google AI Studio / Gemini API ana yapay zeka bileşeni olarak kullanılır.

Gemini iki ana amaçla kullanılır:

1. PDF banka ekstresinden işlem verilerini yapılandırılmış JSON olarak çıkarmak.
2. Chatbot tarafında doğrulanmış finansal context üzerinden doğal dilde açıklama üretmek.

PDF analizi için yeni Google GenAI SDK kullanılmıştır:

- Paket: `google-genai`
- Kullanım: `genai.Client`
- Dosya akışı: `client.files.upload` ve işlem sonrası `client.files.delete`

Gemini'nin finansal hesaplama yapması yerine hesaplamalar backend ve Supabase tarafında deterministik olarak yapılır. Bu yaklaşım, kullanıcıya gösterilen finansal rakamların tutarlı ve denetlenebilir olmasını sağlar.

## Güvenilir Veri Yaklaşımı

Aliyda'da yapay zeka çıktısı doğrudan finansal gerçek kabul edilmez. PDF'den çıkarılan işlemler önce taslak olarak tutulur. Kullanıcı onayı olmadan hiçbir işlem dashboard, chatbot veya aylık analizlere dahil edilmez.

Bu yaklaşım üç temel nedenle önemlidir:

- PDF veya model kaynaklı hatalar kullanıcı tarafından yakalanabilir.
- Kullanıcı kendi finansal verisi üzerinde kontrol sahibi olur.
- Analizler yalnızca doğrulanmış kayıtlar üzerinden üretildiği için daha güvenilir hale gelir.

## Kullanıcı Akışı

1. Kullanıcı siteye giriş yapar.
2. Hesap oluşturur veya mevcut hesabını seçer.
3. PDF Yükle ekranından banka ekstresini yükler.
4. Doğrulama Merkezi'nde çıkarılan işlemleri kontrol eder.
5. İşlemleri onaylar veya reddeder.
6. Onaylanan işlemler İşlemlerim ekranında görünür.
7. Dashboard doğrulanmış verilerle güncellenir.
8. Kullanıcı Chatbot'a doğal dilde finansal sorular sorabilir.

## Veri Güvenliği ve Kontrol

Aliyda'da kullanıcıya ait finansal veriler kullanıcı bazlı tutulur. Backend tarafında service role kullanılsa bile kritik veritabanı işlemleri `user_id` parametresiyle yapılır. Böylece kullanıcıya ait kayıtların ayrıştırılması API ve veritabanı fonksiyonları seviyesinde korunur.

PDF dosyaları analiz amacıyla geçici olarak işlenir. Google Files API'ye yüklenen geçici dosyalar işlem tamamlandıktan sonra temizlenir.

## Proje Yapısı

```text
backend/app/api
  REST endpointleri

backend/app/services
  İş mantığı, Gemini entegrasyonu, Supabase servisleri

backend/app/core
  Konfigürasyon, kimlik doğrulama ve Supabase client yönetimi

frontend/src/pages
  Uygulama ekranları

frontend/src/components
  Ortak arayüz bileşenleri

frontend/src/services
  API ve Supabase istemcileri

supabase/migrations
  PostgreSQL tablo, view, RPC ve policy migration dosyaları
```

## Takım

- Ali Eren Özgen
- İlayda Akyıldız

BTK Akademi Hackathon 2026 kapsamında geliştirilmiştir.
