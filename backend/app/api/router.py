from fastapi import APIRouter
from app.api.pdf import router as pdf_router
from app.api.transactions import router as transactions_router

api_router = APIRouter()

api_router.include_router(pdf_router, prefix="/pdf", tags=["pdf"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])