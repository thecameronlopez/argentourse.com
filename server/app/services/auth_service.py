from __future__ import annotations

from datetime import datetime, timedelta, UTC
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DBSession

from app.core.security import Security
from app.core.config import settings
from app.models import User, ResetToken, Session as SessionModel
from app.schemas import UserCreate



class AuthServiceError(Exception):
    pass

class EmailAlreadyInUseError(AuthServiceError):
    pass

class UserNotFoundError(AuthServiceError):
    pass

class InvalidCredentialsError(AuthServiceError):
    pass

class InvalidTokenError(AuthServiceError):
    pass


@dataclass(frozen=True, slots=True)
class LoginResult:
    user: User
    session_token: str
    csrf_token: str
    expires_at: datetime


class AuthService:
    user_model = User
    session_model = SessionModel
    reset_model = ResetToken
    RESET_TOKEN_MINUTES = settings.token_expiry
    
    
    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)
      
    
    
    @classmethod
    def create_user(cls, db: DBSession, data: UserCreate) -> User:
        payload = data.model_dump()
        user = cls.user_model(
            first_name=payload["first_name"],
            last_name=payload["last_name"],
            email=payload["email"],
            password_hash=Security.hash_password(payload["password"])
        )
        try:
            db.add(user)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise EmailAlreadyInUseError("Email already in use") from exc
        
        db.refresh(user)
        return user
    
    
    
    @classmethod
    def authenticate(cls, db: DBSession, email: str, password: str) -> User:
        user = db.scalar(select(cls.user_model).where(cls.user_model.email == email))
        if user is None:
            raise InvalidCredentialsError("Invalid credentials")
        
        valid, updated_hash = Security.verify_and_maybe_rehash(password, user.password_hash)
        if not valid:
            raise InvalidCredentialsError("Invalid credentials")
        
        if updated_hash is not None:
            user.password_hash = updated_hash
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
            db.refresh(user)
            
        return user
    
    @classmethod
    def login(
        cls, 
        db: DBSession,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> LoginResult:
        user = cls.authenticate(db=db, email=email, password=password)
        secrets_bundle = Security.issue_session_secrets()
        now = cls._now()
        
        session = cls.session_model(
            user_id=user.id,
            session_token_hash=secrets_bundle.session_token_hash,
            csrf_token_hash=secrets_bundle.csrf_token_hash,
            created_at=now,
            expires_at=secrets_bundle.expires_at,
            last_seen_at=now,
            ip_address=(ip_address[:128] if ip_address else None),
            user_agent=(user_agent[:100] if user_agent else None)
        )
        
        try:
            db.add(session)
            db.commit()
        except Exception:
            db.rollback()
            raise
        
        return LoginResult(
            user=user,
            session_token=secrets_bundle.session_token,
            csrf_token=secrets_bundle.csrf_token,
            expires_at=secrets_bundle.expires_at
        )
        
    @classmethod
    def get_user_from_session(
        cls,
        db: DBSession,
        raw_session_token: str,
        touch_last_seen: bool = True
    ) -> User | None:
        try:
            token_hash = Security.hash_token(raw_session_token)
        except (TypeError, ValueError):
            return None
        
        now = cls._now()
        
        db_session = db.scalar(
            select(cls.session_model).where(
                cls.session_model.session_token_hash == token_hash,
                cls.session_model.revoked_at.is_(None),
                cls.session_model.expires_at > now
            )
        )
        if db_session is None:
            return None
        
        user = db.get(cls.user_model, db_session.user_id)
        if user is None:
            return None
        
        if touch_last_seen:
            db_session.last_seen_at = now
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
        
        return user      
        
    @classmethod
    def logout(cls, db: DBSession, raw_session_token: str) -> bool:
        try:
            token_hash = Security.hash_token(raw_session_token)
        except (TypeError, ValueError):
            return False
        
        db_session = db.scalar(
            select(cls.session_model).where(
                cls.session_model.session_token_hash == token_hash,
                cls.session_model.revoked_at.is_(None)
            )
        )
        if db_session is None:
            return False
        
        db_session.revoked_at = cls._now()
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        
        return True
    
    
    @classmethod
    def revoke_all_user_sessions(cls, db: DBSession, user_id: UUID) -> int:
        result = db.execute(
            update(cls.session_model)
            .where(
                cls.session_model.user_id == user_id,
                cls.session_model.revoked_at.is_(None)
            )
            .values(revoked_at=cls._now())
        )
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        return result.rowcount or 0
        
    
    
    @classmethod
    def request_password_reset(cls, db: DBSession, email: str) -> str | None:
        user = db.scalar(select(cls.user_model).where(cls.user_model.email == email))
        if user is None:
            return None
        
        raw_token = Security.generate_token(32)
        token_hash = Security.hash_token(raw_token)
        
        db.execute(delete(cls.reset_model).where(cls.reset_model.user_id == user.id))
        
        reset = cls.reset_model(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=cls._now() + timedelta(minutes=cls.RESET_TOKEN_MINUTES),
        )
        
        db.add(reset)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        
        return raw_token
    
        
        
    @classmethod
    def reset_password(cls, db: DBSession, token: str, new_password: str) -> bool:
        try:
            token_hash = Security.hash_token(token)
        except (TypeError, ValueError):
            raise InvalidTokenError("Token is invalid or expired")
        
        reset = db.scalar(
            select(cls.reset_model).where(
                cls.reset_model.token_hash == token_hash,
                cls.reset_model.expires_at > cls._now()
            )
        )
        if reset is None:
            raise InvalidTokenError("Token is invalid or expired")
        
        user = db.get(cls.user_model, reset.user_id)
        if user is None:
            raise UserNotFoundError("User not found")
        
        user.password_hash = Security.hash_password(new_password)
        db.delete(reset)  
        db.execute(
            update(cls.session_model)
            .where(
                cls.session_model.user_id == user.id,
                cls.session_model.revoked_at.is_(None)
            )
            .values(revoked_at=cls._now())
        )      
        
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        return True
    
    
    @classmethod
    def change_password(cls, db: DBSession, user_id: UUID, current_password: str, new_password: str) -> bool:
        user = db.get(cls.user_model, user_id)
        if user is None:
            raise UserNotFoundError("User not found")
        
        valid, _ = Security.verify_and_maybe_rehash(current_password, user.password_hash)
        if not valid:
            raise InvalidCredentialsError("Invalid credentials")
        
        user.password_hash = Security.hash_password(new_password)
        db.execute(
            update(cls.session_model)
            .where(
                cls.session_model.user_id == user.id,
                cls.session_model.revoked_at.is_(None)
            )
            .values(revoked_at=cls._now())
        )  
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        return True

    
    
    @classmethod
    def cleanup_expired_reset_tokens(cls, db: DBSession) -> int:
        result = db.execute(
            delete(cls.reset_model).where(
                cls.reset_model.expires_at <= cls._now()
            )
        )
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        return result.rowcount or 0
    
    @classmethod
    def cleanup_expired_sessions(cls, db: DBSession) -> int:
        result = db.execute(
            delete(cls.session_model).where(
                cls.session_model.expires_at <= cls._now()
            )
        )
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        return result.rowcount or 0