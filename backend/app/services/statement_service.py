from supabase import Client
from typing import List, Dict, Any


class StatementService:
    def __init__(self, db: Client):
        self.db = db

    def create_statement(self, user_id: str, account_id: str, month: str, file_name: str = None, file_size_bytes: int = None) -> str:
        """Direct insert - bypasses auth.uid() issue with service role."""
        response = (
            self.db.table("statements")
            .insert({
                "user_id": user_id,
                "account_id": account_id,
                "month": month,
                "source": "pdf",
                "file_name": file_name,
                "file_mime_type": "application/pdf",
                "file_size_bytes": file_size_bytes,
                "status": "uploaded",
            })
            .execute()
        )
        return response.data[0]["id"]

    def update_statement_status(self, statement_id: str, status: str, error_message: str = None) -> bool:
        update = {"status": status}
        if error_message:
            update["error_message"] = error_message[:500]
        self.db.table("statements").update(update).eq("id", statement_id).execute()
        return True

    def list_statements_by_month(self, user_id: str, month: str) -> List[Dict[str, Any]]:
        response = (
            self.db.table("statements")
            .select("*")
            .eq("user_id", user_id)
            .eq("month", month)
            .eq("is_deleted", False)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def get_statement(self, statement_id: str) -> Dict[str, Any]:
        response = self.db.table("statements").select("*").eq("id", statement_id).single().execute()
        return response.data

    def soft_delete_statement(self, statement_id: str, reason: str = "User deleted") -> bool:
        self.db.table("statements").update({
            "is_deleted": True,
            "deleted_at": "now()",
            "deleted_reason": reason,
        }).eq("id", statement_id).execute()
        return True
