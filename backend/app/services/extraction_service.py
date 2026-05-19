from supabase import Client
from typing import Dict, Any

class ExtractionService:
    def __init__(self, db: Client):
        self.db = db

    def save_statement_extraction(
        self, 
        user_id: str,
        statement_id: str, 
        provider: str, 
        model: str, 
        raw_output: Any, 
        parsed_output: Dict[str, Any], 
        status: str = "success", 
        error_message: str = None
    ) -> str:
        # Service-role callers must pass user_id explicitly; auth.uid() is not available.
        raw_output_json = raw_output if isinstance(raw_output, dict) else {"text": str(raw_output)}
        response = self.db.rpc(
            "save_statement_extraction",
            {
                "p_user_id": user_id,
                "p_statement_id": statement_id,
                "p_provider": provider,
                "p_model": model,
                "p_prompt_version": "v2.0",
                "p_raw_output": raw_output_json,
                "p_parsed_output": parsed_output,
                "p_status": status,
                "p_error_message": error_message
            }
        ).execute()
        return response.data
