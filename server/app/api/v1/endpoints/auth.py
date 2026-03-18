from fastapi import APIRouter, Depends, HTTPException, status, Response
from app.core.config import settings
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas import (
    UserCreate, 
    UserRead, 
    UserLogin, 
    ForgotPasswordRequest, 
    ResetPasswordRequest
)
from app.services.auth_service import AuthService
from app.core.security import create_access_token

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    user = AuthService.create_user(db=db, data=payload)
    return user


@router.post("/login")
def login(
    payload: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    user = AuthService.authenticate(db=db, email=payload.email, password=payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token = create_access_token(user.id)
    
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=60 * 60,
        path="/",
    )
    
    return {"message": f"Welcome, {user.first_name}"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        path="/"
    )
    return None



@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    AuthService.request_password_reset(db=db, email=payload.email)
    return None


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    ok = AuthService.reset_password(
        db=db,
        token=payload.token,
        new_password=payload.new_password
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )
    return None