from fastapi import APIRouter, Depends, Query
from typing import Dict, Any
from supabase import Client

from app.core.auth import get_current_user_id
from app.api.dependencies import get_db_client
from app.schemas.base import success_response, error_response, BaseResponse
from app.services.insight_service import InsightService
from app.services.summary_service import SummaryService
from app.services.gemini_service import GeminiService, GEMINI_MODEL

router = APIRouter()

def get_insight_service(db: Client = Depends(get_db_client)) -> InsightService:
    return InsightService(db)

def get_summary_service(db: Client = Depends(get_db_client)) -> SummaryService:
    return SummaryService(db)


@router.post("/monthly", response_model=BaseResponse[Dict[str, Any]])
async def generate_monthly_insight(
    month: str = Query(..., description="Format: YYYY-MM"),
    force_refresh: bool = Query(False),
    user_id: str = Depends(get_current_user_id),
    insight_service: InsightService = Depends(get_insight_service),
    sum_service: SummaryService = Depends(get_summary_service)
):
    try:
        # 1. Check if there's a fresh insight already
        if not force_refresh:
            existing = insight_service.get_latest_insight(user_id=user_id, month=month)
            if existing and not existing.get("is_stale"):
                return success_response(data=existing, message="Mevcut güncel yorum kullanılıyor.")

        # 2. Get fresh dashboard data (source of truth is DB, not Gemini)
        sum_service.ensure_summary_fresh(user_id, month)
        dashboard = sum_service.get_monthly_dashboard(user_id=user_id, month=month)

        if not dashboard:
            return error_response(
                code="NO_DATA",
                message="Bu ay için veri yok. Önce işlem ekleyin."
            )

        # 3. Generate Gemini insight based only on deterministic DB data
        gemini = GeminiService()
        insight_text = gemini.generate_monthly_insight(dashboard)

        # 4. Save insight to DB
        insight = insight_service.save_insight(
            user_id=user_id,
            month=month,
            insight_text=insight_text,
            model_used=GEMINI_MODEL,
            prompt_version="v3.1"
        )

        return success_response(data=insight, message="Yorum üretildi.")

    except Exception as e:
        return error_response(code="INSIGHT_ERROR", message=str(e))
