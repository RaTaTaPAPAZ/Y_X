from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.reminder import ReminderCreate, ReminderResponse
from app.services.reminder_service import create_reminder, list_reminders

router = APIRouter()


@router.get("/", response_model=list[ReminderResponse])
def get_reminders(db: Session = Depends(get_db)):
    return list_reminders(db)


@router.post("/", response_model=ReminderResponse)
def create_reminder_route(reminder: ReminderCreate, db: Session = Depends(get_db)):
    return create_reminder(db, reminder)
