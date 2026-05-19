from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.api import router
from app.core.error_handler import validation_exception_handler, general_exception_handler

def _build_cors_origins() -> list[str]:
    origins = [
        origin.strip().rstrip("/")
        for origin in settings.FRONTEND_URL.split(",")
        if origin.strip()
    ]
    if settings.APP_ENV != "production":
        origins.extend([
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ])
    return sorted(set(origins))

app = FastAPI(title="Aliyda API", version="1.0.0")

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router.api_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.APP_ENV}
