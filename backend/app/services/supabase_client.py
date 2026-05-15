from supabase import create_client, Client
from app.core.config import settings

def get_supabase() -> Client:
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_SERVICE_KEY
    return create_client(url, key)
