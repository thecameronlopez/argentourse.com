from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_csrf
from app.core.db import get_db
from app.schemas import AccountCreate, AccountRead, AccountUpdate
from app.services.base_service import BaseService
from app.models import Account, User

router = APIRouter()

class AccountService(BaseService[Account, AccountCreate, AccountUpdate]):
    model = Account
    

@router.post("/", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user),
    _: None = Depends(require_csrf)
):
    return AccountService.create(
        db=db,
        user_id=current_user.id,
        data=payload,
    )
    
    
    
@router.get("/", response_model=list[AccountRead])
def list_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user)
):
    return AccountService.list(
        db=db,
        user_id=current_user.id
    )



@router.get("/{account_id}", response_model=AccountRead)
def get_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user),
):
    return AccountService.get(
        db=db,
        user_id=current_user.id,
        item_id=account_id,
    )




@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: UUID,
    payload: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user),
    _: None = Depends(require_csrf)
):
    return AccountService.update(
        db=db,
        user_id=current_user.id,
        item_id=account_id,
        data=payload,
    )



@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user),
    _: None = Depends(require_csrf)
):
    AccountService.delete(
        db=db,
        user_id=current_user.id,
        item_id=account_id
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)