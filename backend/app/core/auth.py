from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client
from app.core.config import settings

security = HTTPBearer()


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Extracts and returns the raw Bearer token from the Authorization header."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header eksik veya geçersiz.",
        )
    return credentials.credentials


async def get_current_user_id(token: str = Depends(get_current_user_token)) -> str:
    """
    Verifies the JWT token against Supabase Auth and returns the user's UUID.

    We intentionally use the ANON KEY client here — Supabase's auth.get_user(jwt=)
    endpoint accepts any valid API key; it validates the JWT itself.
    The service role key is NOT required for this operation.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sunucu yapılandırma hatası: Supabase bilgileri eksik.",
        )

    try:
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        user_response = client.auth.get_user(jwt=token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Geçersiz veya süresi dolmuş token.",
            )

        return user_response.user.id

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Kimlik doğrulama başarısız: {str(e)}",
        )
