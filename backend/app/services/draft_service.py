from supabase import Client
from typing import List, Dict, Any
from app.schemas.domain import ApproveDraftRequest


class DraftService:
    def __init__(self, db: Client):
        self.db = db

    def create_drafts_from_extraction(
        self, user_id: str, account_id: str, statement_id: str, month: str, transactions: List[Dict[str, Any]]
    ):
        """Creates transaction_drafts from Gemini extraction output."""
        for tx in transactions:
            try:
                self.db.rpc(
                    "create_transaction_draft",
                    {
                        "p_user_id": user_id,
                        "p_account_id": account_id,
                        "p_statement_id": statement_id,
                        "p_month": month,
                        "p_transaction_date": tx.get("transaction_date"),
                        "p_transaction_time": tx.get("transaction_time"),
                        "p_description": tx.get("description", ""),
                        "p_original_description": tx.get("original_description", ""),
                        "p_amount": float(tx.get("amount", 0)),
                        "p_currency": tx.get("currency", "TRY"),
                        "p_direction": tx.get("direction", "expense"),
                        "p_category": tx.get("category"),
                        "p_subcategory": tx.get("subcategory"),
                        "p_counterparty": tx.get("counterparty"),
                        "p_confidence_score": float(tx.get("confidence", 0.8)),
                        "p_needs_review": True,
                    }
                ).execute()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Draft oluşturulamadı: {e}")

    def list_pending_drafts(self, user_id: str, statement_id: str) -> List[Dict[str, Any]]:
        response = (
            self.db.table("transaction_drafts")
            .select("*")
            .eq("user_id", user_id)
            .eq("statement_id", statement_id)
            .eq("review_status", "pending")
            .order("transaction_date")
            .execute()
        )
        return response.data

    def approve_draft(self, user_id: str, draft_id: str, updates: ApproveDraftRequest = None) -> Dict[str, Any]:
        # Fetch draft first
        draft_response = (
            self.db.table("transaction_drafts")
            .select("*")
            .eq("id", draft_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        draft = draft_response.data
        if not draft:
            raise Exception("Taslak işlem bulunamadı.")

        # Apply any user edits
        if updates:
            update_dict = updates.model_dump(exclude_unset=True)
            if update_dict:
                for k, v in list(update_dict.items()):
                    if hasattr(v, "isoformat"):
                        update_dict[k] = v.isoformat()
                self.db.table("transaction_drafts").update(update_dict).eq("id", draft_id).execute()
                draft.update(update_dict)

        # Call the new p_user_id overload
        rpc_params = {
            "p_user_id": user_id,
            "p_draft_id": draft_id,
            "p_transaction_date": str(draft.get("transaction_date")),
            "p_transaction_time": str(draft.get("transaction_time")) if draft.get("transaction_time") else None,
            "p_description": draft.get("description"),
            "p_amount": float(draft.get("amount")) if draft.get("amount") is not None else 0.0,
            "p_direction": draft.get("direction"),
            "p_category": draft.get("category"),
            "p_subcategory": draft.get("subcategory"),
            "p_counterparty": draft.get("counterparty"),
        }
        response = self.db.rpc("approve_transaction_draft", rpc_params).execute()
        return {"transaction_id": response.data, "month": draft.get("month")}

    def reject_draft(self, user_id: str, draft_id: str, reason: str = None) -> bool:
        self.db.rpc(
            "reject_transaction_draft",
            {"p_user_id": user_id, "p_draft_id": draft_id, "p_reason": reason}
        ).execute()
        return True
