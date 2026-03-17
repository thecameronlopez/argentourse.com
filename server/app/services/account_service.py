from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account
from app.schemas import AccountCreate, AccountUpdate


def create_account(db: Session, user_id: UUID, data: AccountCreate) -> Account: 
    account = Account(
        user_id=user_id,
        name=data.name,
        institution=data.institution,
        account_type=data.account_type,
        current_balance_cents=data.current_balance_cents,
    )
    db.add(account)
    db.commit()
    db.refresh()
    return account


def get_account(db: Session, user_id: UUID, account_id: UUID) -> Account:
    stmt = select(Account).where(
        Account.id == account_id,
        Account.user_id == user_id,
    )
    return db.scalar(stmt)

def list_accounts(db: Session, user_id: UUID) -> list[Account]:
    stmt = (
        select(Account)
        .where(Account.user_id == user_id)
        .order_by(Account.created_at.asc())
    )
    return list(db.scalars(stmt).all())


def update_account(
    db: Session,
    user_id: UUID,
    account_id: UUID,
    data: AccountUpdate
) -> Account | None:
    account = get_account(db=db, user_id=user_id, account_id=account_id)
    if account is None:
        return None
    
    update_data = data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(account, field, value)
        
    db.commit()
    db.refresh(account)
    
    return account


def delete_account(db: Session, user_id: UUID, account_id: UUID) -> bool:
    account = get_account(db=db, user_id=user_id, account_id=account_id)
    if account is None:
        return False
    
    db.delete(account)
    db.commit()
    return True