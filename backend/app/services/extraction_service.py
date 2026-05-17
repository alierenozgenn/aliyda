from supabase import Client
from typing import Dict, Any

class ExtractionService:
    def __init__(self, db: Client):
        self.db = db

    def save_statement_extraction(
        self, 
        statement_id: str, 
        provider: str, 
        model: str, 
        raw_output: str, 
        parsed_output: Dict[str, Any], 
        status: str = "success", 
        error_message: str = None
    ) -> str:
        # Using RPC as defined in supabase/migrations/034_save_statement_extraction_function.sql
        response = self.db.rpc(
            "save_statement_extraction",
            {
                "p_statement_id": statement_id,
                "p_provider": provider,
                "p_model": model,
                "p_prompt_version": "v1.0", # Could make this dynamic
                "p_raw_output": raw_output,
                "p_parsed_output": parsed_output,
                "p_status": status,
                "p_error_message": error_message
            }
        ).execute()
        return response.data
