# ruff: noqa: B008

import json
import time

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.analytics import record_query_event
from app.services.rag import answer_question, stream_answer

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    started = time.perf_counter()
    try:
        response = answer_question(
            db=db,
            user_id=current_user.id,
            question=request.question,
            document_id=request.document_id,
            collection_id=request.collection_id,
            conversation_id=request.conversation_id,
        )
        record_query_event(
            db=db,
            user_id=current_user.id,
            status="completed",
            latency_ms=round((time.perf_counter() - started) * 1000),
            provider=settings.llm_provider,
        )
        return response
    except ValueError as exc:
        record_query_event(
            db=db,
            user_id=current_user.id,
            status="rejected",
            latency_ms=round((time.perf_counter() - started) * 1000),
            provider=settings.llm_provider,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/stream")
def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    started = time.perf_counter()

    def event_generator():
        try:
            for event in stream_answer(
                db=db,
                user_id=current_user.id,
                question=request.question,
                document_id=request.document_id,
                collection_id=request.collection_id,
                conversation_id=request.conversation_id,
            ):
                yield f"data: {json.dumps(event)}\n\n"
            record_query_event(
                db=db,
                user_id=current_user.id,
                status="completed",
                latency_ms=round((time.perf_counter() - started) * 1000),
                provider=settings.llm_provider,
            )
        except ValueError as exc:
            record_query_event(
                db=db,
                user_id=current_user.id,
                status="rejected",
                latency_ms=round((time.perf_counter() - started) * 1000),
                provider=settings.llm_provider,
            )
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
