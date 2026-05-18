from supabase import Client
from typing import List, Dict, Any, Optional
from app.schemas.domain import ManualTransactionCreate, TransactionUpdateRequest


class TransactionService:
    def __init__(self, db: Client):
        self.db = db

    def create_manual_transaction(self, user_id: str, data: ManualTransactionCreate) -> str:
        """Manuel işlem oluşturur. date/time nesneleri serialize edilir."""
        tx_date = data.transaction_date.isoformat() if hasattr(data.transaction_date, 'isoformat') else str(data.transaction_date)
        tx_time = None
        if data.transaction_time:
            tx_time = data.transaction_time.isoformat() if hasattr(data.transaction_time, 'isoformat') else str(data.transaction_time)

        response = self.db.rpc(
            "create_manual_transaction",
            {
                "p_user_id": user_id,
                "p_account_id": data.account_id,
                "p_transaction_date": tx_date,
                "p_transaction_time": tx_time,
                "p_description": data.description,
                "p_amount": float(data.amount),
                "p_direction": data.direction,
                "p_category": data.category,
                "p_counterparty": data.counterparty,
            }
        ).execute()
        return response.data

    def list_transactions(self, user_id: str, month: str) -> List[Dict[str, Any]]:
        """v_confirmed_transactions view'ını kullanır — sadece onaylı ve silinmemiş işlemler."""
        response = (
            self.db.table("v_confirmed_transactions")
            .select("*")
            .eq("user_id", user_id)
            .eq("month", month)
            .order("transaction_date", desc=True)
            .execute()
        )
        return response.data or []

    def list_all_transactions(self, user_id: str, month: str) -> List[Dict[str, Any]]:
        """Tüm işlemler (silinmişler dahil) — İşlemlerim sayfası için."""
        response = (
            self.db.table("transactions")
            .select("*")
            .eq("user_id", user_id)
            .eq("month", month)
            .order("transaction_date", desc=True)
            .execute()
        )
        return response.data or []

    def update_transaction(self, user_id: str, transaction_id: str, data: TransactionUpdateRequest) -> bool:
        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            return True

        # Serialize date/time objects
        tx_date = None
        tx_time = None
        if data.transaction_date is not None:
            tx_date = data.transaction_date.isoformat() if hasattr(data.transaction_date, 'isoformat') else str(data.transaction_date)
        if data.transaction_time is not None:
            tx_time = data.transaction_time.isoformat() if hasattr(data.transaction_time, 'isoformat') else str(data.transaction_time)

        rpc_params = {
            "p_transaction_id": transaction_id,
            "p_transaction_date": tx_date,
            "p_transaction_time": tx_time,
            "p_description": data.description,
            "p_amount": float(data.amount) if data.amount is not None else None,
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

    def get_transaction_month(self, transaction_id: str) -> Optional[str]:
        """Gets the month of a transaction (for summary recalc)."""
        try:
            res = (
                self.db.table("transactions")
                .select("month")
                .eq("id", transaction_id)
                .single()
                .execute()
            )
            return res.data.get("month") if res.data else None
        except Exception:
            return None
