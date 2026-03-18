from fastapi import APIRouter
from app.models import Note
from app.database import notes

router = APIRouter()

@router.get("/")
def get_notes():
    return notes


@router.post("/")
def create_note(note: Note):
    notes.append(note)
    return note