from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.agent import OpenClawAgent, get_dashboard, parse_text
from app.database.db import get_db

router = APIRouter()
agent = OpenClawAgent()


class AgentRequest(BaseModel):
    text: str = Field(min_length=1)


@router.post("/parse")
def parse_input(data: AgentRequest):
    return parse_text(data.text)


@router.post("/handle")
async def handle_input(data: AgentRequest, db: Session = Depends(get_db)):
    return await agent.run(db, data.text)


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return get_dashboard(db)
