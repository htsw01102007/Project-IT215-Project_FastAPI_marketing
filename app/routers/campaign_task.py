from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.campaign_task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskPaginatedResponse
)
from app.services import task_service

router = APIRouter(tags=["Campaign Tasks"])

@router.post(
    "/campaigns/{campaign_id}/campaign-tasks", 
    response_model=TaskResponse, 
    status_code=status.HTTP_201_CREATED
)
def create_task(
    campaign_id: int,
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return task_service.create_task(
        db=db, campaign_id=campaign_id, current_user_id=current_user.id,
        title=task_in.title, description=task_in.description,
        priority=task_in.priority, status_val=task_in.status,
        due_date=task_in.due_date, assignee_id=task_in.assignee_id
    )

@router.get(
    "/campaigns/{campaign_id}/campaign-tasks", 
    response_model=TaskPaginatedResponse
)
def list_tasks(
    campaign_id: int,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter theo TODO, IN_PROGRESS, DONE"),
    priority_filter: Optional[str] = Query(None, alias="priority", description="Filter theo LOW, MEDIUM, HIGH"),
    assignee_id: Optional[int] = Query(None, description="Filter theo ID người được giao"),
    search: Optional[str] = Query(None, description="Search theo tiêu đề"),
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    size: int = Query(10, ge=1, le=100, description="Số lượng mục trên mỗi trang"),
    sort_by: str = Query("created_at", description="Trường sắp xếp (created_at hoặc due_date)"),
    sort_order: str = Query("desc", description="Thứ tự sắp xếp (asc hoặc desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items, total = task_service.get_campaign_tasks(
        db=db, campaign_id=campaign_id, current_user_id=current_user.id,
        status_filter=status_filter, priority_filter=priority_filter,
        assignee_id=assignee_id, search=search,
        page=page, size=size, sort_by=sort_by, sort_order=sort_order
    )
    return {"total": total, "page": page, "size": size, "items": items}

@router.get(
    "/campaign-tasks/{task_id}", 
    response_model=TaskResponse
)
def get_task_detail(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return task_service.get_task_by_id(db=db, task_id=task_id, current_user_id=current_user.id)

@router.patch(
    "/campaign-tasks/{task_id}", 
    response_model=TaskResponse
)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return task_service.update_task(
        db=db, task_id=task_id, current_user_id=current_user.id,
        task_in=task_in.model_dump(exclude_unset=True)
    )

@router.delete(
    "/campaign-tasks/{task_id}", 
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task_service.delete_task(db=db, task_id=task_id, current_user_id=current_user.id)
    return None