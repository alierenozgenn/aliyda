from fastapi import APIRouter, Depends
from typing import Dict, Any, List, Optional
from supabase import Client
from pydantic import BaseModel

from app.core.auth import get_current_user_id
from app.api.dependencies import get_db_client
from app.schemas.base import success_response, error_response, BaseResponse
from app.services.account_service import AccountService

router = APIRouter()

# Valid account types from DB check constraint
VALID_ACCOUNT_TYPES = ("bank", "credit_card", "cash", "manual", "wallet", "other")

class AccountCreateRequest(BaseModel):
    name: str
    account_type: str = "bank"
    institution_name: Optional[str] = None
    currency: str = "TRY"

class AccountUpdateRequest(BaseModel):
    name: Optional[str] = None
    account_type: Optional[str] = None
    institution_name: Optional[str] = None
    currency: Optional[str] = None

def get_account_service(db: Client = Depends(get_db_client)) -> AccountService:
    # get_db_client returns user-scoped client — correct for auth.uid() to work
    return AccountService(db)


@router.post("", response_model=BaseResponse[Dict[str, Any]])
async def create_account(
    data: AccountCreateRequest,
    user_id: str = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service),
):
    if data.account_type not in VALID_ACCOUNT_TYPES:
        return error_response(
            code="INVALID_ACCOUNT_TYPE",
            message=f"Geçersiz hesap türü. Olası değerler: {', '.join(VALID_ACCOUNT_TYPES)}"
        )
    try:
        account = service.create_account(
            name=data.name,
            account_type=data.account_type,
            institution_name=data.institution_name or None,
            currency=data.currency,
        )
        return success_response(data=account, message="Hesap başarıyla oluşturuldu.")
    except Exception as e:
        return error_response(code="ACCOUNT_CREATE_ERROR", message=str(e))


@router.get("", response_model=BaseResponse[List[Dict[str, Any]]])
async def list_accounts(
    user_id: str = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service),
):
    try:
        accounts = service.list_accounts()
        return success_response(data=accounts)
    except Exception as e:
        return error_response(code="ACCOUNT_LIST_ERROR", message=str(e))


@router.patch("/{account_id}", response_model=BaseResponse[Dict[str, Any]])
async def update_account(
    account_id: str,
    data: AccountUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service),
):
    if data.account_type is not None and data.account_type not in VALID_ACCOUNT_TYPES:
        return error_response(
            code="INVALID_ACCOUNT_TYPE",
            message=f"Geçersiz hesap türü. Olası değerler: {', '.join(VALID_ACCOUNT_TYPES)}"
        )
    try:
        account = service.update_account(
            account_id=account_id,
            name=data.name,
            account_type=data.account_type,
            institution_name=data.institution_name,
            currency=data.currency,
        )
        return success_response(data=account, message="Hesap başarıyla güncellendi.")
    except Exception as e:
        return error_response(code="ACCOUNT_UPDATE_ERROR", message=str(e))


@router.delete("/{account_id}", response_model=BaseResponse[str])
async def archive_account(
    account_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service),
):
    try:
        service.archive_account(account_id)
        return success_response(data=account_id, message="Hesap devre dışı bırakıldı.")
    except Exception as e:
        return error_response(code="ACCOUNT_ARCHIVE_ERROR", message=str(e))
