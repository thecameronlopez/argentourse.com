from uuid import UUID

from fastapi import Depends, HTTPException, status, Cookie
from sqlalchemy.orm import Session
import jwt

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models import User

DEMO_USER_ID = UUID("11111111-1111-1111-1111-111111111111")

def get_current_user(db: Session = Depends(get_db), access_token: str | None = Cookie(default=None)) -> User:
    
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        payload = decode_access_token(access_token)
        user_id = UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentitals"
        )
        
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user