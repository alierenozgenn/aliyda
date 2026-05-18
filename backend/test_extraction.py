"""
Tam PDF extraction pipeline testi — gercek prompt ile.
"""
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

PDF_EXTRACTION_PROMPT = """
Sen bir banka ekstresi analiz yapay zekasisin. Sana verilen PDF banka ekstresi belgesini incele.

Gorevin SADECE veri cikarmaktir. Yorum yapma, ozet yazma, hesaplama yapma.

Asagidaki kurallara kesinlikle uy:
1. Tum islemleri JSON array icinde dondur.
2. Yanitin SADECE JSON olsun. Basina veya sonuna hicbir sey ekleme (markdown, aciklama yok).
3. "direction" alani yalnizca su degerlerden biri olabilir: "income", "expense", "transfer"
4. Para birimi bilinmiyorsa "TRY" kullan.
5. Tarih formati: "YYYY-MM-DD"
6. Saat formati: "HH:MM" (bilinmiyorsa null)
7. Tutar her zaman pozitif sayi olmali. Yonu "direction" belirler.
8. Gemini olarak hicbir hesaplama yapma. Sadece PDF'de yazan rakamlari yaz.
9. Guven skoru (confidence): 0.0-1.0 arasinda, eger tarih/tutar belirsizse dusuk ver.

Donduulecek format:
{
  "statement_month": "YYYY-MM",
  "income_detected": true,
  "transactions": [
    {
      "transaction_date": "YYYY-MM-DD",
      "transaction_time": "HH:MM",
      "description": "Kisa anlasilir aciklama",
      "original_description": "PDF'deki orijinal metin oldugu gibi",
      "amount": 250.00,
      "currency": "TRY",
      "direction": "expense",
      "category": "Market",
      "subcategory": null,
      "counterparty": "Migros",
      "confidence": 0.95,
      "raw_text": "PDF'deki o satir tam olarak"
    }
  ],
  "warnings": []
}

Kategori onerileri (gerekirse kullan):
- Market, Restoran/Kafe, Ulasim, Faturalar, Eglence, Saglik, Giyim, Egitim, Kira, Maas, Diger Gelir, Transfer, Diger
"""

# PDF dosyasi bul
pdf_path = None
if os.path.exists("demo_ekstre.pdf"):
    pdf_path = "demo_ekstre.pdf"
elif os.path.exists("temp"):
    for f in os.listdir("temp"):
        if f.endswith(".pdf"):
            pdf_path = os.path.join("temp", f)
            break

if not pdf_path:
    print("PDF bulunamadi!")
    sys.exit(1)

print(f"PDF: {pdf_path}")
with open(pdf_path, "rb") as f:
    pdf_bytes = f.read()
print(f"Boyut: {len(pdf_bytes)} bytes")

# Gemini extraction - TAM PROMPT ile
print("\nGemini cagiriliyor (tam prompt ile)...")
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            types.Part.from_text(text=PDF_EXTRACTION_PROMPT)
        ],
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
        )
    )
    
    raw = response.text.strip()
    print(f"Ham yanit ({len(raw)} char):")
    print(raw[:1000])
    
    # JSON parse
    try:
        parsed = json.loads(raw)
        txs = parsed.get("transactions", [])
        print(f"\nJSON parse: BASARILI")
        print(f"Islem sayisi: {len(txs)}")
        if txs:
            print(f"Ilk islem: {json.dumps(txs[0], indent=2, ensure_ascii=False)}")
    except json.JSONDecodeError as e:
        print(f"\nJSON parse HATASI: {e}")
        
except Exception as e:
    print(f"GEMINI HATASI: {e}")
    import traceback
    traceback.print_exc()
