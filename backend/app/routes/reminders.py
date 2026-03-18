from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database.db import get_db
from app.database.models import User
from app.schemas.reminder import ReminderCreate, ReminderResponse
from app.services.reminder_service import create_reminder, list_reminders

router = APIRouter()


@router.get("/", response_model=list[ReminderResponse])
def get_reminders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list_reminders(db, user)


@router.post("/", response_model=ReminderResponse)
def create_reminder_route(reminder: ReminderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_reminder(db, user, reminder)
