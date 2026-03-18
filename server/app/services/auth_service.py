from __future__ import annotations


from uuid import UUID
import secrets
import hashlib
from datetime import datetime, timedelta, UTC

from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models import User, ResetToken
from app.schemas import UserCreate


class AuthService:
    model = User
    
    
    @staticmethod
    def _password_hasher() -> PasswordHash:
        return PasswordHash.recommended()    
    
    @classmethod
    def _hash_password(cls, password: str) -> str:
        return cls._password_hasher().hash(password)
    
    @classmethod
    def _verify_password(cls, password: str, stored_hash: str) -> bool:
        return cls._password_hasher().verify(password, stored_hash)
    
    @classmethod
    def _verify_and_maybe_rehash(cls, password: str, stored_hash: str) -> tuple[bool, str | None]:
        return cls._password_hasher().verify_and_update(password, stored_hash)
    
    
    
    
    @classmethod
    def create_user(cls, db: Session, data: UserCreate) -> User:
        payload = data.model_dump()
        user = cls.model(
            first_name=payload["first_name"],
            last_name=payload["last_name"],
            email=payload["email"],
            password_hash=cls._hash_password(payload["password"])
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    
    
    @classmethod
    def authenticate(cls, db: Session, email: str, password: str) -> User | None:
        user = db.scalar(select(cls.model).where(cls.model.email == email))
        if user is None:
            return None
        
        valid, updated_hash = cls._verify_and_maybe_rehash(password, user.password_hash)
        if not valid:
            return None
        
        if updated_hash is not None:
            user.password_hash = updated_hash
            db.commit()
            db.refresh(user)
            
        return user
    
    @classmethod
    def change_password(cls, db: Session, user_id: UUID, current_password: str, new_password: str) -> bool:
        user = db.get(cls.model, user_id)
        if user is None:
            return False
        
        valid, _ = cls._verify_and_maybe_rehash(current_password, user.password_hash)
        if not valid:
            return False
        
        user.password_hash = cls._hash_password(new_password)
        db.commit()
        return True
    
    
    
    @classmethod
    def request_password_reset(cls, db: Session, email: str) -> None:
        user = db.scalar(select(cls.model).where(cls.model.email == email))
        if user is None:
            return None
        
        db.execute(delete(ResetToken).where(ResetToken.user_id == user.id))
        
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        reset = ResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        db.add(reset)
        db.commit()
        
        return None
        
        
    @classmethod
    def reset_password(cls, db: Session, token: str, new_password: str) -> bool:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        reset = db.scalar(
            select(ResetToken).where(
                ResetToken.token_hash == token_hash,
                ResetToken.expires_at > datetime.now(UTC)
            )
        )
        if reset is None:
            return False
        
        user = db.get(cls.model, reset.user_id)
        if user is None:
            return False
        
        user.password_hash = cls._hash_password(new_password)
        db.delete(reset)        
        db.commit()
        return True
    
    
    @classmethod
    def cleanup_expired_reset_tokens(cls, db: Session) -> int:
        result = db.execute(
            delete(ResetToken).where(
                ResetToken.expires_at <= datetime.now(UTC)
            )
        )
        db.commit()
        return result.rowcount or 0