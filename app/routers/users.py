from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.dependencies.auth import get_current_user, require_admin
from app.services.user_service import get_all_users

router = APIRouter(prefix="/users", tags=["User"])

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("", response_model=List[UserResponse])
def list_users(
    search: Optional[str] = Query(None, description="Search by name or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    return get_all_users(db, search=search, is_active=is_active)