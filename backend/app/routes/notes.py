from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database.db import get_db
from app.database.models import User
from app.schemas.note import NoteCreate, NoteResponse
from app.services.note_service import create_note, list_notes

router = APIRouter()


@router.get("/", response_model=list[NoteResponse])
def get_notes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list_notes(db, user)


@router.post("/", response_model=NoteResponse)
def create_note_route(note: NoteCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_note(db, user, note)
