from sqlalchemy.orm import Session

from app.database.models import Note, User
from app.schemas.note import NoteCreate


def list_notes(db: Session, user: User) -> list[Note]:
    return db.query(Note).filter(Note.user_id == user.id).order_by(Note.created_at.desc()).all()


def create_note(db: Session, user: User, data: NoteCreate | dict) -> Note:
    payload = data.model_dump() if isinstance(data, NoteCreate) else dict(data)
    note = Note(user_id=user.id, **payload)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
