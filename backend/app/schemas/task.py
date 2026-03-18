from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    status: str = "todo"
    priority: str = "medium"
    source: str = "manual"
    widgets: list[dict[str, Any]] = Field(default_factory=list)


class TaskResponse(TaskCreate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
