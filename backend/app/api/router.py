from fastapi import APIRouter
from app.api.pdf import router as pdf_router
from app.api.transactions import router as transactions_router
from app.api.analytics import router as analytics_router


api_router = APIRouter()

api_router.include_router(pdf_router, prefix="/pdf", tags=["pdf"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])