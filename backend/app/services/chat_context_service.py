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

    def build_context(self, question: str, month: Optional[str]) -> Dict[str, Any]:
        """
        Soruyu analiz ederek ilgili context'i seçer.
        Gemini bu context üzerinden cevap üretir.
        """
        question_lower = question.lower()

        context: Dict[str, Any] = {"month": month}

        if not month:
            context["note"] = "Ay belirtilmedi. Genel finansal bilgi sorusu."
            return context

        # 1. Aylık özet (neredeyse her soru için gerekli)
        summary = self._get_monthly_summary(month)

        if not summary:
            context["note"] = "Bu ay için henüz doğrulanmış veri yok."
            return context

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
        profile = self._get_monthly_profile(month)
        if profile:
            context["goals"] = {
                "savings_goal": profile.get("savings_goal"),
                "budget_goal": profile.get("budget_goal"),
            }

        return context

    def _get_monthly_summary(self, month: str) -> Optional[Dict[str, Any]]:
        try:
            res = (
                self.db.table("monthly_summaries")
                .select("*")
                .eq("month", month)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception:
            return None

    def _get_monthly_profile(self, month: str) -> Optional[Dict[str, Any]]:
        try:
            res = (
                self.db.table("monthly_profiles")
                .select("*")
                .eq("month", month)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception:
            return None
