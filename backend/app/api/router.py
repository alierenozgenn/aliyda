from fastapi import APIRouter
from app.api.pdf import router as pdf_router

api_router = APIRouter()

api_router.include_router(pdf_router, prefix="/pdf", tags=["pdf"])