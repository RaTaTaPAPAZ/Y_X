from datetime import datetime

from pydantic import BaseModel, Field


class ReminderCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    remind_at: datetime
    status: str = "scheduled"
    source: str = "manual"


class ReminderResponse(ReminderCreate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
