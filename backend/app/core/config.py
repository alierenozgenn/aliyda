from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""

    # Accept both naming conventions for the service key
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""  # fallback alias used in .env

    # JWT secret (optional — used for local JWT decode if needed)
    SUPABASE_JWT_SECRET: Optional[str] = None

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_EXTRACTION: str = "gemini-2.0-flash"
    GEMINI_MODEL_CHAT: str = "gemini-2.0-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def service_key(self) -> str:
        """Returns whichever service key variable is set."""
        return self.SUPABASE_SERVICE_ROLE_KEY or self.SUPABASE_SERVICE_KEY

settings = Settings()