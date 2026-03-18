from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.note import NoteCreate, NoteResponse
from app.services.note_service import create_note, list_notes

router = APIRouter()


@router.get("/", response_model=list[NoteResponse])
def get_notes(db: Session = Depends(get_db)):
    return list_notes(db)


@router.post("/", response_model=NoteResponse)
def create_note_route(note: NoteCreate, db: Session = Depends(get_db)):
    return create_note(db, note)
