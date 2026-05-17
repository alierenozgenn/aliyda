from supabase import Client
from typing import List, Dict, Any

class AccountService:
    def __init__(self, db: Client):
        # db must be a USER-SCOPED client (anon key + user JWT)
        # so that auth.uid() works inside the DB function
        self.db = db

    def create_account(
        self,
        name: str,
        account_type: str = "bank",
        institution_name: str = None,
        currency: str = "TRY",
    ) -> Dict[str, Any]:
        """
        Calls create_user_account(p_name, p_institution_name, p_account_type, p_currency).
        auth.uid() is resolved inside the DB function — client MUST be user-scoped.
        """
        response = self.db.rpc(
            "create_user_account",
            {
                "p_name": name,
                "p_institution_name": institution_name,
                "p_account_type": account_type,
                "p_currency": currency,
            }
        ).execute()

        account_id = response.data  # UUID string
        return self.get_account(account_id)

    def get_account(self, account_id: str) -> Dict[str, Any]:
        response = (
            self.db.table("accounts")
            .select("*")
            .eq("id", account_id)
            .single()
            .execute()
        )
        return response.data

    def list_accounts(self) -> List[Dict[str, Any]]:
        """RLS automatically scopes results to auth.uid() user."""
        response = (
            self.db.table("accounts")
            .select("*")
            .eq("is_active", True)
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []

    def archive_account(self, account_id: str) -> bool:
        self.db.table("accounts").update({"is_active": False}).eq("id", account_id).execute()
        return True
