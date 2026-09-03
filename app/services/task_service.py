from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from app.dependencies.auth import get_current_user
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.campaign_task import CampaignTask
from app.models.campaign import CampaignMember
from app.services.campaign_service import require_campaign_access, get_campaign_member_role

VALID_STATUSES = ["TODO", "IN_PROGRESS", "DONE"]
VALID_PRIORITIES = ["LOW", "MEDIUM", "HIGH"]

# --- Helper Kiểm tra Assignee thuộc Chiến dịch ---
def validate_assignee_in_campaign(db: Session, campaign_id: int, assignee_id: Optional[int]):
    if assignee_id is not None:
        member = db.query(CampaignMember).filter(
            CampaignMember.campaign_id == campaign_id,
            CampaignMember.user_id == assignee_id
        ).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee user is not a member of this campaign"
            )

# --- Service Task CRUD & Query ---
def create_task(
    db: Session, campaign_id: int, current_user_id: int, 
    title: str, description: Optional[str], priority: str, 
    status_val: str, due_date: Optional[datetime], assignee_id: Optional[int]
) -> CampaignTask:
    # 1. Kiểm tra user thuộc chiến dịch
    require_campaign_access(db, campaign_id, current_user_id)
    
    # 2. Validate enum workflow
    if priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Invalid priority. Allowed: {VALID_PRIORITIES}")
    if status_val not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {VALID_STATUSES}")

    # 3. Validate assignee thuộc đội chiến dịch
    if assignee_id is None:
            assignee_id = current_user_id
    else:
        validate_assignee_in_campaign(db, campaign_id, assignee_id)

    if due_date is None:
        due_date = datetime.now() + timedelta(days=3)

    

    task = CampaignTask(
        campaign_id=campaign_id,
        title=title.strip(),
        description=description,
        priority=priority,
        status=status_val,
        due_date=due_date,
        assignee_id=assignee_id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def get_campaign_tasks(
    db: Session, campaign_id: int, current_user_id: int,
    status_filter: Optional[str] = None, priority_filter: Optional[str] = None,
    assignee_id: Optional[int] = None, search: Optional[str] = None,
    page: int = 1, size: int = 10, sort_by: str = "created_at", sort_order: str = "desc"
) -> Tuple[List[CampaignTask], int]:
    # Kiểm tra user thuộc chiến dịch trước khi trả danh sách (tránh lộ task chiến dịch khác)
    require_campaign_access(db, campaign_id, current_user_id)

    query = db.query(CampaignTask).filter(CampaignTask.campaign_id == campaign_id)

    # Search & Filter nhiều điều kiện
    if status_filter:
        query = query.filter(CampaignTask.status == status_filter)
    if priority_filter:
        query = query.filter(CampaignTask.priority == priority_filter)
    if assignee_id is not None:
        query = query.filter(CampaignTask.assignee_id == assignee_id)
    if search:
        query = query.filter(CampaignTask.title.ilike(f"%{search}%"))

    total = query.count()

    # Sort & Phân trang (Pagination)
    sort_column = getattr(CampaignTask, sort_by, CampaignTask.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    tasks = query.offset((page - 1) * size).limit(size).all()
    return tasks, total

def get_task_by_id(db: Session, task_id: int, current_user_id: int) -> CampaignTask:
    task = db.query(CampaignTask).filter(CampaignTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    # Kiểm tra user thuộc chiến dịch chứa task này
    require_campaign_access(db, task.campaign_id, current_user_id)
    return task

def update_task(db: Session, task_id: int, current_user_id: int, task_in: dict) -> CampaignTask:
    task = get_task_by_id(db, task_id, current_user_id)
    user_role = get_campaign_member_role(db, task.campaign_id, current_user_id)

    # 1. Permission Matrix căn bản: Chỉ OWNER chiến dịch hoặc ASSIGNEE mới được cập nhật task
    if user_role != "OWNER" and task.assignee_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only Campaign OWNER or Task Assignee can update this task"
        )

    # 2. Phân quyền chi tiết theo trường: Chỉ OWNER mới có quyền chỉnh sửa 'title' và 'description'
    if user_role != "OWNER":
        if "title" in task_in or "description" in task_in:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only Campaign OWNER can modify task title or description"
            )

    # 3. Validation dữ liệu cập nhật
    if "priority" in task_in and task_in["priority"] and task_in["priority"] not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail="Invalid priority")
    if "status" in task_in and task_in["status"] and task_in["status"] not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")
    if "assignee_id" in task_in and task_in["assignee_id"] is not None:
        validate_assignee_in_campaign(db, task.campaign_id, task_in["assignee_id"])

    # 4. PATCH update: chỉ cập nhật các trường hợp lệ được truyền lên
    for key, value in task_in.items():
        if value is not None:
            setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task

def delete_task(db: Session, task_id: int, current_user_id: int):
    task = get_task_by_id(db, task_id, current_user_id)
    user_role = get_campaign_member_role(db, task.campaign_id, current_user_id)

    # Permission Matrix: Chỉ Campaign OWNER mới được xóa task
    if user_role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only Campaign OWNER can delete tasks"
        )

    db.delete(task)
    db.commit()