# ruff: noqa: B008

import json
import logging
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
from app.services.rag_settings import get_rag_config

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)
logger = logging.getLogger(__name__)


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
        rag_config = get_rag_config(db)
        response = answer_question(
            db=db,
            user_id=current_user.id,
            question=request.question,
            document_id=request.document_id,
            collection_id=request.collection_id,
            conversation_id=request.conversation_id,
            config=rag_config,
        )
        metrics = response.pop("_metrics", {})
        record_query_event(
            db=db,
            user_id=current_user.id,
            status="completed",
            latency_ms=round((time.perf_counter() - started) * 1000),
            provider=metrics.get("provider", settings.llm_provider),
            model=metrics.get("model"),
            retrieval_count=metrics.get("retrieval_count", 0),
            citation_count=metrics.get("citation_count", 0),
            prompt_tokens=metrics.get("prompt_tokens", 0),
            completion_tokens=metrics.get("completion_tokens", 0),
            fallback=metrics.get("fallback", False),
            estimated_cost_usd=metrics.get("estimated_cost_usd", 0.0),
            cache_hit=metrics.get("cache_hit", False),
            retrieval_latency_ms=metrics.get("retrieval_latency_ms", 0),
            generation_latency_ms=metrics.get("generation_latency_ms", 0),
            verification_latency_ms=metrics.get("verification_latency_ms", 0),
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
    except Exception as exc:
        record_query_event(
            db=db,
            user_id=current_user.id,
            status="failed",
            latency_ms=round((time.perf_counter() - started) * 1000),
            provider=settings.llm_provider,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI response could not be completed. Please try again.",
        ) from exc


@router.post("/stream")
def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    started = time.perf_counter()

    def event_generator():
        metrics = {}
        query_status = "completed"
        try:
            rag_config = get_rag_config(db)
            for event in stream_answer(
                db=db,
                user_id=current_user.id,
                question=request.question,
                document_id=request.document_id,
                collection_id=request.collection_id,
                conversation_id=request.conversation_id,
                config=rag_config,
            ):
                if event.get("type") == "metrics":
                    metrics = event.get("metrics", {})
                if event.get("type") == "error" and not metrics.get("fallback", False):
                    query_status = "failed"
                yield f"data: {json.dumps(event)}\n\n"
            record_query_event(
                db=db,
                user_id=current_user.id,
                status=query_status,
                latency_ms=round((time.perf_counter() - started) * 1000),
                provider=metrics.get("provider", settings.llm_provider),
                model=metrics.get("model"),
                retrieval_count=metrics.get("retrieval_count", 0),
                citation_count=metrics.get("citation_count", 0),
                prompt_tokens=metrics.get("prompt_tokens", 0),
                completion_tokens=metrics.get("completion_tokens", 0),
                fallback=metrics.get("fallback", False),
                estimated_cost_usd=metrics.get("estimated_cost_usd", 0.0),
                cache_hit=metrics.get("cache_hit", False),
                retrieval_latency_ms=metrics.get("retrieval_latency_ms", 0),
                generation_latency_ms=metrics.get("generation_latency_ms", 0),
                verification_latency_ms=metrics.get("verification_latency_ms", 0),
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
        except Exception:
            logger.exception(
                "Unexpected error while streaming chat response",
                extra={"user_id": current_user.id},
            )
            record_query_event(
                db=db,
                user_id=current_user.id,
                status="failed",
                latency_ms=round((time.perf_counter() - started) * 1000),
                provider=settings.llm_provider,
            )
            yield f"data: {json.dumps({'type': 'error', 'content': 'The AI response could not be completed. Please try again.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
