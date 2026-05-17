from fastapi import APIRouter
from app.api import accounts, transactions, dashboard, statements, drafts, chat, insights

api_router = APIRouter()

# -- Accounts --
api_router.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])

# -- Statements (PDF upload + status) --
api_router.include_router(statements.router, prefix="/statements", tags=["Statements"])

# -- Drafts (approve/reject) --
api_router.include_router(drafts.router, prefix="/drafts", tags=["Drafts"])

# -- Transactions (manual + list + CRUD) --
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])

# -- Dashboard & Monthly Profile --
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

# -- Insights (AI-generated, DB-based) --
api_router.include_router(insights.router, prefix="/insights", tags=["Insights"])

# -- Chat --
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])