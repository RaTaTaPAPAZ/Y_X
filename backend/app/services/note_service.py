from sqlalchemy.orm import Session

from app.database.models import Note
from app.schemas.note import NoteCreate


def list_notes(db: Session) -> list[Note]:
    return db.query(Note).order_by(Note.created_at.desc()).all()


def create_note(db: Session, data: NoteCreate | dict) -> Note:
    payload = data.model_dump() if isinstance(data, NoteCreate) else dict(data)
    note = Note(**payload)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
