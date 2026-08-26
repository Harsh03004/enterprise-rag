from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    title: str = "New conversation"
    document_id: int | None = None


class ConversationUpdate(BaseModel):
    title: str


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    document_id: int | None
    title: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(BaseModel):
    id: int
    user_id: int
    document_id: int | None
    title: str
    created_at: datetime
    messages: list[MessageResponse]

    model_config = ConfigDict(from_attributes=True)