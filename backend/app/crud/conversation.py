from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message


def create_conversation(
    db: Session,
    user_id: int,
    title: str = "New conversation",
    document_id: int | None = None,
) -> Conversation:
    conversation = Conversation(
        user_id=user_id,
        document_id=document_id,
        title=title,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


def get_conversation(
    db: Session,
    conversation_id: int,
    user_id: int,
) -> Conversation | None:
    statement = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id,
    )

    return db.scalar(statement)


def get_conversations(
    db: Session,
    user_id: int,
    document_id: int | None = None,
) -> list[Conversation]:
    statement = select(Conversation).where(
        Conversation.user_id == user_id,
    )

    if document_id is None:
        statement = statement.where(
            Conversation.document_id.is_(None)
        )
    else:
        statement = statement.where(
            Conversation.document_id == document_id
        )

    statement = statement.order_by(
        Conversation.created_at.desc()
    )

    return list(db.scalars(statement).all())


def update_conversation_title(
    db: Session,
    conversation_id: int,
    user_id: int,
    title: str,
) -> Conversation | None:
    conversation = get_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=user_id,
    )

    if conversation is None:
        return None

    conversation.title = title

    db.commit()
    db.refresh(conversation)

    return conversation


def delete_conversation(
    db: Session,
    conversation_id: int,
    user_id: int,
) -> bool:
    conversation = get_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=user_id,
    )

    if conversation is None:
        return False

    db.delete(conversation)
    db.commit()

    return True


def add_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


def get_messages(
    db: Session,
    conversation_id: int,
) -> list[Message]:
    statement = (
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
        )
        .order_by(Message.created_at)
    )

    return list(db.scalars(statement).all())