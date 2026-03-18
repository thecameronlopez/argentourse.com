from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models import Base


ModelT = TypeVar("ModelT", bound=Base)
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)


class BaseService(Generic[ModelT, CreateSchemaT, UpdateSchemaT]):
    
    model: type[ModelT]
    
    @classmethod
    def _to_dict(cls, data: BaseModel, *, exclude_unset: bool = False) -> dict:
        return data.model_dump(exclude_unset=exclude_unset)
    
    
    @classmethod
    def create(cls, db: Session, user_id: UUID, data: CreateSchemaT) -> ModelT:
        payload = cls._to_dict(data)
        obj = cls.model(user_id=user_id, **payload)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    
    
    @classmethod
    def get(cls, db: Session, user_id: UUID, item_id: UUID) -> ModelT | None:
        stmt = select(cls.model).where(
            cls.model.id == item_id,
            cls.model.user_id == user_id,
        )
        
        return db.scalar(stmt)
    
    
    @classmethod
    def list(cls, db: Session, user_id: UUID) -> list[ModelT]:
        stmt = (
            select(cls.model)
            .where(cls.model.user_id == user_id)
            .order_by(cls.model.created_at.asc())
        )
        return list(db.scalars(stmt).all())
    
    
    @classmethod
    def update(
        cls,
        db: Session,
        user_id: UUID,
        item_id: UUID,
        data: UpdateSchemaT,
    ) -> ModelT | None:
        obj = cls.get(db=db, user_id=user_id, item_id=item_id)
        
        if obj is None:
            return None
        
        updates = cls._to_dict(data, exclude_unset=True)
        for field, value in updates.items():
            setattr(obj, field, value)
            
        db.commit()
        db.refresh(obj)
        return obj
    
    
    @classmethod
    def delete(cls, db: Session, user_id: UUID, item_id: UUID) -> bool:
        obj = cls.get(db=db, user_id=user_id, item_id=item_id)
        if obj is None:
            return False
        db.delete(obj)
        db.commit()
        return True