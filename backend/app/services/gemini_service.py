import google.generativeai as genai
import json
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

EXTRACTION_PROMPT = """
Sen bir banka ekstresi analiz uzmanısın. Görevin PDF içindeki finansal işlemleri (gelir/gider) bulup JSON olarak çıkarmaktır.

KURALLAR:
1. Tarihleri kesinlikle "YYYY-MM-DD" formatına çevir (Örn: 15.05.2026 -> 2026-05-15).
2. Yalnızca "income" (gelir) veya "expense" (gider) olarak sınıflandır.
3. Her işlem için en uygun Kategoriyi seç. Emin olmadıklarına "Diger" de. EFT/Havale/FAST gibi gönderimlere "Transfer" de.
4. "description" alanına işlemin açıklamasını yaz, ancak gereksiz uzun işlem kodlarını temizle, kime/nereye gittiği net kalsın.
5. "raw_text" alanına PDF'te okuduğun orijinal satırı BİREBİR yaz.
6. SADECE JSON çıktısı ver, başka hiçbir kelime (```json vb.) kullanma.

Kategoriler: Market, Kira, Ulasim, Yemek, Fatura, Egitim, Saglik, Eglence, Abonelik, Giyim, Transfer, Maas, Freelance, Diger

ÇIKTI FORMATI:
{
  "transactions": [
    {
      "date": "2026-05-15",
      "description": "Temizlenmis Aciklama",
      "amount": 123.45,
      "direction": "expense",
      "estimated_category": "Market",
      "confidence": 0.95,
      "raw_text": "15.05.2026 A101 MARKET 123.45 TL islem no:123"
    }
  ]
}
"""

async def extract_transactions_from_pdf(pdf_bytes: bytes) -> dict:
    pdf_part = {"mime_type": "application/pdf", "data": pdf_bytes}
    response = await model.generate_content_async([EXTRACTION_PROMPT, pdf_part])
    text = response.text.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])
    if text.startswith("json\n"):
        text = text[5:]
    return json.loads(text.strip())
