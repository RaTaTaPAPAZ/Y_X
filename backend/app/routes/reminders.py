from fastapi import APIRouter
from app.models import Reminder
from app.database import reminders

router = APIRouter()

@router.get("/")
def get_reminders():
    return reminders


@router.post("/")
def create_reminder(reminder: Reminder):
    reminders.append(reminder)
    return reminder