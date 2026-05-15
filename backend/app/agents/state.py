from typing import TypedDict, Optional, List

class FinanceAgentState(TypedDict):
    pdf_bytes: Optional[bytes]
    user_id: str
    upload_id: str
    raw_transactions: Optional[List[dict]]
    extraction_error: Optional[str]
    valid_transactions: Optional[List[dict]]
    invalid_transactions: Optional[List[dict]]
    categorized_transactions: Optional[List[dict]]
    anomalies: Optional[List[dict]]
    financial_summary: Optional[dict]
    insight_text: Optional[str]
    retry_count: int
    status: str
