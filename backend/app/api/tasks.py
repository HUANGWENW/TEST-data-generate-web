from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import GenerationTask
from app.schemas.entities import TaskRead

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks(db: Session = Depends(get_db)):
    stmt = select(GenerationTask).order_by(GenerationTask.created_at.desc()).limit(100)
    return db.scalars(stmt).all()


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(GenerationTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
