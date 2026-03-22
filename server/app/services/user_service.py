from __future__ import annotations
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models import User
from app.schemas import UserProfileUpdate
from app.core.errors import (
    UserNotFoundError,
    EmailAlreadyInUseError
)


class UserService:
    model = User
    

    @classmethod
    def get_by_id(cls, db: Session, user_id: UUID) -> User | None:        
        return db.scalar(select(cls.model).where(cls.model.id == user_id)) or None
    
    @classmethod
    def get_by_email(cls, db: Session, email: str) -> User | None:
        return db.scalar(select(cls.model).where(cls.model.email == email)) or None
    
    
    @classmethod
    def update_profile(cls, db: Session, user_id: UUID, data: UserProfileUpdate) -> User:
        user = db.get(cls.model, user_id)
        if user is None:
            raise UserNotFoundError()
        
        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(user, field, value)
        
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise EmailAlreadyInUseError()
        db.refresh(user)
        return user
    
    
    @classmethod
    def list_users(cls, db: Session) -> list[User]:
        stmt = select(cls.model).order_by(cls.model.created_at.asc())
        return list(db.scalars(stmt).all())
        
    
    
    