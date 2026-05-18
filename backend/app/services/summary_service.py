from supabase import Client
from typing import Dict, Any, Optional


class SummaryService:
    def __init__(self, db: Client):
        self.db = db

    def recalculate_monthly_summary(self, user_id: str, month: str) -> Dict[str, Any]:
        """Calls the p_user_id overload of recalculate_monthly_summary."""
        self.db.rpc(
            "recalculate_monthly_summary",
            {"p_user_id": user_id, "p_month": month}
        ).execute()
        return self.get_monthly_summary(user_id, month)

    def get_monthly_summary(self, user_id: str, month: str) -> Optional[Dict[str, Any]]:
        response = (
            self.db.table("monthly_summaries")
            .select("*")
            .eq("user_id", user_id)
            .eq("month", month)
            .execute()
        )
        return response.data[0] if response.data else None

    def get_monthly_dashboard(self, user_id: str, month: str) -> Optional[Dict[str, Any]]:
        response = (
            self.db.table("v_monthly_dashboard")
            .select("*")
            .eq("user_id", user_id)
            .eq("month", month)
            .execute()
        )
        return response.data[0] if response.data else None

    def ensure_summary_fresh(self, user_id: str, month: str):
        summary = self.get_monthly_summary(user_id, month)
        if not summary or summary.get("is_stale", True):
            self.recalculate_monthly_summary(user_id, month)
