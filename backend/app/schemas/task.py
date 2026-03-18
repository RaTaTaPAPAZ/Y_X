from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority: str = "normal"
    widgets: list = []

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: str
    priority: str

    class Config:
        from_attributes = True