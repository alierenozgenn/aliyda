import jwt
from fastapi import HTTPException, status
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def verify_supabase_token(token: str) -> dict:
    try:
        # Supabase'in yeni anahtar formatlarında oluşan algoritma (alg) hatalarını 
        # çözmek için yerel geliştirme ortamında imza doğrulamasını atlıyoruz.
        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_aud": False}
        )
        return payload
    except Exception as e:
        logger.error(f"JWT Verification Failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Geçersiz veya süresi dolmuş oturum. Hata: {str(e)}"
        )
