"""
Chat Context Builder — Aşama 6, Adım 43

Sorulara göre Supabase'den akıllıca context seçer.
Gemini'ye tüm transaction listesini vermek yerine sadece
gerekli özet verisi gönderilir.
"""
from supabase import Client
from typing import Dict, Any, List, Optional
import re


STOP_WORDS = {
    "bu", "ay", "icin", "için", "bana", "ben", "ne", "kadar", "para",
    "gondermis", "göndermiş", "gonderdi", "gönderdi", "gonderen", "gönderen",
    "kim", "kisi", "kişi", "kisisi", "kişisi", "toplam", "tl", "try",
    "harcamisim", "harcamışım", "odemisim", "ödemişim", "almisim", "almışım",
}

CATEGORY_ALIASES = {
    "fatura": "Faturalar",
    "faturalar": "Faturalar",
    "faturalarim": "Faturalar",
    "elektrik": "Faturalar",
    "su": "Faturalar",
    "internet": "Faturalar",
    "telefon": "Faturalar",
    "market": "Market",
    "marketim": "Market",
    "marketler": "Market",
    "restoran": "Restoran/Kafe",
    "kafe": "Restoran/Kafe",
    "yemek": "Restoran/Kafe",
    "ulasim": "Ulaşım",
    "ulaşim": "Ulaşım",
    "kira": "Kira",
    "eglence": "Eğlence",
    "egitim": "Eğitim",
    "saglik": "Sağlık",
    "giyim": "Giyim",
}

FIXED_OR_LOW_FLEX_CATEGORIES = {"Kira", "Faturalar", "Sağlık", "Eğitim"}

