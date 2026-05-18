from supabase import Client
from typing import List, Dict, Any


class AccountService:
    def __init__(self, db: Client):
        self.db = db

    def create_account(
        self,
        user_id: str,
        name: str,
        account_type: str = "bank",
        institution_name: str = None,
        currency: str = "TRY",
    ) -> Dict[str, Any]:
        """Direct insert with user_id — works with service role client."""
        response = (
            self.db.table("accounts")
            .insert({
                "user_id": user_id,
                "name": name,
                "account_type": account_type,
                "institution_name": institution_name,
                "currency": currency,
                "is_active": True,
            })
            .execute()
        )
        return response.data[0]

    def get_account(self, account_id: str) -> Dict[str, Any]:
        response = (
            self.db.table("accounts")
            .select("*")
            .eq("id", account_id)
            .single()
            .execute()
        )
        return response.data

    def list_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        response = (
            self.db.table("accounts")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []

    def update_account(
        self,
        user_id: str,
        account_id: str,
        name: str = None,
        account_type: str = None,
        institution_name: str = None,
        currency: str = None,
    ) -> Dict[str, Any]:
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if account_type is not None:
            update_data["account_type"] = account_type
        if institution_name is not None:
            update_data["institution_name"] = institution_name
        if currency is not None:
            update_data["currency"] = currency

        if update_data:
            self.db.table("accounts").update(update_data).eq("id", account_id).eq("user_id", user_id).execute()

        return self.get_account(account_id)

    def archive_account(self, user_id: str, account_id: str) -> bool:
        self.db.table("accounts").update({"is_active": False}).eq("id", account_id).eq("user_id", user_id).execute()
        return True
