from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: int
    filename: str
    content_type: str
    status: str
    source_url: str | None
    collection_id: int | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class DocumentUpdate(BaseModel):
    filename: str


class DocumentURLCreate(BaseModel):
    url: str