from sqlalchemy.orm import Session

from app.database.models import Reminder, User
from app.schemas.reminder import ReminderCreate


def list_reminders(db: Session, user: User) -> list[Reminder]:
    return db.query(Reminder).filter(Reminder.user_id == user.id).order_by(Reminder.remind_at.asc()).all()


def create_reminder(db: Session, user: User, data: ReminderCreate | dict) -> Reminder:
    payload = data.model_dump() if isinstance(data, ReminderCreate) else dict(data)
    reminder = Reminder(user_id=user.id, **payload)
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder
