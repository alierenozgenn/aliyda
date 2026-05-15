from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": "Gonderi verisi gecersiz.", "details": exc.errors()})

async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Beklenmeyen hata: {exc}", exc_info=True)
    messages = {
        "pdf":      "PDF analiz edilirken sorun olustu. Dosyanin banka ekstresi oldugunu dogrulayin.",
        "supabase": "Veritabani baglantisi kurulamadi. Lutfen tekrar deneyin.",
        "gemini":   "AI servisi su an yanit vermiyor. Birkac dakika sonra tekrar deneyin.",
    }
    for key, msg in messages.items():
        if key in str(exc).lower():
            return JSONResponse(status_code=500, content={"error": msg})
    return JSONResponse(status_code=500, content={"error": "Beklenmeyen bir hata olustu."})
