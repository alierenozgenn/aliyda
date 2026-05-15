from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.api import router
from app.core.error_handler import validation_exception_handler, general_exception_handler

app = FastAPI(title="Aliyda API", version="1.0.0")

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router.api_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.APP_ENV}