import os
import uuid
import logging
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from typing import Dict, Any, List
from supabase import Client

from app.core.auth import get_current_user_id
from app.api.dependencies import get_db_client
from app.schemas.base import success_response, error_response, BaseResponse
from app.services.statement_service import StatementService
from app.services.extraction_service import ExtractionService
from app.services.draft_service import DraftService
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_statement_service(db: Client = Depends(get_db_client)) -> StatementService:
    return StatementService(db)

def get_extraction_service(db: Client = Depends(get_db_client)) -> ExtractionService:
    return ExtractionService(db)

def get_draft_service(db: Client = Depends(get_db_client)) -> DraftService:
    return DraftService(db)


@router.post("/upload", response_model=BaseResponse[Dict[str, Any]])
async def upload_statement(
    month: str = Form(...),
    account_id: str = Form(...),
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    stmt_service: StatementService = Depends(get_statement_service),
    ext_service: ExtractionService = Depends(get_extraction_service),
    draft_service: DraftService = Depends(get_draft_service),
):
    gemini_service = GeminiService()
    statement_id = None
    temp_path = ""
    try:
        # 1. Read file
        file_content = await file.read()
        if not file_content:
            return error_response(code="EMPTY_FILE", message="Yüklenen PDF dosyası boş.")

        logger.info(f"PDF yükleniyor: {file.filename} ({len(file_content)} bytes) - user={user_id}")

        # 2. Create statement record
        statement_id = stmt_service.create_statement(
            account_id=account_id,
            month=month,
            file_name=file.filename,
            file_size_bytes=len(file_content),
        )
        logger.info(f"Statement kaydı oluşturuldu: {statement_id}")

        # 3. Mark as extracting
        stmt_service.update_statement_status(statement_id, "extracting")

        # 4. Write temp file
        os.makedirs("temp", exist_ok=True)
        safe_name = f"{uuid.uuid4()}_{file.filename}"
        temp_path = os.path.join("temp", safe_name)
        with open(temp_path, "wb") as buffer:
            buffer.write(file_content)
        logger.info(f"Temp dosya yazıldı: {temp_path}")

        # 5. Gemini extraction
        logger.info("Gemini PDF extraction başlatılıyor...")
        extracted_data = gemini_service.extract_transactions_from_pdf(temp_path)
        transactions = extracted_data.get("transactions", [])
        logger.info(f"Gemini {len(transactions)} işlem çıkardı.")

        # 6. Save raw extraction log
        ext_service.save_statement_extraction(
            statement_id=statement_id,
            provider="gemini",
            model="gemini-2.0-flash",
            raw_output=str(extracted_data)[:4000],
            parsed_output=extracted_data,
        )

        # 7. Create drafts (pending review)
        if transactions:
            draft_service.create_drafts_from_extraction(
                user_id=user_id,
                account_id=account_id,
                statement_id=statement_id,
                month=month,
                transactions=transactions,
            )

        # 8. Mark as pending_review
        stmt_service.update_statement_status(statement_id, "pending_review")
        logger.info(f"PDF işlendi başarıyla. {len(transactions)} draft oluşturuldu.")

        return success_response(
            data={"statement_id": statement_id, "draft_count": len(transactions)},
            message=f"PDF işlendi. {len(transactions)} işlem onayınızı bekliyor.",
        )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"PDF upload hatası: {error_msg}", exc_info=True)

        if statement_id:
            try:
                stmt_service.update_statement_status(statement_id, "failed", error_msg[:500])
            except Exception as inner_e:
                logger.error(f"Status update failed: {inner_e}")

        return error_response(code="UPLOAD_ERROR", message=f"PDF işlenemedi: {error_msg}")

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
            logger.info(f"Temp dosya silindi: {temp_path}")


@router.get("", response_model=BaseResponse[List[Dict[str, Any]]])
async def list_statements(
    month: str = Query(...),
    user_id: str = Depends(get_current_user_id),
    stmt_service: StatementService = Depends(get_statement_service),
):
    try:
        statements = stmt_service.list_statements_by_month(month)
        return success_response(data=statements)
    except Exception as e:
        return error_response(code="STATEMENT_LIST_ERROR", message=str(e))


@router.get("/{statement_id}/drafts", response_model=BaseResponse[List[Dict[str, Any]]])
async def list_drafts(
    statement_id: str,
    user_id: str = Depends(get_current_user_id),
    draft_service: DraftService = Depends(get_draft_service),
):
    try:
        drafts = draft_service.list_pending_drafts(statement_id)
        return success_response(data=drafts)
    except Exception as e:
        return error_response(code="DRAFT_LIST_ERROR", message=str(e))


@router.post("/{statement_id}/finalize", response_model=BaseResponse[str])
async def finalize_statement(
    statement_id: str,
    user_id: str = Depends(get_current_user_id),
    stmt_service: StatementService = Depends(get_statement_service),
    draft_service: DraftService = Depends(get_draft_service),
):
    try:
        pending = draft_service.list_pending_drafts(statement_id)
        if pending:
            return error_response(
                code="STATEMENT_HAS_PENDING",
                message=f"{len(pending)} işlem henüz onaylanmadı veya reddedilmedi.",
            )
        stmt_service.update_statement_status(statement_id, "approved")
        return success_response(data=statement_id, message="Statement tamamlandı.")
    except Exception as e:
        return error_response(code="STATEMENT_FINALIZE_ERROR", message=str(e))
