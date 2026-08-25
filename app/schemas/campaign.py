from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

class CampaignBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

class CampaignResponse(CampaignBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MemberAddRequest(BaseModel):
    user_id: int
    role: str = "MEMBER"  # OWNER / MEMBER

class MemberResponse(BaseModel):
    campaign_id: int
    user_id: int
    role: str
    joined_at: datetime
    full_name: Optional[str] = None
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)