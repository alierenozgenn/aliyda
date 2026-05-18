from fastapi import APIRouter, Depends
from typing import Dict, Any, List, Optional
from supabase import Client

from app.core.auth import get_current_user_id
from app.api.dependencies import get_db_client
from app.schemas.domain import ChatRequest
from app.schemas.base import success_response, error_response, BaseResponse
from app.services.chat_service import ChatService
from app.services.summary_service import SummaryService
from app.services.chat_context_service import ChatContextService
from app.services.gemini_service import GeminiService

router = APIRouter()


def get_chat_service(db: Client = Depends(get_db_client)) -> ChatService:
    return ChatService(db)


def get_summary_service(db: Client = Depends(get_db_client)) -> SummaryService:
    return SummaryService(db)


def get_context_service(db: Client = Depends(get_db_client)) -> ChatContextService:
    return ChatContextService(db)


@router.post("/sessions", response_model=BaseResponse[Dict[str, Any]])
async def create_chat_session(
    month: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        session_id = chat_service.create_session(
            user_id=user_id,
            title=f"Sohbet — {month or 'Genel'}",
            month_context=month,
        )
        return success_response(data={"session_id": session_id})
    except Exception as e:
        return error_response(code="SESSION_CREATE_ERROR", message=str(e))


@router.get("/sessions", response_model=BaseResponse[List[Dict[str, Any]]])
async def list_chat_sessions(
    user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        sessions = chat_service.list_sessions(user_id=user_id)
        return success_response(data=sessions)
    except Exception as e:
        return error_response(code="SESSION_LIST_ERROR", message=str(e))


@router.get("/sessions/{session_id}/messages", response_model=BaseResponse[List[Dict[str, Any]]])
async def get_session_messages(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        messages = chat_service.get_session_messages(session_id)
        return success_response(data=messages)
    except Exception as e:
        return error_response(code="MESSAGES_FETCH_ERROR", message=str(e))


@router.post("", response_model=BaseResponse[Dict[str, Any]])
async def send_chat_message(
    data: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service),
    sum_service: SummaryService = Depends(get_summary_service),
    context_service: ChatContextService = Depends(get_context_service),
):
    try:
        gemini = GeminiService()

        # 1. Ensure session exists
        session_id = data.session_id
        if not session_id:
            session_id = chat_service.create_session(
                user_id=user_id,
                title="Sohbet",
                month_context=data.month,
            )

        # 2. Build SMART context from DB — only relevant fields for this question
        if data.month:
            sum_service.ensure_summary_fresh(user_id, data.month)
        
        context = context_service.build_context(
            user_id=user_id,
            question=data.message,
            month=data.month,
        )

        # 3. Save user message with context snapshot for debugging
        chat_service.add_message(
            session_id=session_id,
            role="user",
            content=data.message,
            context_snapshot=context,
        )

        # 4. Gemini answers based ONLY on verified DB context
        answer = gemini.answer_chat_question(
            question=data.message,
            context=context,
        )

        # 5. Save assistant response
        assistant_msg = chat_service.add_message(
            session_id=session_id,
            role="assistant",
            content=answer,
        )

        return success_response(data={
            "session_id": session_id,
            "message_id": assistant_msg["id"] if assistant_msg else None,
            "answer": answer,
        })

    except Exception as e:
        return error_response(code="CHAT_ERROR", message=str(e))
