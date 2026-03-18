from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.task import TaskCreate, TaskResponse
from app.services.task_service import create_task, list_tasks

router = APIRouter()


@router.get("/", response_model=list[TaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    return list_tasks(db)


@router.post("/", response_model=TaskResponse)
def create_task_route(task: TaskCreate, db: Session = Depends(get_db)):
    return create_task(db, task)
