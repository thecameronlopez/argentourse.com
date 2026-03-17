from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models import User
from app.schemas import AccountCreate, AccountRead, AccountUpdate
from app.services import account_service

router = APIRouter()

@router.post("/", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return account_service.create_account(
        db=db,
        user_id=current_user.id,
        data=payload,
    )
    
    
    
@router.get("/", response_model=list[AccountRead])
def list_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return account_service.list_accounts(
        db=db,
        user_id=current_user.id
    )



@router.get("/{account_id}", response_model=AccountRead)
def get_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = account_service.get_account(
        db=db,
        user_id=current_user.id,
        account_id=account_id,
    )
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account



@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: UUID,
    payload: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = account_service.update_account(
        db=db,
        user_id=current_user.id,
        account_id=account_id,
        data=payload,
    )
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = account_service.delete_account(
        db=db,
        user_id=current_user.id,
        account_id=account_id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)