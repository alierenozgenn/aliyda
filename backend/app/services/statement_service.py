from supabase import Client
from typing import List, Dict, Any

class StatementService:
    def __init__(self, db: Client):
        self.db = db

    def create_statement(self, account_id: str, month: str, file_name: str = None, file_size_bytes: int = None) -> str:
        """
        Calls create_statement RPC.
        RPC signature: (p_account_id, p_month, p_source, p_file_name, p_file_mime_type, p_file_size_bytes)
        auth.uid() is resolved inside the DB function.
        """
        response = self.db.rpc(
            "create_statement",
            {
                "p_account_id": account_id,
                "p_month": month,
                "p_source": "pdf",
                "p_file_name": file_name,
                "p_file_mime_type": "application/pdf",
                "p_file_size_bytes": file_size_bytes,
            }
        ).execute()
        return response.data  # returns UUID string

    def update_statement_status(self, statement_id: str, status: str, error_message: str = None) -> bool:
        """
        Calls update_statement_status RPC.
        """
        self.db.rpc(
            "update_statement_status",
            {
                "p_statement_id": statement_id,
                "p_status": status,
                "p_error_message": error_message,
            }
        ).execute()
        return True

    def list_statements_by_month(self, month: str) -> List[Dict[str, Any]]:
        response = (
            self.db.table("statements")
            .select("*")
            .eq("month", month)
            .eq("is_deleted", False)
            .execute()
        )
        return response.data

    def get_statement(self, statement_id: str) -> Dict[str, Any]:
        response = self.db.table("statements").select("*").eq("id", statement_id).single().execute()
        return response.data

    def soft_delete_statement(self, statement_id: str, reason: str = "User deleted") -> bool:
        self.db.rpc(
            "soft_delete_statement",
            {
                "p_statement_id": statement_id,
                "p_reason": reason,
            }
        ).execute()
        return True
