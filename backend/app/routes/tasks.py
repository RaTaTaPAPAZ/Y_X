from fastapi import APIRouter
from app.models import Task
from app.database import tasks

router = APIRouter()

@router.get("/")
def get_tasks():
    return tasks


@router.post("/")
def create_task(task: Task):
    tasks.append(task)
    return task