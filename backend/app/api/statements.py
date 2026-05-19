import os
import uuid
import logging
from fastapi.concurrency import run_in_threadpool
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from typing import Dict, Any, List
from supabase import Client

from app.core.auth import get_current_user_id
from app.api.dependencies import get_db_client
from app.schemas.base import success_response, error_response, BaseResponse
from app.services.statement_service import StatementService
from app.services.extraction_service import ExtractionService
from app.services.draft_service import DraftService
from app.services.gemini_service import GeminiService, GEMINI_MODEL

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
    statement_id = None
    temp_path = ""
    try:
        gemini_service = GeminiService()

        # 1. Read file
        file_content = await file.read()
        if not file_content:
            return error_response(code="EMPTY_FILE", message="Yüklenen PDF dosyası boş.")

        logger.info(f"PDF yükleniyor: {file.filename} ({len(file_content)} bytes) - user={user_id}")

        # 2. Create statement record
        statement_id = stmt_service.create_statement(
            user_id=user_id,
            account_id=account_id,
            month=month,
            file_name=file.filename,
            file_size_bytes=len(file_content),
        )
        logger.info(f"Statement kaydı oluşturuldu: {statement_id}")

        # 3. Mark as extracting
        stmt_service.update_statement_status(user_id, statement_id, "extracting")

        # 4. Write temp file
        os.makedirs("temp", exist_ok=True)
        safe_name = f"{uuid.uuid4()}_{file.filename}"
        temp_path = os.path.join("temp", safe_name)
        with open(temp_path, "wb") as buffer:
            buffer.write(file_content)
        logger.info(f"Temp dosya yazıldı: {temp_path}")

        # 5. Gemini extraction
        logger.info("Gemini PDF extraction başlatılıyor...")
        extracted_data = await run_in_threadpool(gemini_service.extract_transactions_from_pdf, temp_path)
        transactions = extracted_data.get("transactions", [])
        logger.info(f"Gemini {len(transactions)} işlem çıkardı.")

        # 6. Save raw extraction log
        ext_service.save_statement_extraction(
            user_id=user_id,
            statement_id=statement_id,
            provider="gemini",
            model=GEMINI_MODEL,
            raw_output={"text": str(extracted_data)[:4000]},
            parsed_output=extracted_data,
        )

        # 7. Create drafts (pending review)
        draft_result = {"created_count": 0, "failed_count": 0, "errors": []}
        if transactions:
            draft_result = draft_service.create_drafts_from_extraction(
                user_id=user_id,
                account_id=account_id,
                statement_id=statement_id,
                month=month,
                transactions=transactions,
            )

        created_count = draft_result["created_count"]
        failed_count = draft_result["failed_count"]

        if not transactions:
            raise Exception("Gemini PDF'den işlem çıkaramadı; draft oluşturulmadı.")

        if created_count == 0:
            first_error = draft_result["errors"][0]["message"] if draft_result["errors"] else "Bilinmeyen draft oluşturma hatası."
            raise Exception(f"Gemini {len(transactions)} işlem çıkardı fakat hiçbir draft kaydedilemedi: {first_error}")

        pending_count = draft_service.count_pending_drafts(user_id=user_id, statement_id=statement_id)
        if pending_count <= 0:
            raise Exception("Draft kayıtları oluşturuldu gibi görünüyor ancak pending draft bulunamadı.")

        # 8. Mark as pending_review only after real pending drafts exist.
        status_message = None
        if failed_count:
            status_message = f"{created_count} draft oluşturuldu, {failed_count} draft oluşturulamadı."
        stmt_service.update_statement_status(user_id, statement_id, "pending_review", status_message)
        logger.info(
            "PDF işlendi. extracted=%s created=%s failed=%s pending=%s",
            len(transactions), created_count, failed_count, pending_count,
        )

        return success_response(
            data={
                "statement_id": statement_id, 
                "draft_count": pending_count,
                "created_draft_count": created_count,
                "failed_draft_count": failed_count,
                "income_detected": extracted_data.get("income_detected", False)
            },
            message=f"PDF işlendi. {pending_count} işlem onayınızı bekliyor.",
        )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"PDF upload hatası: {error_msg}", exc_info=True)

        if statement_id:
            try:
                stmt_service.update_statement_status(user_id, statement_id, "failed", error_msg[:500])
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
        statements = stmt_service.list_statements_by_month(user_id=user_id, month=month)
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
        drafts = draft_service.list_pending_drafts(user_id=user_id, statement_id=statement_id)
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
        pending = draft_service.list_pending_drafts(user_id=user_id, statement_id=statement_id)
        if pending:
            return error_response(
                code="STATEMENT_HAS_PENDING",
                message=f"{len(pending)} işlem henüz onaylanmadı veya reddedilmedi.",
            )
        total_drafts = draft_service.count_statement_drafts(user_id=user_id, statement_id=statement_id)
        if total_drafts == 0:
            return error_response(
                code="STATEMENT_HAS_NO_DRAFTS",
                message="Bu PDF için işlem taslağı oluşmamış; tamamlanamaz. Backend loglarını kontrol edin.",
            )
        stmt_service.update_statement_status(user_id, statement_id, "approved")
        return success_response(data=statement_id, message="Statement tamamlandı.")
    except Exception as e:
        return error_response(code="STATEMENT_FINALIZE_ERROR", message=str(e))
