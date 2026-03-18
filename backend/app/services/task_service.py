from sqlalchemy.orm import Session

from app.database.models import Task
from app.schemas.task import TaskCreate


def list_tasks(db: Session) -> list[Task]:
    return db.query(Task).order_by(Task.created_at.desc()).all()


def create_task(db: Session, data: TaskCreate | dict) -> Task:
    payload = data.model_dump() if isinstance(data, TaskCreate) else dict(data)
    task = Task(**payload)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
