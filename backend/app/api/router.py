from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/")
def read_root():
    return {"message": "Aliyda Backend Calisiyor!"}


@api_router.get("/health")
def health_check():
    return {"status": "healthy"}  # Backend kontrolü için [cite: 300]