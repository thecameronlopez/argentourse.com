from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.db import get_db

from app.schemas import (
    UserCreate, 
    UserRead, 
    UserLogin, 
    ForgotPasswordRequest, 
    ResetPasswordRequest
)
from app.services.auth_service import AuthService

router = APIRouter()

def _set_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.token_expiry * 60,
        path="/"
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.token_expiry * 60,
        path="/"
    )
    

def _clear_cookies(response: Response) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/"
    )
    response.delete_cookie(
        key=settings.csrf_cookie_name,
        path="/"
    )
    
    
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate,
    db: DBSession = Depends(get_db),
) -> UserRead:
    return AuthService.create_user(db=db, data=payload)


@router.post("/login", response_model=UserRead)
def login(
    payload: UserLogin,
    response: Response,
    request: Request,
    db: DBSession = Depends(get_db)
) -> UserRead:
    result = AuthService.login(
        db=db,
        email=payload.email,
        password=payload.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    
    _set_cookies(response, result.session_token, result.csrf_token)
    
    return result.user

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: DBSession = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name)
) -> None:
    if session_token:
        AuthService.logout(db=db, raw_session_token=session_token)
        
    _clear_cookies(response)
    
    return None

@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: DBSession = Depends(get_db)
) -> None:
    reset_token = AuthService.request_password_reset(db=db, email=payload.email)
    
    #TODO - need to implement email in fastapi before prod.
    
    _ = reset_token
    return None

@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    payload: ResetPasswordRequest,
    db: DBSession = Depends(get_db)
) -> None:
    AuthService.reset_password(
        db=db,
        token=payload.token,
        new_password=payload.new_password
    )
    return None
