from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    document_id: int | None = None
    collection_id: int | None = None
    conversation_id: int | None = None

class ChatSource(BaseModel):
    id: int
    document_id: int
    filename: str
    chunk_index: int
    distance: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]