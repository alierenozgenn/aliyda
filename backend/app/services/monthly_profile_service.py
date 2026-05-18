from supabase import Client
from typing import Dict, Any, Optional
from app.schemas.domain import MonthlyProfileUpsert


class MonthlyProfileService:
    def __init__(self, db: Client):
        self.db = db

    def upsert_monthly_profile(self, user_id: str, data: MonthlyProfileUpsert) -> str:
        # Using RPC as defined in supabase/migrations/030_upsert_monthly_profile_function.sql
        response = self.db.rpc(
            "upsert_monthly_profile",
            {
                "p_user_id": user_id,
                "p_month": data.month,
                "p_declared_income": data.declared_income,
                "p_income_source": "manual",
                "p_savings_goal": data.savings_goal,
                "p_budget_goal": data.budget_goal
            }
        ).execute()
        return response.data

    def get_monthly_profile(self, user_id: str, month: str) -> Optional[Dict[str, Any]]:
        """user_id filtresi eklendi — sadece kendi profilini görür."""
        response = (
            self.db.table("monthly_profiles")
            .select("*")
            .eq("user_id", user_id)
            .eq("month", month)
            .execute()
        )
        return response.data[0] if response.data else None
