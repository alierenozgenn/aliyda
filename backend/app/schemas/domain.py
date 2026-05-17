from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import date, time

# -- Accounts --
class AccountCreate(BaseModel):
    name: str
    type: str = "checking"
    currency: str = "TRY"
    balance: float = 0.0

# -- Statements --
class StatementCreate(BaseModel):
    month: str
    account_id: str

class PDFUploadResponse(BaseModel):
    statement_id: str
    status: str
    message: str

# -- Drafts --
class TransactionDraftResponse(BaseModel):
    id: str
    transaction_date: date
    transaction_time: Optional[time]
    description: str
    amount: float
    direction: str
    category: Optional[str]
    subcategory: Optional[str]
    counterparty: Optional[str]
    confidence_score: Optional[float]
    review_status: str

class ApproveDraftRequest(BaseModel):
    # Optional fields to allow editing before approval
    transaction_date: Optional[date] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    direction: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    counterparty: Optional[str] = None

class RejectDraftRequest(BaseModel):
    reason: Optional[str] = None

# -- Transactions --
class ManualTransactionCreate(BaseModel):
    account_id: str
    transaction_date: date
    transaction_time: Optional[time] = None
    description: str
    amount: float
    direction: str
    category: Optional[str] = None
    counterparty: Optional[str] = None

class TransactionUpdateRequest(BaseModel):
    transaction_date: Optional[date] = None
    transaction_time: Optional[time] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    direction: Optional[str] = None
    category: Optional[str] = None
    counterparty: Optional[str] = None

# -- Monthly Profiles & Dashboard --
class MonthlyProfileUpsert(BaseModel):
    month: str
    declared_income: float
    savings_goal: Optional[float] = None
    budget_goal: Optional[float] = None

class MonthlyDashboardResponse(BaseModel):
    month: str
    total_income: float
    total_expense: float
    net_balance: float
    top_categories: Any
    largest_transactions: Any
    is_stale: bool

# -- AI Insights & Chat --
class InsightResponse(BaseModel):
    insight_text: str
    generated_at: str
    is_stale: bool

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    month: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    answer: str
