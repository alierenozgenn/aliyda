from supabase import Client
from typing import List, Dict, Any
from app.schemas.domain import ManualTransactionCreate, TransactionUpdateRequest

class TransactionService:
    def __init__(self, db: Client):
        self.db = db

    def create_manual_transaction(self, user_id: str, month: str, data: ManualTransactionCreate) -> str:
        # Using RPC as defined in supabase/migrations/026_create_manual_transaction_function.sql
        response = self.db.rpc(
            "create_manual_transaction",
            {
                "p_user_id": user_id,
                "p_account_id": data.account_id,
                "p_month": month,
                "p_transaction_date": data.transaction_date,
                "p_transaction_time": data.transaction_time,
                "p_description": data.description,
                "p_amount": data.amount,
                "p_direction": data.direction,
                "p_category": data.category,
                "p_counterparty": data.counterparty
            }
        ).execute()
        return response.data

    def list_transactions(self, month: str) -> List[Dict[str, Any]]:
        # Using view v_confirmed_transactions for clean user history
        response = self.db.table("v_confirmed_transactions")\
            .select("*")\
            .eq("month", month)\
            .order("transaction_date", desc=True)\
            .execute()
        return response.data

    def update_transaction(self, transaction_id: str, data: TransactionUpdateRequest) -> bool:
        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            return True
            
        # Using RPC as defined in supabase/migrations/027_update_transaction_details_function.sql
        # Note: we need to pass individual fields according to the RPC. 
        # For simplicity, if we don't have all, we can fallback to normal update or map the RPC parameters.
        # RPC parameters: p_transaction_id, p_transaction_date, p_transaction_time, p_description, p_amount, p_direction, p_category, p_subcategory, p_counterparty, p_payment_method, p_location, p_is_excluded_from_budget
        # The RPC provides a cleaner interface and maintains last_modified_at and stale triggers.
        
        rpc_params = {
            "p_transaction_id": transaction_id,
            "p_transaction_date": data.transaction_date,
            "p_transaction_time": data.transaction_time,
            "p_description": data.description,
            "p_amount": data.amount,
            "p_direction": data.direction,
            "p_category": data.category,
            "p_counterparty": data.counterparty,
            # For unmapped optional fields, we send None
            "p_subcategory": None,
            "p_payment_method": None,
            "p_location": None,
            "p_is_excluded_from_budget": None
        }
        
        self.db.rpc("update_transaction_details", rpc_params).execute()
        return True

    def soft_delete_transaction(self, transaction_id: str, reason: str = "User deleted") -> bool:
        self.db.rpc("soft_delete_transaction", {"p_transaction_id": transaction_id, "p_reason": reason}).execute()
        return True

    def restore_transaction(self, transaction_id: str) -> bool:
        self.db.rpc("restore_transaction", {"p_transaction_id": transaction_id}).execute()
        return True
