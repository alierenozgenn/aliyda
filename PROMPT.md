Bu proje Aliyda adlı kişisel finans ve bütçe chatbot uygulamasıdır.

Önce proje dizinini incele. Özellikle şu dosyaları oku ve onlara göre hareket et:

- ROADMAP.md: Genel teknik yol haritası, geliştirme sırası ve yapılacak adımlar burada.
- SUPABASE.md: Supabase veritabanı mimarisi, tablolar, RPC fonksiyonları, view'lar ve veri akışı burada.
- supabase/migrations/: Supabase SQL migration dosyaları burada.
- supabase/seed/: Test/demo seed dosyaları burada.

Temel mimari kurallar:

- Finansal gerçekliğin kaynağı Gemini değil, kullanıcının onayladığı Supabase `transactions` verisidir.
- PDF'den gelen işlemler önce `transaction_drafts` tablosuna gider.
- Kullanıcı onayladıktan sonra işlemler `transactions` tablosuna aktarılır.
- Manuel girilen işlemler backend validation sonrası doğrudan `transactions` tablosuna gider.
- Dashboard ve chatbot sadece doğrulanmış DB verisine göre çalışır.
- Gemini finans matematiği yapmaz; sadece PDF extraction, doğal dil yorum ve chatbot cevabı üretir.
- Toplam gelir, toplam gider, kategori toplamları, net bakiye gibi hesaplamalar backend/Supabase tarafında yapılmalıdır.
- Chatbot PDF'e veya doğrulanmamış draft veriye değil, Supabase'deki doğrulanmış verilere ve summary contextine bakmalıdır.
- Service role key veya secret key frontend'e asla konmamalıdır.

Çalışma şeklin:

1. Önce mevcut kod yapısını analiz et.
2. ROADMAP.md ve SUPABASE.md dosyalarını oku.
3. Yapılacak görevi mevcut mimariye uygun şekilde planla.
4. Büyük ve kontrolsüz refactor yapma.
5. Değişiklikleri küçük, test edilebilir adımlar halinde uygula.
6. İş bitince hangi dosyaları değiştirdiğini, nasıl test edileceğini ve bir sonraki önerilen adımı yaz.

Şu an ROADMAP.md üzerinde kaldığımız adım:
