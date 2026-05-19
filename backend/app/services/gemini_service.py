from app.core.config import settings
from google import genai
from google.genai import types
from typing import Any, Dict, Optional
import json
import logging
import os
import time

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v3.1"
GEMINI_MODEL = "gemini-3.1-flash-lite"
MAX_RETRIES = 2
RETRY_DELAYS = [2]
FILE_READY_TIMEOUT_SECONDS = 30
FILE_READY_POLL_SECONDS = 1


PDF_EXTRACTION_PROMPT = """
Sen bir banka ekstresi veri çıkarma motorusun. Görevin SADECE PDF'de yazan işlem verilerini JSON olarak çıkarmaktır.

Kesin kurallar:
1. Yanıt SADECE geçerli JSON olsun. Markdown, açıklama, ```json bloğu veya yorum ekleme.
2. Finans matematiği yapma, toplam/özet hesaplama, tahmin yürütme. Sadece PDF'de gördüğün satırları çıkar.
3. Tutar her zaman pozitif sayı olsun. İşlemin yönünü direction alanı belirler.
4. direction yalnızca şu değerlerden biri olsun: expense, income, transfer_in, transfer_out.
5. Tarih YYYY-MM-DD formatında olsun. Saat bilinmiyorsa null olsun.
6. Para birimi bilinmiyorsa TRY kullan.
7. Güven skoru confidence 0.0 ile 1.0 arasında olsun.
8. Emin olmadığın alanları null bırak ve warnings listesine kısa not ekle.

Döndürülecek JSON şeması:
{
  "statement_period": "YYYY-MM veya null",
  "month": "YYYY-MM veya null",
  "bank_name": "Banka adı veya null",
  "account_hint": "Hesap/kart ipucu veya null",
  "income_detected": true,
  "warnings": [],
  "transactions": [
    {
      "date": "YYYY-MM-DD",
      "time": "HH:MM veya null",
      "description": "Kısa anlaşılır açıklama",
      "original_description": "PDF'deki açıklama/metin",
      "amount": 250.00,
      "direction": "expense",
      "currency": "TRY",
      "counterparty": "Karşı taraf veya null",
      "category_hint": "Kategori önerisi veya null",
      "confidence": 0.95,
      "raw_text": "İşlem satırının ham metni veya null",
      "source_line": "Varsa kaynak satır veya null"
    }
  ]
}

Kategori önerileri gerekiyorsa şunlardan seç:
Market, Restoran/Kafe, Ulaşım, Faturalar, Eğlence, Sağlık, Giyim, Eğitim, Kira, Maaş, Diğer Gelir, Transfer, Diğer
"""

PDF_SUMMARY_PROMPT = """
Bu PDF dosyasını Türkçe özetle.
Kısa, açık ve kullanıcının anlayacağı dilde yaz.
Finans matematiği yapma; sadece PDF'de açıkça görünen bilgileri özetle.
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


class GeminiConfigurationError(RuntimeError):
    pass


class GeminiAnalysisError(RuntimeError):
    pass


def _is_retryable_error(error: Exception) -> bool:
    error_str = str(error)
    return any(
        code in error_str
        for code in ["503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "timeout", "Timeout"]
    )


def _clean_json_text(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:].strip()
    if cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    return cleaned


def _file_state_name(file_obj: Any) -> str:
    state = getattr(file_obj, "state", None)
    if state is None:
        return ""
    return str(getattr(state, "name", state)).upper()


def _safe_error_detail(error: Exception, max_length: int = 350) -> str:
    detail = str(error) or error.__class__.__name__
    api_key = settings.google_api_key
    if api_key:
        detail = detail.replace(api_key, "[REDACTED_API_KEY]")
    detail = " ".join(detail.split())
    return detail[:max_length]


class GeminiService:
    def __init__(self):
        api_key = settings.google_api_key
        if not api_key:
            raise GeminiConfigurationError(
                "Google AI API anahtarı eksik. Backend .env içine GOOGLE_API_KEY veya GEMINI_API_KEY ekleyin."
            )

        self.client = genai.Client(api_key=api_key)
        self.model = GEMINI_MODEL
        self.extraction_model = GEMINI_MODEL
        self.chat_model = GEMINI_MODEL

    def analyze_pdf_summary(self, pdf_path: str) -> str:
        uploaded_file = None
        try:
            uploaded_file = self._upload_pdf(pdf_path)
            uploaded_file = self._wait_until_file_ready(uploaded_file)

            response_text = self._generate_text(
                contents=[uploaded_file, PDF_SUMMARY_PROMPT],
                temperature=0.2,
            )
            if not response_text:
                raise GeminiAnalysisError("Gemini PDF özetleme için boş yanıt döndürdü.")
            return response_text
        except GeminiConfigurationError:
            raise
        except Exception as e:
            logger.error("Gemini PDF summary hatasi: %s", e, exc_info=True)
            raise GeminiAnalysisError("PDF Google AI ile özetlenemedi. Lütfen birazdan tekrar deneyin.") from e
        finally:
            self._delete_uploaded_file(uploaded_file)

    def summarize_pdf_file(self, file_path: str) -> str:
        return self.analyze_pdf_summary(file_path)

    def extract_transactions_from_pdf(
        self,
        pdf_path: str,
        statement_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        uploaded_file = None
        try:
            uploaded_file = self._upload_pdf(pdf_path)
            uploaded_file = self._wait_until_file_ready(uploaded_file)

            prompt = self._build_extraction_prompt(statement_context)
            text = self._generate_text(
                contents=[uploaded_file, prompt],
                temperature=0.1,
                response_mime_type="application/json",
            )
            return self._parse_and_normalize_extraction(text)
        except GeminiConfigurationError:
            raise
        except GeminiAnalysisError:
            raise
        except Exception as e:
            logger.error("Gemini PDF extraction hatasi: %s", e, exc_info=True)
            raise GeminiAnalysisError("PDF Google AI ile analiz edilemedi. Lütfen birazdan tekrar deneyin.") from e
        finally:
            self._delete_uploaded_file(uploaded_file)

    def generate_monthly_insight(self, dashboard_data: Dict[str, Any]) -> str:
        month = dashboard_data.get("month", "")
        data_str = json.dumps(dashboard_data, indent=2, ensure_ascii=False)
        prompt = INSIGHT_PROMPT_TEMPLATE.format(month=month, data=data_str)

        return self._generate_text(
            contents=prompt,
            temperature=0.7,
        )

    def answer_chat_question(self, question: str, context: Dict[str, Any]) -> str:
        context_str = json.dumps(context, indent=2, ensure_ascii=False)

        full_prompt = f"""{CHAT_SYSTEM_PROMPT}

Kullanıcının bu ayki doğrulanmış finansal verisi:
{context_str}

Kullanıcı sorusu: {question}

