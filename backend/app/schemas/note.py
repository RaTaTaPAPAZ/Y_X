from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    source: str = "manual"
    widgets: list[dict[str, Any]] = Field(default_factory=list)


class NoteResponse(NoteCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
