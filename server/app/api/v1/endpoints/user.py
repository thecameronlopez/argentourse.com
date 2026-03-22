from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_csrf
from app.core.db import get_db
from app.models import User
from app.schemas import UserProfileUpdate, UserPasswordChange, UserRead
from app.services.user_service import UserService
from app.services.auth_service import AuthService

router = APIRouter()

@router.get("/", response_model=UserRead)
def get_me(current_user: User = Depends(current_user)):
    return current_user


@router.patch("/", response_model=UserRead)
def update_me(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user),
    _: None = Depends(require_csrf)
):
    return UserService.update_profile(
        db=db,
        user_id=current_user.id,
        data=payload
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: UserPasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user),
    _: None = Depends(require_csrf)
):
    AuthService.change_password(
        db=db,
        user_id=current_user.id,
        current_password=payload.current_password,
        new_password=payload.new_password
    )
   
    return None