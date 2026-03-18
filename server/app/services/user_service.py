from __future__ import annotations

from app.core.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import User
from app.schemas import UserCreate, UserRead, UserUpdate
from .base_service import BaseService


class UserService(BaseService[User, UserCreate, UserUpdate]):
    model = User
    
    @staticmethod
    def _hash_password(password: str) -> str:
        pass
    
    @staticmethod
    def _verify_password(password: str, user_password: str) -> bool:
        if password != user_password:
            return False
        return True
    
    @classmethod
    def create_user(cls, db: Session, data: UserUpdate) -> User:
        payload = data.model_dump(exclude_unset=True)
        payload["password_hash"] = cls._hash_password(payload.pop("password"))
        user = cls.model(**payload)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
        
        
    @classmethod
    def authenticate(cls, db: Session, email: str, password: str) -> User | None:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            return None
        return user if cls._verify_password(password, user.password_hash) else None