from fastapi import APIRouter, Depends
from typing import Dict, Any
from supabase import Client

from app.core.auth import get_current_user_id
from app.api.dependencies import get_db_client
from app.schemas.base import success_response, error_response, BaseResponse
from app.schemas.domain import ApproveDraftRequest, RejectDraftRequest
from app.services.draft_service import DraftService
from app.services.summary_service import SummaryService

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
    sum_service: SummaryService = Depends(get_summary_service)
):
    try:
        # draft_service will update the draft if data is provided, then approve it
        transaction_id = draft_service.approve_draft(draft_id, updates=data)
        
        # After approving, we should mark the summary as stale, but usually the db trigger does it.
        # Alternatively we can trigger recalculate if we want immediate consistency.
        # For performance, usually the frontend triggers recalculate at the end, 
        # or we just rely on the DB trigger marking it stale.
        
        return success_response(data=transaction_id, message="İşlem onaylandı.")
    except Exception as e:
        return error_response(code="DRAFT_APPROVE_ERROR", message=str(e))

@router.post("/{draft_id}/reject", response_model=BaseResponse[str])
async def reject_draft(
    draft_id: str,
    data: RejectDraftRequest = None,
    user_id: str = Depends(get_current_user_id),
    draft_service: DraftService = Depends(get_draft_service)
):
    try:
        reason = data.reason if data else None
        draft_service.reject_draft(draft_id, reason=reason)
        return success_response(message="İşlem reddedildi.")
    except Exception as e:
        return error_response(code="DRAFT_REJECT_ERROR", message=str(e))
