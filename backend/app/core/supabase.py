from supabase import create_client, Client
from app.core.config import settings

def get_service_supabase() -> Client:
    """
    Returns a Supabase client with the SERVICE ROLE KEY.
    Use for admin/background tasks that need to bypass RLS.
    """
    key = settings.service_key
    if not settings.SUPABASE_URL or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY (or SUPABASE_SERVICE_ROLE_KEY) "
            "must be set in backend/.env"
        )
    return create_client(settings.SUPABASE_URL, key)


def get_user_supabase(access_token: str) -> Client:
    """
    Returns a Supabase client with the ANON KEY + user JWT.
    This client respects Row Level Security (RLS).
    auth.uid() resolves correctly inside DB functions called via this client.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in backend/.env")

    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    client.postgrest.auth(access_token)
    return client
