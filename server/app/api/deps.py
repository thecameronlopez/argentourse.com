from fastapi import Depends, HTTPException, status, Cookie, Header
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.security import Security
from app.core.db import get_db
from app.models import User, Session as SessionModel


def current_session(
    db: DBSession = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> SessionModel:
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        token_hash = Security.hash_token(session_token)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    db_session = db.query(SessionModel).filter(
        SessionModel.session_token_hash == token_hash,
        SessionModel.revoked_at.is_(None)
    ).first()
    
    if db_session is None or Security.is_expired(db_session.expires_at):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    return db_session


def current_user(
    db: DBSession = Depends(get_db), 
    db_session: SessionModel = Depends(current_session)
    ) -> User:
    
    user = db.get(User, db_session.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user


def require_csrf(
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
    db_session: SessionModel = Depends(current_session)
    ) -> None:
    if not csrf_header or not Security.verify_csrf(csrf_header, db_session.csrf_token_hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed"
        )
    
    