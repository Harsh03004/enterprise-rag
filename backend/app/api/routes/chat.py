import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
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
    return answer_question(
        db=db,
        user_id=current_user.id,
        question=request.question,
        document_id=request.document_id,
        collection_id=request.collection_id,
        conversation_id=request.conversation_id,
    )


@router.post("/stream")
def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    def event_generator():
        for event in stream_answer(
            db=db,
            user_id=current_user.id,
            question=request.question,
            document_id=request.document_id,
            collection_id=request.collection_id,
            conversation_id=request.conversation_id,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )