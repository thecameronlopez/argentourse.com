from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import OwnedResourceNotFoundError
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
        
        try:
            db.add(obj)
            db.commit()
        except Exception:
            db.rollback()
            raise
        
        db.refresh(obj)
        return obj
    
    
    @classmethod
    def get(cls, db: Session, user_id: UUID, item_id: UUID) -> ModelT:
        stmt = select(cls.model).where(
            cls.model.id == item_id,
            cls.model.user_id == user_id,
        )
        obj = db.scalar(stmt)
        if obj is None:
            raise OwnedResourceNotFoundError()
        
        return obj
    
    
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
    ) -> ModelT:
        obj = cls.get(db=db, user_id=user_id, item_id=item_id)
            
        updates = cls._to_dict(data, exclude_unset=True)
        for field, value in updates.items():
            setattr(obj, field, value)
            
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        
        db.refresh(obj)
        return obj
    
    
    @classmethod
    def delete(cls, db: Session, user_id: UUID, item_id: UUID) -> None:
        obj = cls.get(db=db, user_id=user_id, item_id=item_id)
        
        try:
            db.delete(obj)
            db.commit()
        except Exception:
            db.rollback()
            raise
