from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import hash_password

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, email: str, password: str, full_name: str, role: str = "USER") -> User:
    hashed_pwd = hash_password(password)
    user = User(
        email=email,
        password_hash=hashed_pwd,
        full_name=full_name,
        role=role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_all_users(db: Session, search: Optional[str] = None, is_active: Optional[bool] = None) -> List[User]:
    query = db.query(User)
    if search:
        query = query.filter(
            (User.full_name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return query.all()