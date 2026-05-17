from supabase import Client
from typing import Dict, Any

class InsightService:
    def __init__(self, db: Client):
        self.db = db

    def save_insight(self, user_id: str, month: str, insight_text: str, model_used: str, prompt_version: str) -> Dict[str, Any]:
        response = self.db.table("ai_insights").insert({
            "user_id": user_id,
            "month": month,
            "insight_text": insight_text,
            "model_used": model_used,
            "prompt_version": prompt_version,
            "is_stale": False
        }).execute()
        return response.data[0] if response.data else None

    def get_latest_insight(self, month: str) -> Dict[str, Any]:
        response = self.db.table("ai_insights")\
            .select("*")\
            .eq("month", month)\
            .order("generated_at", desc=True)\
            .limit(1)\
            .execute()
        return response.data[0] if response.data else None

    def mark_insights_stale(self, month: str) -> bool:
        self.db.table("ai_insights").update({"is_stale": True}).eq("month", month).execute()
        return True
