"""
Tam PDF extraction pipeline testi — gercek prompt ile.
"""
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

from app.services.gemini_service import GeminiService, PDF_EXTRACTION_PROMPT


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
print(f"Boyut: {os.path.getsize(pdf_path)} bytes")

# Gemini extraction - TAM PROMPT ile
print("\nGemini cagiriliyor (tam prompt ile)...")
try:
    gemini = GeminiService()
    parsed = gemini.extract_transactions_from_pdf(pdf_path, {"test_prompt": PDF_EXTRACTION_PROMPT[:120]})
    raw = json.dumps(parsed, ensure_ascii=False)
    print(f"Normalize yanit ({len(raw)} char):")
    print(raw[:1000])
    
    # JSON parse
    try:
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
