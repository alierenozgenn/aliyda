from fastapi import Depends
from supabase import Client
from app.core.auth import get_current_user_token
from app.core.supabase import get_service_supabase

async def get_db_client(token: str = Depends(get_current_user_token)) -> Client:
    """Returns a service-role Supabase client.
    Auth is validated via get_current_user_id separately.
    All service methods must explicitly filter by user_id."""
    return get_service_supabase()

async def get_service_client() -> Client:
    """Returns an admin Supabase client (bypasses RLS)."""
    return get_service_supabase()
