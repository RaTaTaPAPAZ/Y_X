from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    telegram_id: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    photo_url: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
