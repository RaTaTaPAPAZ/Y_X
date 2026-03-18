from pydantic import BaseModel


class Widget(BaseModel):
    type: str
    value: str