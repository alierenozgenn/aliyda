"""
Gemini API baglanti testi.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# 1. Env kontrol
api_key = os.getenv("GEMINI_API_KEY", "")
print(f"[1] GEMINI_API_KEY: {'TANIMLI (' + api_key[:10] + '...)' if api_key else 'TANIMLI DEGIL!'}")

if not api_key:
    print("HATA: .env dosyasinda GEMINI_API_KEY yok.")
    sys.exit(1)

# 2. google-genai import testi
try:
    from google import genai
    from google.genai import types
    print("[2] google-genai import: OK")
except ImportError as e:
    print(f"[2] google-genai import: HATA {e}")
    print("    pip install google-genai")
    sys.exit(1)

# 3. Client olusturma
try:
    client = genai.Client(api_key=api_key)
    print("[3] Gemini client olusturuldu: OK")
except Exception as e:
    print(f"[3] Gemini client olusturma: HATA {e}")
    sys.exit(1)

# 4. Basit metin testi
print("\n[4] Basit metin testi yapiliyor...")
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Merhaba, 2+2 kac eder? Sadece sayiyi yaz.",
        config=types.GenerateContentConfig(temperature=0.1)
    )
    print(f"    Gemini yaniti: {response.text.strip()}")
    print(f"    Gemini API calisiyor!")
except Exception as e:
    error_str = str(e)
    print(f"    HATA: {error_str}")
    if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
        print("    --> KOTA DOLMUS veya rate limit!")
    elif "403" in error_str or "permission" in error_str.lower():
        print("    --> API KEY YETKISIZ!")
    elif "401" in error_str or "invalid" in error_str.lower():
        print("    --> API KEY GECERSIZ!")
    elif "model" in error_str.lower() and "not found" in error_str.lower():
        print("    --> MODEL BULUNAMADI. gemini-1.5-flash deneyin.")
    sys.exit(1)

# 5. PDF testi
pdf_files = []
if os.path.exists("temp"):
    pdf_files = [os.path.join("temp", f) for f in os.listdir("temp") if f.endswith(".pdf")]
for f in os.listdir("."):
    if f.endswith(".pdf"):
        pdf_files.append(f)

if pdf_files:
    test_pdf = pdf_files[0]
    print(f"\n[5] PDF extraction testi: {test_pdf}")
    try:
        with open(test_pdf, "rb") as f:
            pdf_bytes = f.read()
        print(f"    PDF boyutu: {len(pdf_bytes)} bytes")
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                types.Part.from_text(text="Bu PDF dosyasindaki ilk 2 islemi JSON olarak listele.")
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            )
        )
        print(f"    Gemini PDF yaniti (ilk 300 char): {response.text[:300]}")
        print(f"    PDF extraction calisiyor!")
    except Exception as e:
        print(f"    PDF extraction HATASI: {e}")
else:
    print("\n[5] PDF testi atlandi - test edilecek PDF bulunamadi.")

print("\nTestler tamamlandi.")
