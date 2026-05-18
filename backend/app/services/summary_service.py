from supabase import Client
from typing import Dict, Any

class SummaryService:
    def __init__(self, db: Client):
        self.db = db

    def recalculate_monthly_summary(self, user_id: str, month: str) -> Dict[str, Any]:
        # Using RPC as defined in supabase/migrations/019_recalculate_monthly_summary_function.sql
        # This will compute total income, expense, balance, top categories, etc.
        self.db.rpc(
            "recalculate_monthly_summary",
            {
                "p_month": month
            }
        ).execute()
        
        return self.get_monthly_summary(month)

    def get_monthly_summary(self, month: str) -> Dict[str, Any]:
        response = self.db.table("monthly_summaries")\
            .select("*")\
            .eq("month", month)\
            .execute()
        return response.data[0] if response.data else None

    def get_monthly_dashboard(self, month: str) -> Dict[str, Any]:
        # Uses the v_monthly_dashboard view which combines summary and profile
        response = self.db.table("v_monthly_dashboard")\
            .select("*")\
            .eq("month", month)\
            .execute()
        return response.data[0] if response.data else None
        
    def ensure_summary_fresh(self, user_id: str, month: str):
        summary = self.get_monthly_summary(month)
        if not summary or summary.get("is_stale", True):
            self.recalculate_monthly_summary(user_id, month)
