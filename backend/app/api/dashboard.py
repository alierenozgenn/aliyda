from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, Optional
from supabase import Client

from app.core.auth import get_current_user_id
from app.api.dependencies import get_db_client
from app.schemas.domain import MonthlyProfileUpsert
from app.schemas.base import success_response, error_response, BaseResponse
from app.services.summary_service import SummaryService
from app.services.monthly_profile_service import MonthlyProfileService
from app.services.transaction_service import TransactionService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def get_summary_service(db: Client = Depends(get_db_client)) -> SummaryService:
    return SummaryService(db)


def get_profile_service(db: Client = Depends(get_db_client)) -> MonthlyProfileService:
    return MonthlyProfileService(db)


def get_tx_service(db: Client = Depends(get_db_client)) -> TransactionService:
    return TransactionService(db)


@router.get("", response_model=BaseResponse[Dict[str, Any]])
async def get_dashboard(
    month: str = Query(..., description="Format: YYYY-MM"),
    user_id: str = Depends(get_current_user_id),
    sum_service: SummaryService = Depends(get_summary_service),
    tx_service: TransactionService = Depends(get_tx_service),
    profile_service: MonthlyProfileService = Depends(get_profile_service),
):
    try:
        sum_service.ensure_summary_fresh(user_id, month)
        dashboard_data = sum_service.get_monthly_dashboard(user_id, month)
        if not dashboard_data:
            return success_response(data=None, message="Bu ay için henüz veri yok.")
        
        # Enrich with recent transactions
        recent_txs = tx_service.list_transactions(user_id, month)
        dashboard_data["recent_transactions"] = recent_txs[:10] if recent_txs else []
        dashboard_data["transaction_count"] = len(recent_txs) if recent_txs else 0
        
        # Enrich with monthly profile (income source, goals)
        profile = profile_service.get_monthly_profile(user_id, month)
        if profile:
            dashboard_data["declared_income"] = profile.get("declared_income")
            dashboard_data["income_source"] = profile.get("income_source")
            dashboard_data["savings_goal"] = profile.get("savings_goal")
            dashboard_data["budget_goal"] = profile.get("budget_goal")
        
        return success_response(data=dashboard_data)
    except Exception as e:
        logger.error(f"Dashboard hatası: {e}", exc_info=True)
        return error_response(code="DASHBOARD_ERROR", message=str(e))


@router.put("/profile/{month}", response_model=BaseResponse[str])
async def upsert_monthly_profile(
    month: str,
    data: MonthlyProfileUpsert,
    user_id: str = Depends(get_current_user_id),
    profile_service: MonthlyProfileService = Depends(get_profile_service),
    sum_service: SummaryService = Depends(get_summary_service),
):
    try:
        data.month = month
        profile_id = profile_service.upsert_monthly_profile(user_id=user_id, data=data)
        sum_service.recalculate_monthly_summary(user_id, month)
        return success_response(data=profile_id, message="Aylık profil güncellendi.")
    except Exception as e:
        return error_response(code="PROFILE_UPSERT_ERROR", message=str(e))
