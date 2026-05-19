"""
Chat Context Builder — Aşama 6, Adım 43

Sorulara göre Supabase'den akıllıca context seçer.
Gemini'ye tüm transaction listesini vermek yerine sadece
gerekli özet verisi gönderilir.
"""
from supabase import Client
from typing import Dict, Any, List, Optional


class ChatContextService:
    def __init__(self, db: Client):
        self.db = db

    def build_context(self, user_id: str, question: str, month: Optional[str]) -> Dict[str, Any]:
        """
        Soruyu analiz ederek ilgili context'i seçer.
        Gemini bu context üzerinden cevap üretir.
        """
        question_lower = question.lower()

        context: Dict[str, Any] = {"month": month, "has_verified_data": False}

        if not month:
            context["note"] = "Ay belirtilmedi. Genel finansal bilgi sorusu."
            return context

        # 1. Aylık özet (neredeyse her soru için gerekli)
        summary = self._get_monthly_summary(user_id, month)

        if not summary or int(summary.get("transaction_count") or 0) <= 0:
            # Summary recalculation can lag/fail. Chat must still see confirmed
            # source-of-truth transactions instead of claiming there is no data.
            fallback_summary = self._build_summary_from_confirmed_transactions(user_id, month)
            if fallback_summary:
                summary = fallback_summary
            else:
                context["note"] = "Bu ay için doğrulanmış işlem bulunmuyor."
                context["transaction_count"] = 0
                return context

        context["has_verified_data"] = True

        # 2. Soruya göre hangi alanların ekleneceğine karar ver
        needs_categories = any(k in question_lower for k in [
            "kategori", "harcama", "nereye", "en çok", "market", "restoran",
            "fatura", "ulaşım", "kira", "yemek", "gider", "giderleri"
        ])
        needs_largest = any(k in question_lower for k in [
            "en büyük", "en pahalı", "büyük harcama", "yüksek", "ağır"
        ])
        needs_balance = any(k in question_lower for k in [
            "bakiye", "kaldı", "kalır", "net", "tasarruf", "birikti", "durum"
        ])
        needs_income = any(k in question_lower for k in [
            "gelir", "maaş", "kazandım", "para girdi"
        ])
        needs_all = any(k in question_lower for k in [
            "genel", "özet", "rapor", "durum", "ay nasıl", "nasıl gidiyor"
        ])

        # Temel rakamlar hep ekle
        context["total_income"] = summary.get("total_income")
        context["total_expense"] = summary.get("total_expense")
        context["net_balance"] = summary.get("net_balance")
        context["transaction_count"] = summary.get("transaction_count")

        if needs_categories or needs_all:
            context["top_categories"] = summary.get("top_categories", [])

        if needs_largest or needs_all:
            context["largest_transactions"] = summary.get("largest_transactions", [])

        if needs_income or needs_all:
            context["declared_income"] = summary.get("declared_income")
            context["detected_income"] = summary.get("detected_income")
            context["income_basis"] = summary.get("income_basis")

        if needs_balance or needs_all:
            context["savings_info"] = {
                "net_balance": summary.get("net_balance"),
                "total_expense": summary.get("total_expense"),
                "total_income": summary.get("total_income"),
            }

        # Monthly profile (hedefler)
        profile = self._get_monthly_profile(user_id, month)
        if profile:
            context["goals"] = {
                "savings_goal": profile.get("savings_goal"),
                "budget_goal": profile.get("budget_goal"),
            }

        return context

    def _get_monthly_summary(self, user_id: str, month: str) -> Optional[Dict[str, Any]]:
        try:
            res = (
                self.db.table("monthly_summaries")
                .select("*")
                .eq("user_id", user_id)
                .eq("month", month)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception:
            return None

    def _get_monthly_profile(self, user_id: str, month: str) -> Optional[Dict[str, Any]]:
        try:
            res = (
                self.db.table("monthly_profiles")
                .select("*")
                .eq("user_id", user_id)
                .eq("month", month)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception:
            return None

    def _build_summary_from_confirmed_transactions(self, user_id: str, month: str) -> Optional[Dict[str, Any]]:
        try:
            res = (
                self.db.table("v_confirmed_transactions")
                .select("*")
                .eq("user_id", user_id)
                .eq("month", month)
                .execute()
            )
            transactions = res.data or []
        except Exception:
            return None

        if not transactions:
            return None

        total_income = 0.0
        total_expense = 0.0
        category_totals: Dict[str, float] = {}

        for tx in transactions:
            amount = float(tx.get("amount") or 0)
            direction = tx.get("direction")
            if direction == "income":
                total_income += amount
            elif direction in ("expense", "transfer_out", "transfer"):
                total_expense += amount
                category = tx.get("category") or "Diğer"
                category_totals[category] = category_totals.get(category, 0.0) + amount

        top_categories = [
            {"category": category, "total": total}
            for category, total in sorted(category_totals.items(), key=lambda item: item[1], reverse=True)[:10]
        ]
        largest_transactions = sorted(
            [
                {
                    "id": tx.get("id"),
                    "description": tx.get("description"),
                    "amount": float(tx.get("amount") or 0),
                    "direction": tx.get("direction"),
                    "category": tx.get("category"),
                    "transaction_date": tx.get("transaction_date"),
                }
                for tx in transactions
            ],
            key=lambda tx: tx["amount"],
            reverse=True,
        )[:10]

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_balance": total_income - total_expense,
            "transaction_count": len(transactions),
            "top_categories": top_categories,
            "largest_transactions": largest_transactions,
            "detected_income": total_income,
            "declared_income": None,
            "income_basis": "detected" if total_income > 0 else "none",
        }
