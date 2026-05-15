from pydantic import BaseModel, validator
from typing import Optional
from datetime import date

class TransactionCreate(BaseModel):
    date: date
    description: str
    amount: float
    direction: str
    category_id: Optional[str] = None
    source: str = "manual"

class TransactionUpdate(BaseModel):
    category_id: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    direction: Optional[str] = None
    date: Optional[date] = None
    is_verified: Optional[bool] = None

class PDFTransactionItem(BaseModel):
    date: str
    description: str
    amount: float
    direction: str
    estimated_category: str
    confidence: float
    raw_text: Optional[str] = None

    @validator('direction')
    def check_direction(cls, v):
        if v not in ('income', 'expense'):
            raise ValueError("direction must be income or expense")
        return v

    @validator('confidence')
    def check_confidence(cls, v):
        if not (0 <= v <= 1):
            raise ValueError("confidence must be between 0 and 1")
        return v
