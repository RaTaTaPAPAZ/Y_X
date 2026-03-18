from fastapi import APIRouter
from app.ai.agent import parse_text, handle_text

router = APIRouter()


@router.post("/parse")
def parse_input(data: dict):
    text = data.get("text", "")
    result = parse_text(text)
    return result

@router.post("/handle")
def handle_input(data: dict):
    text = data.get("text", "")
    return handle_text(text)