Cevabın:"""

        return self._generate_text(
            contents=full_prompt,
            temperature=0.5,
        )

    def _upload_pdf(self, pdf_path: str) -> Any:
        try:
            logger.info("Google Files upload baslatiliyor: model=%s file=%s", self.model, pdf_path)
            return self.client.files.upload(
                file=pdf_path,
                config=types.UploadFileConfig(
                    mime_type="application/pdf",
                    display_name=os.path.basename(pdf_path),
                ),
            )
        except Exception as e:
            logger.error("Google Files upload hatasi: %s", e, exc_info=True)
            raise GeminiAnalysisError(
                f"PDF Google AI servisine yüklenemedi: {_safe_error_detail(e)}"
            ) from e

    def _wait_until_file_ready(self, uploaded_file: Any) -> Any:
        file_name = getattr(uploaded_file, "name", None)
        if not file_name:
            return uploaded_file

        deadline = time.monotonic() + FILE_READY_TIMEOUT_SECONDS
        current_file = uploaded_file

        while time.monotonic() < deadline:
            state_name = _file_state_name(current_file)
            if not state_name or "ACTIVE" in state_name or "READY" in state_name:
                return current_file
            if "FAILED" in state_name:
                raise GeminiAnalysisError("Google AI yüklenen PDF dosyasını işleyemedi.")

            logger.info("Google Files PDF hazirlanıyor: name=%s state=%s", file_name, state_name)
            time.sleep(FILE_READY_POLL_SECONDS)
            try:
                current_file = self.client.files.get(name=file_name)
            except Exception as e:
                logger.warning("Google Files state okunamadi, mevcut referans kullanilacak: %s", e)
                return uploaded_file

        raise GeminiAnalysisError("Google AI PDF dosyasını zamanında hazır hale getiremedi.")

    def _delete_uploaded_file(self, uploaded_file: Any) -> None:
        file_name = getattr(uploaded_file, "name", None) if uploaded_file else None
        if not file_name:
            return

        try:
            self.client.files.delete(name=file_name)
            logger.info("Google Files gecici dosya silindi: %s", file_name)
        except Exception as e:
            logger.warning("Google Files gecici dosya silinemedi: %s", e, exc_info=True)

    def _generate_text(
        self,
        contents: Any,
        temperature: float,
        response_mime_type: Optional[str] = None,
    ) -> str:
        config_kwargs: Dict[str, Any] = {"temperature": temperature}
        if response_mime_type:
            config_kwargs["response_mime_type"] = response_mime_type

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(**config_kwargs),
                )
                return (response.text or "").strip()
            except Exception as e:
                last_error = e
                if _is_retryable_error(e) and attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    logger.warning(
                        "Gemini gecici hata: model=%s attempt=%s/%s error=%s; %ss sonra tekrar denenecek",
                        self.model,
                        attempt + 1,
                        MAX_RETRIES,
                        str(e),
                        delay,
                    )
                    time.sleep(delay)
                    continue
                break

        logger.error("Gemini generate_content basarisiz: %s", last_error, exc_info=True)
        raise GeminiAnalysisError("Google AI modeli şu anda yanıt veremedi. Lütfen birazdan tekrar deneyin.") from last_error

    def _build_extraction_prompt(self, statement_context: Optional[Dict[str, Any]]) -> str:
        if not statement_context:
            return PDF_EXTRACTION_PROMPT

        context_str = json.dumps(statement_context, ensure_ascii=False)
        return f"""{PDF_EXTRACTION_PROMPT}

Ek bağlam:
{context_str}
"""

    def _parse_and_normalize_extraction(self, text: str) -> Dict[str, Any]:
        cleaned = _clean_json_text(text)
        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("Gemini gecersiz JSON dondurdu: %s raw=%s", e, cleaned[:1000], exc_info=True)
            raise GeminiAnalysisError("Google AI geçerli JSON döndürmedi. Lütfen PDF'i tekrar deneyin.") from e

        if not isinstance(result, dict):
            raise GeminiAnalysisError("Google AI beklenen JSON nesnesini döndürmedi.")

        transactions = result.get("transactions") or []
        if not isinstance(transactions, list):
            raise GeminiAnalysisError("Google AI transactions alanını liste olarak döndürmedi.")

        normalized_transactions = [self._normalize_transaction(tx) for tx in transactions if isinstance(tx, dict)]
        result["transactions"] = normalized_transactions
        result["warnings"] = result.get("warnings") if isinstance(result.get("warnings"), list) else []
        result["month"] = result.get("month") or result.get("statement_period") or result.get("statement_month")
        result["statement_period"] = result.get("statement_period") or result.get("month")
        result["income_detected"] = any(tx.get("direction") == "income" for tx in normalized_transactions)

        logger.info("Gemini extraction basarili: %s islem cikarildi", len(normalized_transactions))
        return result

    def _normalize_transaction(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        direction = tx.get("direction") or "expense"
        if direction == "transfer":
            direction = "transfer_out"

        confidence = tx.get("confidence", 0.8)
        try:
            confidence = max(0.0, min(1.0, float(confidence)))
        except (TypeError, ValueError):
            confidence = 0.8

        return {
            **tx,
            "transaction_date": tx.get("transaction_date") or tx.get("date"),
            "transaction_time": tx.get("transaction_time") or tx.get("time"),
            "description": tx.get("description") or tx.get("original_description") or "PDF işlemi",
            "original_description": tx.get("original_description") or tx.get("description"),
            "amount": tx.get("amount"),
            "currency": tx.get("currency") or "TRY",
            "direction": direction,
            "category": tx.get("category") or tx.get("category_hint"),
            "subcategory": tx.get("subcategory"),
            "counterparty": tx.get("counterparty"),
            "confidence": confidence,
            "raw_text": tx.get("raw_text") or tx.get("source_line"),
        }
