from sqlalchemy.orm import Session

from app.database.models import Task, User
from app.schemas.task import TaskCreate


def list_tasks(db: Session, user: User) -> list[Task]:
    return db.query(Task).filter(Task.user_id == user.id).order_by(Task.created_at.desc()).all()


def create_task(db: Session, user: User, data: TaskCreate | dict) -> Task:
    payload = data.model_dump() if isinstance(data, TaskCreate) else dict(data)
    task = Task(user_id=user.id, **payload)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
