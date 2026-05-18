from supabase import Client
from typing import List, Dict, Any, Optional


class ChatService:
    def __init__(self, db: Client):
        self.db = db

    def create_session(self, user_id: str, title: str = "New Session", month_context: str = None) -> str:
        response = self.db.table("chat_sessions").insert({
            "user_id": user_id,
            "title": title,
            "month_context": month_context
        }).execute()
        return response.data[0]["id"] if response.data else None

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        response = self.db.table("chat_sessions").select("*").eq("id", session_id).single().execute()
        return response.data

    def list_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """user_id filtresi eklendi — sadece kendi oturumlarını listeler."""
        response = (
            self.db.table("chat_sessions")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

    def add_message(self, session_id: str, role: str, content: str, context_snapshot: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        response = self.db.table("chat_messages").insert({
            "session_id": session_id,
            "role": role,
            "content": content,
            "context_snapshot": context_snapshot
        }).execute()
        return response.data[0] if response.data else None

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        response = (
            self.db.table("chat_messages")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []
