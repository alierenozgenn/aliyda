import google.generativeai as genai
import json
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

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
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])
    # Also strip possible 'json' language identifier
    if text.startswith("json\n"):
        text = text[5:]
    return json.loads(text.strip())
