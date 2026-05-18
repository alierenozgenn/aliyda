from supabase import Client
from typing import List, Dict, Any
from app.schemas.domain import ManualTransactionCreate, TransactionUpdateRequest


class TransactionService:
    def __init__(self, db: Client):
        self.db = db

    def create_manual_transaction(self, user_id: str, data: ManualTransactionCreate) -> str:
        response = self.db.rpc(
            "create_manual_transaction",
            {
                "p_user_id": user_id,
                "p_account_id": data.account_id,
                "p_transaction_date": data.transaction_date,
                "p_transaction_time": data.transaction_time,
                "p_description": data.description,
                "p_amount": data.amount,
                "p_direction": data.direction,
                "p_category": data.category,
                "p_counterparty": data.counterparty,
            }
        ).execute()
        return response.data

    def list_transactions(self, user_id: str, month: str) -> List[Dict[str, Any]]:
        response = (
            self.db.table("v_confirmed_transactions")
            .select("*")
            .eq("user_id", user_id)
            .eq("month", month)
            .order("transaction_date", desc=True)
            .execute()
        )
        return response.data

    def update_transaction(self, user_id: str, transaction_id: str, data: TransactionUpdateRequest) -> bool:
        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            return True
        rpc_params = {
            "p_transaction_id": transaction_id,
            "p_transaction_date": data.transaction_date,
            "p_transaction_time": data.transaction_time,
            "p_description": data.description,
            "p_amount": data.amount,
            "p_direction": data.direction,
            "p_category": data.category,
            "p_counterparty": data.counterparty,
            "p_subcategory": None,
            "p_payment_method": None,
            "p_location": None,
            "p_is_excluded_from_budget": None,
        }
        self.db.rpc("update_transaction_details", rpc_params).execute()
        return True

    def soft_delete_transaction(self, user_id: str, transaction_id: str, reason: str = "User deleted") -> bool:
        self.db.rpc(
            "soft_delete_transaction",
            {"p_user_id": user_id, "p_transaction_id": transaction_id, "p_reason": reason}
        ).execute()
        return True

    def restore_transaction(self, user_id: str, transaction_id: str) -> bool:
        self.db.rpc(
            "restore_transaction",
            {"p_user_id": user_id, "p_transaction_id": transaction_id}
        ).execute()
        return True

    def get_transaction_month(self, transaction_id: str) -> str:
        """Gets the month of a transaction (for summary recalc)."""
        res = (
            self.db.table("transactions")
            .select("month")
            .eq("id", transaction_id)
            .single()
            .execute()
        )
        return res.data.get("month") if res.data else None
