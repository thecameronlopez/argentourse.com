from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User

DEMO_USER_ID = UUID("11111111-1111-1111-1111-111111111111")

def get_current_user(db: Session = Depends(get_db)) -> User:
    user = db.get(User, DEMO_USER_ID)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Demo user not found",
        )
    return User