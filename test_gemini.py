from google import genai

API_KEY = "AIzaSyBrWeJGdOBrfSKHDBo6VknV77VQ5Rrqx3k"

# Yoğunluk hatasını aşmak için listendeki modelleri sırayla deniyoruz
modeller = [
    'gemini-2.0-flash',        # 2.5 yoğundur ama 2.0 daha müsait olabilir
    'gemini-3.1-flash-lite',   # Yepyeni ve hafif model, genelde hep boştur
    'gemini-2.5-flash'         # Az önce 503 veren model
]

try:
    print("1. Gemini istemcisi başlatılıyor...")
    client = genai.Client(api_key=API_KEY)
    
    # Modelleri sırayla dürtüyoruz
    for model_adi in modeller:
        try:
            print(f"-> {model_adi} modeli deneniyor...")
            response = client.models.generate_content(
                model=model_adi,
                contents="Merhaba! Eğer bu mesajı okuyabiliyorsan sadece 'Sistem Hazır' yaz."
            )
            print("\n=== %100 BAŞARILI! ===")
            print(f"Cevap veren model: {model_adi}")
            print(f"Gemini'nin Cevabı: {response.text}")
            break  # Cevap aldık, döngüden çıkabiliriz
            
        except Exception as model_hatasi:
            print(f"   [Meşgul veya Hatalı] {model_adi} yanıt vermedi, sonrakine geçiliyor...")
            # Eğer listedeki son model de hata verdiyse hatayı yukarı fırlat
            if model_adi == modeller[-1]:
                raise model_hatasi

except Exception as e:
    print("\n--- HATA OLUŞTU! ---")
    print("Hata Detayı:", str(e))