SAVINGS_RATES = {
    "Restoran/Kafe": 0.25,
    "Eğlence": 0.25,
    "Giyim": 0.20,
    "Market": 0.12,
    "Ulaşım": 0.10,
    "Diğer": 0.10,
}


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

        # Summary recalculation can lag/fail. Chat should prefer confirmed
        # source-of-truth transactions so dashboard and answers stay consistent.
        fallback_summary = self._build_summary_from_confirmed_transactions(user_id, month)
        if fallback_summary:
            summary = fallback_summary
        elif not summary or int(summary.get("transaction_count") or 0) <= 0:
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

        savings_context = self._build_savings_context(summary, question)
        if savings_context:
            context.update(savings_context)
            return context

        category_context = self._build_category_context(user_id, month, question)
        if category_context:
            context.update(category_context)
            return context

        counterparty_context = self._build_counterparty_context(user_id, month, question)
        if counterparty_context:
            context.update(counterparty_context)
            return context

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

        detected_income = 0.0
        total_expense = 0.0
        category_totals: Dict[str, float] = {}

        for tx in transactions:
            amount = float(tx.get("amount") or 0)
            direction = tx.get("direction")
            if direction in ("income", "transfer_in"):
                detected_income += amount
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
        profile = self._get_monthly_profile(user_id, month)
        declared_income = float(profile.get("declared_income") or 0) if profile else 0.0
        total_income = max(declared_income, detected_income)

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_balance": total_income - total_expense,
            "transaction_count": len(transactions),
            "top_categories": top_categories,
            "largest_transactions": largest_transactions,
            "detected_income": detected_income,
            "declared_income": declared_income,
            "income_basis": "mixed" if declared_income and detected_income else "manual" if declared_income else "pdf" if detected_income else "none",
        }

    def _build_counterparty_context(self, user_id: str, month: str, question: str) -> Optional[Dict[str, Any]]:
        query_tokens = self._extract_query_tokens(question)
        if len(query_tokens) < 2:
            return None

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

        matches = []
        for tx in transactions:
            haystack = self._normalize_text(
                " ".join([
                    str(tx.get("counterparty") or ""),
                    str(tx.get("description") or ""),
                ])
            )
            score = sum(1 for token in query_tokens if token in haystack)
            if score >= min(2, len(query_tokens)):
                matches.append(tx)

        if not matches:
            return None

        incoming = [tx for tx in matches if tx.get("direction") in ("income", "transfer_in")]
        outgoing = [tx for tx in matches if tx.get("direction") in ("expense", "transfer_out", "transfer")]
        total_incoming = sum(float(tx.get("amount") or 0) for tx in incoming)
        total_outgoing = sum(float(tx.get("amount") or 0) for tx in outgoing)

        asks_sent_to_user = any(word in self._normalize_text(question) for word in ["bana", "gondermis", "gonderdi"])
        relevant_total = total_incoming if asks_sent_to_user else total_incoming - total_outgoing
        relevant_count = len(incoming) if asks_sent_to_user else len(matches)

        person_label = " ".join(token.capitalize() for token in query_tokens)
        detail_lines = [
            {
                "date": tx.get("transaction_date"),
                "description": tx.get("description"),
                "amount": float(tx.get("amount") or 0),
                "direction": tx.get("direction"),
                "counterparty": tx.get("counterparty"),
            }
            for tx in matches[:10]
        ]

        if asks_sent_to_user:
            answer = (
                f"{month} ayında {person_label} ile eşleşen {len(matches)} doğrulanmış işlem buldum. "
                f"Sana gelen toplam tutar {self._format_try(total_incoming)}."
            )
            if not incoming and total_outgoing > 0:
                answer = (
                    f"{month} ayında {person_label} ile eşleşen işlem var ama sana gelen para görünmüyor. "
                    f"Bu kişi/ifadeyle eşleşen dışarı giden toplam tutar {self._format_try(total_outgoing)}."
                )
        else:
            answer = (
                f"{month} ayında {person_label} ile eşleşen {relevant_count} doğrulanmış işlem buldum. "
                f"Net toplam {self._format_try(relevant_total)}."
            )

        return {
            "counterparty_query": {
                "query_tokens": query_tokens,
                "matched_transaction_count": len(matches),
                "incoming_total": total_incoming,
                "outgoing_total": total_outgoing,
                "matched_transactions": detail_lines,
            },
            "deterministic_answer": answer,
        }

    def _build_category_context(self, user_id: str, month: str, question: str) -> Optional[Dict[str, Any]]:
        category = self._detect_category(question)
        if not category:
            return None

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

        matches = [
            tx for tx in transactions
            if self._category_matches(tx.get("category"), category)
        ]
        if not matches:
            return None

        matches = sorted(matches, key=lambda tx: (tx.get("transaction_date") or "", float(tx.get("amount") or 0)))
        total = sum(float(tx.get("amount") or 0) for tx in matches)
        wants_detail = any(word in self._normalize_text(question) for word in [
            "hangi", "detay", "detaylandir", "hepsi", "hepsini", "listele", "neler",
            "tek", "tek tek", "soyle", "soyler", "sayar", "sayabilir"
        ])

        if wants_detail:
            lines = []
            for tx in matches[:8]:
                date = tx.get("transaction_date") or "tarih yok"
                description = tx.get("description") or tx.get("counterparty") or "İşlem"
                lines.append(f"- {date}: {description} — {self._format_try(float(tx.get('amount') or 0))}")
            more = ""
            if len(matches) > 8:
                more = f"\nİlk 8 işlemi gösterdim; toplam {len(matches)} işlem var."
            answer = (
                f"{month} ayında {category} kategorisinde {len(matches)} doğrulanmış işlem var; "
                f"toplam {self._format_try(total)}.\n" + "\n".join(lines) + more
            )
        else:
            biggest = max(matches, key=lambda tx: float(tx.get("amount") or 0))
            answer = (
                f"{month} ayında {category} kategorisinde toplam {self._format_try(total)} harcama görünüyor. "
                f"Bu kategoride {len(matches)} işlem var; en büyük işlem "
                f"{self._format_try(float(biggest.get('amount') or 0))} ile {biggest.get('description') or 'isimsiz işlem'}."
            )

        return {
            "category_query": {
                "category": category,
                "matched_transaction_count": len(matches),
                "total": total,
                "matched_transactions": [
                    {
                        "date": tx.get("transaction_date"),
                        "description": tx.get("description"),
                        "amount": float(tx.get("amount") or 0),
                        "counterparty": tx.get("counterparty"),
                    }
                    for tx in matches[:20]
                ],
            },
            "deterministic_answer": answer,
        }

    def _build_savings_context(self, summary: Dict[str, Any], question: str) -> Optional[Dict[str, Any]]:
        normalized = self._normalize_text(question)
        if not any(word in normalized for word in ["tasarruf", "kisabilirim", "azalt", "nereden", "ayirmak", "biriktir"]):
            return None

        categories = summary.get("top_categories") or []
        if not categories:
            return None

        fixed_categories = []
        flexible_suggestions = []
        for item in categories:
            category = item.get("category") or "Diğer"
            total = float(item.get("total") or item.get("amount") or 0)
            if total <= 0:
                continue

            if category in FIXED_OR_LOW_FLEX_CATEGORIES:
                fixed_categories.append({"category": category, "total": total})
                continue

            rate = SAVINGS_RATES.get(category, 0.10)
            suggested_cut = total * rate
            if suggested_cut <= 0:
                continue

            flexible_suggestions.append({
                "category": category,
                "total": total,
                "suggested_cut": suggested_cut,
                "rate": rate,
            })

        flexible_suggestions = sorted(
            flexible_suggestions,
            key=lambda item: item["suggested_cut"],
            reverse=True,
        )
        realistic_total = sum(item["suggested_cut"] for item in flexible_suggestions[:5])
        requested_goal = (
            self._extract_money_amount(question)
            if any(word in normalized for word in ["ayir", "ayirmak", "biriktir", "hedef", "ekstra"])
            else None
        )

        if flexible_suggestions:
            lines = []
            for suggestion in flexible_suggestions[:4]:
                pct = int(round(suggestion["rate"] * 100))
                lines.append(
                    f"- {suggestion['category']}: toplam {self._format_try(suggestion['total'])}; "
                    f"yaklaşık %{pct} dikkatle {self._format_try(suggestion['suggested_cut'])} alan açabilir."
                )
            flexible_text = "\n".join(lines)
        else:
            flexible_text = "- Bu ay esnek sayılabilecek belirgin bir harcama kategorisi görünmüyor."

        fixed_text = ""
        if fixed_categories:
            names = ", ".join(
                f"{item['category']} ({self._format_try(item['total'])})"
                for item in fixed_categories[:3]
            )
            fixed_text = (
                f"\n\nNot: {names} yüksek görünse bile bunları ana tasarruf alanı gibi düşünmemek daha doğru. "
                "Bunlar sabit ya da düşük esnekliğe sahip kalemler; en fazla tarife, abonelik veya ödeme planı kontrol edilir."
            )

        goal_text = ""
        if requested_goal:
            if realistic_total >= requested_goal:
                goal_text = (
                    f"\n\n{self._format_try(requested_goal)} hedefi bu ayki esnek harcamalara bakınca zor ama mümkün görünüyor; "
                    "bunu tek bir kalemden değil birkaç küçük karardan toplamak daha sağlıklı."
                )
            else:
                gap = requested_goal - realistic_total
                goal_text = (
                    f"\n\n{self._format_try(requested_goal)} ekstra ayırmak mevcut doğrulanmış veriye göre sadece harcamayı kısmakla gerçekçi görünmüyor. "
                    f"Esnek kalemlerden makul alan yaklaşık {self._format_try(realistic_total)}; kalan {self._format_try(gap)} için hedefi iki aya bölmek, "
                    "ek gelir yaratmak veya sabit ödemelerin takvimini yeniden planlamak gerekir."
                )

        answer = (
            "Bence tasarrufta ilk bakılacak yer sabit giderler değil, gerçekten oynayabildiğin harcamalar. "
            "Bu ayki doğrulanmış veriye göre en mantıklı alanlar:\n"
            f"{flexible_text}"
            f"{fixed_text}"
            f"{goal_text}"
        )

        return {
            "savings_suggestions": flexible_suggestions[:5],
            "fixed_or_low_flex_categories": fixed_categories[:5],
            "requested_savings_goal": requested_goal,
            "realistic_savings_room": realistic_total,
            "deterministic_answer": answer,
        }

    def _extract_query_tokens(self, question: str) -> List[str]:
        normalized = self._normalize_text(question)
        tokens = [token for token in normalized.split() if len(token) >= 3 and token not in STOP_WORDS]
        return tokens[:5]

    def _detect_category(self, question: str) -> Optional[str]:
        normalized = self._normalize_text(question)
        for token in normalized.split():
            if token in CATEGORY_ALIASES:
                return CATEGORY_ALIASES[token]
        for alias, category in CATEGORY_ALIASES.items():
            if alias in normalized:
                return category
        return None

    def _category_matches(self, value: Optional[str], expected: str) -> bool:
        if not value:
            return False
        return self._normalize_text(value) == self._normalize_text(expected)

    def _normalize_text(self, value: str) -> str:
        lowered = (value or "").lower()
        lowered = lowered.replace("ı", "i").replace("ğ", "g").replace("ü", "u")
        lowered = lowered.replace("ş", "s").replace("ö", "o").replace("ç", "c")
        return re.sub(r"[^a-z0-9]+", " ", lowered).strip()

    def _extract_money_amount(self, question: str) -> Optional[float]:
        matches = re.findall(r"\d+(?:[.,]\d+)*", question or "")
        if not matches:
            return None

        values = []
        for match in matches:
            compact = match.replace(".", "").replace(",", "")
            try:
                value = float(compact)
            except ValueError:
                continue
            if value >= 100:
                values.append(value)

        return max(values) if values else None

    def _format_try(self, value: float) -> str:
        formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{formatted} TL"
