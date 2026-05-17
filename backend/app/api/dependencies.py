from fastapi import Depends, HTTPException
from supabase import Client
from app.core.auth import get_current_user_token, get_current_user_id
from app.core.supabase import get_user_supabase, get_service_supabase

async def get_db_client(token: str = Depends(get_current_user_token)) -> Client:
    """Returns a user-scoped Supabase client."""
    return get_user_supabase(token)

async def get_service_client() -> Client:
    """Returns an admin Supabase client (bypasses RLS)."""
    return get_service_supabase()
