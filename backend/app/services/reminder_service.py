from sqlalchemy.orm import Session

from app.database.models import Reminder
from app.schemas.reminder import ReminderCreate


def list_reminders(db: Session) -> list[Reminder]:
    return db.query(Reminder).order_by(Reminder.remind_at.asc()).all()


def create_reminder(db: Session, data: ReminderCreate | dict) -> Reminder:
    payload = data.model_dump() if isinstance(data, ReminderCreate) else dict(data)
    reminder = Reminder(**payload)
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder
