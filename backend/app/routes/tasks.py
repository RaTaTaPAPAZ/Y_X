from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database.db import get_db
from app.database.models import User
from app.schemas.task import TaskCreate, TaskResponse
from app.services.task_service import create_task, list_tasks

router = APIRouter()


@router.get("/", response_model=list[TaskResponse])
def get_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list_tasks(db, user)


@router.post("/", response_model=TaskResponse)
def create_task_route(task: TaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_task(db, user, task)
