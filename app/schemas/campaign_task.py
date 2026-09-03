from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: str = "MEDIUM"  # LOW / MEDIUM / HIGH
    status: str = "TODO"      # TODO / IN_PROGRESS / DONE
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    assignee_id: Optional[int] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None

class TaskResponse(TaskBase):
    id: int
    campaign_id: int
    assignee_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TaskPaginatedResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[TaskResponse]