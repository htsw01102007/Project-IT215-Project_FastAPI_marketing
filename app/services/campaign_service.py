from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.campaign import Campaign, CampaignMember
from app.models.user import User

from app.schemas.campaign import MemberResponse

# --- Helper kiểm tra quyền ---
def get_campaign_member_role(db: Session, campaign_id: int, user_id: int) -> Optional[str]:
    member = db.query(CampaignMember).filter(
        CampaignMember.campaign_id == campaign_id,
        CampaignMember.user_id == user_id
    ).first()
    return member.role if member else None

def require_campaign_access(db: Session, campaign_id: int, user_id: int) -> str:
    role = get_campaign_member_role(db, campaign_id, user_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a member of this campaign"
        )
    return role

def require_campaign_owner(db: Session, campaign_id: int, user_id: int):
    role = require_campaign_access(db, campaign_id, user_id)
    if role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only campaign OWNER can perform this action"
        )

# --- Service Chiến dịch ---
def create_campaign(db: Session, current_user_id: int, name: str, description: Optional[str] = None) -> Campaign:
    campaign = Campaign(
        name=name.strip(),
        description=description,
        owner_id=current_user_id
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    # Tự động gán người tạo làm OWNER trong bảng campaign_members
    member = CampaignMember(
        campaign_id=campaign.id,
        user_id=current_user_id,
        role="OWNER"
    )
    db.add(member)
    db.commit()
    return campaign

def get_user_campaigns(db: Session, current_user_id: int, search: Optional[str] = None) -> List[Campaign]:
    query = db.query(Campaign).join(CampaignMember).filter(CampaignMember.user_id == current_user_id)
    if search:
        query = query.filter(Campaign.name.ilike(f"%{search}%"))
    return query.all()

def get_campaign_by_id(db: Session, campaign_id: int, current_user_id: int) -> Campaign:
    require_campaign_access(db, campaign_id, current_user_id)
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign

def update_campaign(db: Session, campaign_id: int, current_user_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Campaign:
    require_campaign_owner(db, campaign_id, current_user_id)
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if name is not None:
        campaign.name = name.strip()
    if description is not None:
        campaign.description = description

    db.commit()
    db.refresh(campaign)
    return campaign

def delete_campaign(db: Session, campaign_id: int, current_user_id: int):
    require_campaign_owner(db, campaign_id, current_user_id)
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    
    db.delete(campaign)
    db.commit()

# --- Service Thành viên ---
def add_campaign_member(db: Session, campaign_id: int, current_user_id: int, target_user_id: int, role: str) -> CampaignMember:
    require_campaign_owner(db, campaign_id, current_user_id)
    
    # Kiểm tra user cần thêm có tồn tại không
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

    # Kiểm tra đã là member chưa
    existing_member = db.query(CampaignMember).filter(
        CampaignMember.campaign_id == campaign_id,
        CampaignMember.user_id == target_user_id
    ).first()
    if existing_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this campaign")

    new_member = CampaignMember(
        campaign_id=campaign_id,
        user_id=target_user_id,
        role=role.upper()
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member

def get_campaign_members(db: Session, campaign_id: int, current_user_id: int) -> List[MemberResponse]:
    require_campaign_access(db, campaign_id, current_user_id)
    
    members = db.query(
        CampaignMember.campaign_id,
        CampaignMember.user_id,
        CampaignMember.role,
        CampaignMember.joined_at,
        User.full_name,
        User.email
    ).join(User, CampaignMember.user_id == User.id)\
     .filter(CampaignMember.campaign_id == campaign_id).all()
     
    return [
        MemberResponse(
            campaign_id=m.campaign_id,
            user_id=m.user_id,
            role=m.role,
            joined_at=m.joined_at,
            full_name=m.full_name,
            email=m.email
        ) for m in members
    ]

def remove_campaign_member(db: Session, campaign_id: int, current_user_id: int, target_user_id: int):
    require_campaign_owner(db, campaign_id, current_user_id)

    member_to_remove = db.query(CampaignMember).filter(
        CampaignMember.campaign_id == campaign_id,
        CampaignMember.user_id == target_user_id
    ).first()
    if not member_to_remove:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in campaign")

    # Chặn xóa OWNER cuối cùng
    if member_to_remove.role == "OWNER":
        owner_count = db.query(CampaignMember).filter(
            CampaignMember.campaign_id == campaign_id,
            CampaignMember.role == "OWNER"
        ).count()
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last OWNER of the campaign"
            )

    db.delete(member_to_remove)
    db.commit()