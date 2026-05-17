from supabase import Client
from typing import List, Dict, Any
from app.schemas.domain import ApproveDraftRequest

class DraftService:
    def __init__(self, db: Client):
        self.db = db

    def create_drafts_from_extraction(self, user_id: str, account_id: str, statement_id: str, month: str, transactions: List[Dict[str, Any]]):
        # We loop and call the RPC for each extracted transaction
        for tx in transactions:
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
                    "p_amount": tx.get("amount", 0.0),
                    "p_currency": tx.get("currency", "TRY"),
                    "p_direction": tx.get("direction", "expense"),
                    "p_category": tx.get("category"),
                    "p_subcategory": tx.get("subcategory"),
                    "p_counterparty": tx.get("counterparty"),
                    "p_confidence_score": tx.get("confidence", 0.0),
                    "p_needs_review": True # Since it came from extraction
                }
            ).execute()

    def list_pending_drafts(self, statement_id: str) -> List[Dict[str, Any]]:
        # Usually from a view or the table directly
        response = self.db.table("transaction_drafts")\
            .select("*")\
            .eq("statement_id", statement_id)\
            .eq("review_status", "pending")\
            .execute()
        return response.data

    def approve_draft(self, draft_id: str, updates: ApproveDraftRequest = None) -> str:
        # Apply updates if any provided
        if updates:
            update_dict = updates.model_dump(exclude_unset=True)
            if update_dict:
                self.db.table("transaction_drafts").update(update_dict).eq("id", draft_id).execute()
        
        # Approve using RPC
        response = self.db.rpc("approve_transaction_draft", {"p_draft_id": draft_id}).execute()
        return response.data

    def reject_draft(self, draft_id: str, reason: str = None) -> bool:
        self.db.rpc("reject_transaction_draft", {"p_draft_id": draft_id, "p_reason": reason}).execute()
        return True
