from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List
from supabase import Client

from app.core.auth import get_current_user_id
from app.api.dependencies import get_db_client
from app.schemas.domain import ManualTransactionCreate, TransactionUpdateRequest
from app.schemas.base import success_response, error_response, BaseResponse
from app.services.transaction_service import TransactionService
from app.services.summary_service import SummaryService

router = APIRouter()

def get_tx_service(db: Client = Depends(get_db_client)) -> TransactionService:
    return TransactionService(db)

def get_summary_service(db: Client = Depends(get_db_client)) -> SummaryService:
    return SummaryService(db)

@router.post("/manual", response_model=BaseResponse[str])
async def create_manual_transaction(
    month: str,
    data: ManualTransactionCreate,
    user_id: str = Depends(get_current_user_id),
    tx_service: TransactionService = Depends(get_tx_service),
    sum_service: SummaryService = Depends(get_summary_service)
):
    try:
        tx_id = tx_service.create_manual_transaction(user_id=user_id, month=month, data=data)
        # Recalculate summary since a manual transaction affects the dashboard immediately
        sum_service.recalculate_monthly_summary(user_id=user_id, month=month)
        return success_response(data=tx_id, message="İşlem başarıyla eklendi.")
    except Exception as e:
        return error_response(code="TRANSACTION_CREATE_ERROR", message=str(e))

@router.get("", response_model=BaseResponse[List[Dict[str, Any]]])
async def list_transactions(
    month: str = Query(..., description="Format: YYYY-MM"),
    user_id: str = Depends(get_current_user_id),
    tx_service: TransactionService = Depends(get_tx_service)
):
    try:
        transactions = tx_service.list_transactions(month=month)
        return success_response(data=transactions)
    except Exception as e:
        return error_response(code="TRANSACTION_LIST_ERROR", message=str(e))


@router.patch("/{transaction_id}", response_model=BaseResponse[str])
async def update_transaction(
    transaction_id: str,
    data: TransactionUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    tx_service: TransactionService = Depends(get_tx_service),
    sum_service: SummaryService = Depends(get_summary_service)
):
    try:
        tx_service.update_transaction(transaction_id, data)
        # If date changes the month, both months need recalc — but for now recalc the current month
        # The DB trigger marks summary as stale automatically, recalculate is optional here
        return success_response(data=transaction_id, message="İşlem güncellendi.")
    except Exception as e:
        return error_response(code="TRANSACTION_UPDATE_ERROR", message=str(e))


@router.delete("/{transaction_id}", response_model=BaseResponse[str])
async def delete_transaction(
    transaction_id: str,
    user_id: str = Depends(get_current_user_id),
    tx_service: TransactionService = Depends(get_tx_service)
):
    try:
        tx_service.soft_delete_transaction(transaction_id)
        # DB trigger marks summary stale automatically
        return success_response(data=transaction_id, message="İşlem silindi.")
    except Exception as e:
        return error_response(code="TRANSACTION_DELETE_ERROR", message=str(e))


@router.post("/{transaction_id}/restore", response_model=BaseResponse[str])
async def restore_transaction(
    transaction_id: str,
    user_id: str = Depends(get_current_user_id),
    tx_service: TransactionService = Depends(get_tx_service)
):
    try:
        tx_service.restore_transaction(transaction_id)
        return success_response(data=transaction_id, message="İşlem geri alındı.")
    except Exception as e:
        return error_response(code="TRANSACTION_RESTORE_ERROR", message=str(e))
