from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Note(BaseModel):
    id: int
    title: str
    description: Optional[str] = None


class Task(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str = "todo"
    priority: int = 1


class Reminder(BaseModel):
    id: int
    title: str
    remind_at: datetime