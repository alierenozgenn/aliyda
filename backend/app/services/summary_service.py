from supabase import Client
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SummaryService:
    def __init__(self, db: Client):
        self.db = db

    def recalculate_monthly_summary(self, user_id: str, month: str) -> Optional[Dict[str, Any]]:
        """Calls the p_user_id overload of recalculate_monthly_summary."""
        try:
            self.db.rpc(
                "recalculate_monthly_summary",
                {"p_user_id": user_id, "p_month": month}
            ).execute()
        except Exception as e:
            error_str = str(e)
            # declared_income NOT NULL hatasi — profil olusturup tekrar dene
            if "declared_income" in error_str and "not-null" in error_str:
                logger.warning(f"declared_income NULL hatasi, default profil olusturuluyor: user={user_id}, month={month}")
                self._ensure_monthly_profile_exists(user_id, month)
                # Tekrar dene
                try:
                    self.db.rpc(
                        "recalculate_monthly_summary",
                        {"p_user_id": user_id, "p_month": month}
                    ).execute()
                except Exception as retry_e:
                    logger.error(f"recalculate retry hatasi: {retry_e}")
                    return None
            else:
                logger.error(f"recalculate_monthly_summary hatasi: {e}")
                return None
        return self.get_monthly_summary(user_id, month)

    def _ensure_monthly_profile_exists(self, user_id: str, month: str):
        """monthly_profiles'ta kayit yoksa default degerlerle olusturur."""
        try:
            existing = (
                self.db.table("monthly_profiles")
                .select("id")
                .eq("user_id", user_id)
                .eq("month", month)
                .execute()
            )
            if not existing.data:
                self.db.table("monthly_profiles").insert({
                    "user_id": user_id,
                    "month": month,
                    "declared_income": 0,
                    "income_source": "none",
                    "savings_goal": None,
                    "budget_goal": None,
                }).execute()
                logger.info(f"Default monthly_profile olusturuldu: user={user_id}, month={month}")
        except Exception as e:
            logger.error(f"monthly_profile olusturma hatasi: {e}")

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
        """Summary yoksa veya stale ise recalculate et."""
        summary = self.get_monthly_summary(user_id, month)
        if not summary or summary.get("is_stale", True):
            self._ensure_monthly_profile_exists(user_id, month)
            self.recalculate_monthly_summary(user_id, month)
