from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.agent import OpenClawAgent, get_dashboard, parse_text
from app.auth import get_current_user
from app.database.db import get_db
from app.database.models import User

router = APIRouter()
agent = OpenClawAgent()


class AgentRequest(BaseModel):
    text: str = Field(min_length=1)


@router.post("/parse")
def parse_input(data: AgentRequest):
    return parse_text(data.text)


@router.post("/handle")
async def handle_input(data: AgentRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return await agent.run(db, user, data.text)


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_dashboard(db, user)
