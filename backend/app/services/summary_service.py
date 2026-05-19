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
        live_dashboard = self.build_dashboard_from_confirmed_transactions(user_id, month)
        if live_dashboard:
            return live_dashboard

        response = (
            self.db.table("v_monthly_dashboard")
            .select("*")
            .eq("user_id", user_id)
            .eq("month", month)
            .execute()
        )
        return response.data[0] if response.data else None

    def ensure_summary_fresh(self, user_id: str, month: str):
        """Summary yoksa, stale ise veya confirmed tx varken 0 görünüyorsa recalculate et."""
        summary = self.get_monthly_summary(user_id, month)
        confirmed_count = self.count_confirmed_transactions(user_id, month)
        summary_count = int(summary.get("transaction_count") or 0) if summary else 0
        if not summary or summary.get("is_stale", True) or (confirmed_count > 0 and summary_count == 0):
            self._ensure_monthly_profile_exists(user_id, month)
            self.recalculate_monthly_summary(user_id, month)

    def count_confirmed_transactions(self, user_id: str, month: str) -> int:
        try:
            response = (
                self.db.table("v_confirmed_transactions")
                .select("id")
                .eq("user_id", user_id)
                .eq("month", month)
                .execute()
            )
            return len(response.data or [])
        except Exception as e:
            logger.error(f"confirmed transaction count hatasi: {e}")
            return 0

    def build_dashboard_from_confirmed_transactions(self, user_id: str, month: str) -> Optional[Dict[str, Any]]:
        try:
            response = (
                self.db.table("v_confirmed_transactions")
                .select("*")
                .eq("user_id", user_id)
                .eq("month", month)
                .execute()
            )
            transactions = response.data or []
        except Exception as e:
            logger.error(f"dashboard fallback transaction query hatasi: {e}")
            return None

        if not transactions:
            return None

        detected_income = 0.0
        declared_income = self._get_declared_income(user_id, month)
        total_income = 0.0
        total_expense = 0.0
        total_transfer_in = 0.0
        total_transfer_out = 0.0
        income_count = 0
        expense_count = 0
        category_totals: Dict[str, float] = {}

        largest_transactions = []
        for tx in transactions:
            amount = float(tx.get("amount") or 0)
            direction = tx.get("direction")
            if direction == "income":
                detected_income += amount
                income_count += 1
            elif direction == "transfer_in":
                detected_income += amount
                total_transfer_in += amount
                income_count += 1
            elif direction in ("expense", "transfer_out", "transfer"):
                if direction == "transfer_out":
                    total_transfer_out += amount
                total_expense += amount
                expense_count += 1
                category = tx.get("category") or "Diğer"
                category_totals[category] = category_totals.get(category, 0.0) + amount

            largest_transactions.append({
                "id": tx.get("id"),
                "description": tx.get("description"),
                "amount": amount,
                "direction": direction,
                "category": tx.get("category"),
                "transaction_date": tx.get("transaction_date"),
            })

        top_categories = [
            {"category": category, "total": total}
            for category, total in sorted(category_totals.items(), key=lambda item: item[1], reverse=True)[:10]
        ]
        largest_transactions = sorted(largest_transactions, key=lambda tx: tx["amount"], reverse=True)[:10]
        total_income = max(declared_income, detected_income)
        if declared_income > 0 and detected_income > 0:
            income_basis = "mixed"
        elif declared_income > 0:
            income_basis = "manual"
        elif detected_income > 0:
            income_basis = "pdf"
        else:
            income_basis = "none"

        return {
            "user_id": user_id,
            "month": month,
            "detected_income": detected_income,
            "declared_income": declared_income,
            "income_basis": income_basis,
            "total_income": total_income,
            "total_expense": total_expense,
            "total_transfer_in": total_transfer_in,
            "total_transfer_out": total_transfer_out,
            "net_balance": total_income - total_expense,
            "transaction_count": len(transactions),
            "income_count": income_count,
            "expense_count": expense_count,
            "top_categories": top_categories,
            "largest_transactions": largest_transactions,
            "recurring_candidates": [],
            "is_stale": False,
            "calculated_at": None,
        }

    def _get_declared_income(self, user_id: str, month: str) -> float:
        try:
            response = (
                self.db.table("monthly_profiles")
                .select("declared_income")
                .eq("user_id", user_id)
                .eq("month", month)
                .limit(1)
                .execute()
            )
            if not response.data:
                return 0.0
            return float(response.data[0].get("declared_income") or 0)
        except Exception as e:
            logger.warning(f"declared income okunamadi: {e}")
            return 0.0
