from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_JWT_SECRET: str
    GEMINI_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()