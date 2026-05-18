from app.core.config import settings
from google import genai
from google.genai import types
from typing import List, Dict, Any
import json
import time
import logging

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GEMINI_API_KEY)

PROMPT_VERSION = "v2.0"

PDF_EXTRACTION_PROMPT = """
Sen bir banka ekstresi analiz yapay zekasısın. Sana verilen PDF banka ekstresi belgesini incele.

Görevin SADECE veri çıkarmaktır. Yorum yapma, özet yazma, hesaplama yapma.

Aşağıdaki kurallara kesinlikle uy:
1. Tüm işlemleri JSON array içinde döndür.
2. Yanıtın SADECE JSON olsun. Başına veya sonuna hiçbir şey ekleme (markdown, açıklama yok).
3. "direction" alanı yalnızca şu değerlerden biri olabilir: "income", "expense", "transfer"
4. Para birimi bilinmiyorsa "TRY" kullan.
5. Tarih formatı: "YYYY-MM-DD"
6. Saat formatı: "HH:MM" (bilinmiyorsa null)
7. Tutar her zaman pozitif sayı olmalı. Yönü "direction" belirler.
8. Gemini olarak hiçbir hesaplama yapma. Sadece PDF'de yazan rakamları yaz.
9. Güven skoru (confidence): 0.0-1.0 arasında, eğer tarih/tutar belirsizse düşük ver.

Döndürülecek format:
{
  "statement_month": "YYYY-MM",
  "income_detected": true,
  "transactions": [
    {
      "transaction_date": "YYYY-MM-DD",
      "transaction_time": "HH:MM",
      "description": "Kısa anlaşılır açıklama",
      "original_description": "PDF'deki orijinal metin olduğu gibi",
      "amount": 250.00,
      "currency": "TRY",
      "direction": "expense",
      "category": "Market",
      "subcategory": null,
      "counterparty": "Migros",
      "confidence": 0.95,
      "raw_text": "PDF'deki o satır tam olarak"
    }
  ],
  "warnings": []
}

Kategori önerileri (gerekirse kullan):
- Market, Restoran/Kafe, Ulaşım, Faturalar, Eğlence, Sağlık, Giyim, Eğitim, Kira, Maaş, Diğer Gelir, Transfer, Diğer
"""

INSIGHT_PROMPT_TEMPLATE = """
Sen Aliyda adlı kişisel bütçe asistanısın. Kullanıcının {month} ayı finansal özeti aşağıda verilmiştir.

Bu özete bakarak kullanıcıya 3-5 cümlelik, samimi, faydalı ve özgün bir yorum yaz.
- Türkçe yaz.
- Gerçek rakamları kullan (uydurma).
- Olumlu bir dil kullan ama gerçekçi ol.
- En çok harcanan kategoriyi belirt.
- Net bakiye pozitifse tebrik et, negatifse nazikçe uyar.
- Somut bir tasarruf önerisi ver.

Finansal özet:
{data}
"""

CHAT_SYSTEM_PROMPT = """
Sen Aliyda, bir kişisel bütçe ve finans asistanısın.

ÖNEMLİ KURALLAR:
1. SADECE sana verilen doğrulanmış finansal veriye dayan. Veri yoksa bunu açıkça söyle.
2. Asla kendi başına hesaplama yapma veya tahmin üretme.
3. Finansal yatırım tavsiyesi verme.
4. Veride olmayan işlem veya tutar söyleme.
5. Cevaplarını kısa, net ve pratik tut.
6. Türkçe yaz, samimi bir dil kullan.

Eğer sana sorulan şeyin cevabı veride yoksa: "Bu konuda elimde yeterli veri yok, işlem eklemeyi veya PDF yüklemeyi deneyin." de.
"""

# ─── Retry helper ───────────────────────────────
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]  # seconds


def _call_gemini_with_retry(model: str, contents, config) -> str:
    """
    Gemini API çağrısını retry mekanizmasıyla yapar.
    503 (server overload) ve 429 (rate limit) hatalarında otomatik bekler ve tekrar dener.
    """
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            return response.text.strip()
        except Exception as e:
            error_str = str(e)
            last_error = e

            # Retryable hatalar: 503 (overload), 429 (rate limit)
            is_retryable = any(code in error_str for code in ["503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED"])

            if is_retryable and attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.warning(
                    f"Gemini gecici hata (deneme {attempt + 1}/{MAX_RETRIES}): {error_str[:100]}. "
                    f"{delay}s sonra tekrar denenecek..."
                )
                time.sleep(delay)
            else:
                break

    raise last_error


class GeminiService:
    def __init__(self):
        self.extraction_model = settings.GEMINI_MODEL_EXTRACTION
        self.chat_model = settings.GEMINI_MODEL_CHAT

    def extract_transactions_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        PDF dosyasından işlemleri JSON olarak çıkarır.
        Roadmap kuralı: 1 PDF = 1 Gemini isteği.
        Gemini hiçbir hesaplama yapmaz, sadece veri çıkarır.
        503/429 hatalarında otomatik retry yapar.
        """
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()

        logger.info(f"Gemini extraction baslatiliyor: model={self.extraction_model}, pdf_size={len(pdf_bytes)}")

        text = _call_gemini_with_retry(
            model=self.extraction_model,
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                types.Part.from_text(text=PDF_EXTRACTION_PROMPT)
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for factual extraction
                response_mime_type="application/json",
            )
        )

        # Defensive cleanup in case model wraps in markdown
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        try:
            result = json.loads(text.strip())
            # Basic validation
            if "transactions" not in result:
                result["transactions"] = []
            if "income_detected" not in result:
                result["income_detected"] = any(
                    t.get("direction") == "income" for t in result["transactions"]
                )
            logger.info(f"Gemini extraction basarili: {len(result['transactions'])} islem cikarildi")
            return result
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Gemini gecerli JSON dondurmedi: {str(e)}\n"
                f"Ham cikti (ilk 500 karakter): {text[:500]}"
            )

    def generate_monthly_insight(self, dashboard_data: Dict[str, Any]) -> str:
        """
        Aylık özet verisine göre doğal dil yorumu üretir.
        Kaynak: Supabase'deki deterministik hesaplanmış veriler.
        Gemini hesaplama yapmaz, sadece yorumlar.
        """
        month = dashboard_data.get("month", "")
        data_str = json.dumps(dashboard_data, indent=2, ensure_ascii=False)

        prompt = INSIGHT_PROMPT_TEMPLATE.format(month=month, data=data_str)

        return _call_gemini_with_retry(
            model=self.chat_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
            )
        )

    def answer_chat_question(self, question: str, context: Dict[str, Any]) -> str:
        """
        Kullanıcının sorusunu YALNIZCA Supabase'den gelen doğrulanmış bağlam verisine
        dayanarak yanıtlar. Gemini asla kendi başına finansal hesap yapmaz.
        """
        context_str = json.dumps(context, indent=2, ensure_ascii=False)

        full_prompt = f"""{CHAT_SYSTEM_PROMPT}

Kullanıcının bu ayki doğrulanmış finansal verisi:
{context_str}

Kullanıcı sorusu: {question}

Cevabın:"""

        return _call_gemini_with_retry(
            model=self.chat_model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.5,
            )
        )
