from fastapi import APIRouter, Depends
from typing import Dict, Any
from supabase import Client

from app.core.auth import get_current_user_id
from app.api.dependencies import get_db_client
from app.schemas.base import success_response, error_response, BaseResponse
from app.schemas.domain import ApproveDraftRequest, RejectDraftRequest
from app.services.draft_service import DraftService
from app.services.summary_service import SummaryService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def get_draft_service(db: Client = Depends(get_db_client)) -> DraftService:
    return DraftService(db)


def get_summary_service(db: Client = Depends(get_db_client)) -> SummaryService:
    return SummaryService(db)


@router.post("/{draft_id}/approve", response_model=BaseResponse[str])
async def approve_draft(
    draft_id: str,
    data: ApproveDraftRequest = None,
    user_id: str = Depends(get_current_user_id),
    draft_service: DraftService = Depends(get_draft_service),
    sum_service: SummaryService = Depends(get_summary_service),
):
    try:
        result = draft_service.approve_draft(user_id=user_id, draft_id=draft_id, updates=data)
        tx_id = result["transaction_id"]
        month = result["month"]
        try:
            sum_service.recalculate_monthly_summary(user_id, month)
        except Exception as e:
            logger.error(f"Summary recalc failed after approve: {e}")
        return success_response(data=str(tx_id), message="İşlem onaylandı.")
    except Exception as e:
        return error_response(code="DRAFT_APPROVE_ERROR", message=str(e))


@router.post("/{draft_id}/reject", response_model=BaseResponse[str])
async def reject_draft(
    draft_id: str,
    data: RejectDraftRequest = None,
    user_id: str = Depends(get_current_user_id),
    draft_service: DraftService = Depends(get_draft_service),
):
    try:
        reason = data.reason if data else None
        draft_service.reject_draft(user_id=user_id, draft_id=draft_id, reason=reason)
        return success_response(message="İşlem reddedildi.")
    except Exception as e:
        return error_response(code="DRAFT_REJECT_ERROR", message=str(e))
