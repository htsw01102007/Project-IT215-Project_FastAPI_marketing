from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "MEDIUM"
    status: str = "TODO"
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    assignee_id: Optional[int] = None

class TaskResponse(TaskBase):
    id: int
    campaign_id: int
    assignee_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)