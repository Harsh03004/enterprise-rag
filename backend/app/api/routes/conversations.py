from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.crud.conversation import (
    create_conversation,
    delete_conversation,
    get_conversation,
    get_conversations,
    get_messages,
    update_conversation_title,
)
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationResponse,
    ConversationUpdate,
    MessageResponse,
)
from app.crud.collection import get_collection


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_conversation(
    request: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if (
        request.document_id is not None
        and request.collection_id is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A conversation cannot be scoped to both "
                "a document and a collection."
            ),
        )

    if request.collection_id is not None:
        collection = get_collection(
            db=db,
            collection_id=request.collection_id,
            user_id=current_user.id,
        )

        if collection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found.",
            )

    conversation = create_conversation(
        db=db,
        user_id=current_user.id,
        title=request.title.strip() or "New conversation",
        document_id=request.document_id,
        collection_id=request.collection_id,
    )

    return conversation


@router.get(
    "",
    response_model=list[ConversationResponse],
)
def list_user_conversations(
    document_id: int | None = None,
    collection_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if document_id is not None and collection_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A conversation list cannot be scoped to both "
                "a document and a collection."
            ),
        )

    if collection_id is not None:
        collection = get_collection(
            db=db,
            collection_id=collection_id,
            user_id=current_user.id,
        )

        if collection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found.",
            )

    return get_conversations(
        db=db,
        user_id=current_user.id,
        document_id=document_id,
        collection_id=collection_id,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
)
def get_conversation_detail(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = get_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    messages = get_messages(
        db=db,
        conversation_id=conversation.id,
    )

    return ConversationDetailResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        document_id=conversation.document_id,
        collection_id=conversation.collection_id,
        title=conversation.title,
        created_at=conversation.created_at,
        messages=[
            MessageResponse.model_validate(message)
            for message in messages
        ],
    )


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def rename_conversation(
    conversation_id: int,
    request: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    title = request.title.strip()

    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conversation title cannot be empty.",
        )

    conversation = update_conversation_title(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        title=title,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return conversation


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = delete_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return None