from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    MemberAddRequest,
    MemberResponse
)
from app.services import campaign_service

router = APIRouter(prefix="/campaigns", tags=["Campaigns & Members"])

# --- Endpoints Chiến dịch ---
@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    campaign_in: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return campaign_service.create_campaign(
        db=db,
        current_user_id=current_user.id,
        name=campaign_in.name,
        description=campaign_in.description
    )

@router.get("", response_model=List[CampaignResponse])
def get_my_campaigns(
    search: Optional[str] = Query(None, description="Search campaign by name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return campaign_service.get_user_campaigns(db=db, current_user_id=current_user.id, search=search)

@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign_detail(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return campaign_service.get_campaign_by_id(db=db, campaign_id=campaign_id, current_user_id=current_user.id)

@router.patch("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: int,
    campaign_in: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return campaign_service.update_campaign(
        db=db,
        campaign_id=campaign_id,
        current_user_id=current_user.id,
        name=campaign_in.name,
        description=campaign_in.description
    )

@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    campaign_service.delete_campaign(db=db, campaign_id=campaign_id, current_user_id=current_user.id)
    return None

# --- Endpoints Thành viên Chiến dịch ---
@router.post("/{campaign_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def add_member(
    campaign_id: int,
    member_in: MemberAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return campaign_service.add_campaign_member(
        db=db,
        campaign_id=campaign_id,
        current_user_id=current_user.id,
        target_user_id=member_in.user_id,
        role=member_in.role
    )

@router.get("/{campaign_id}/members", response_model=List[MemberResponse])
def get_members(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return campaign_service.get_campaign_members(db=db, campaign_id=campaign_id, current_user_id=current_user.id)

@router.delete("/{campaign_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    campaign_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    campaign_service.remove_campaign_member(
        db=db,
        campaign_id=campaign_id,
        current_user_id=current_user.id,
        target_user_id=user_id
    )
    return None