from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models import Transaction, Category
from app.schemas import TransactionCreate, TransactionUpdate, TransactionRead
from app.services.base_service import BaseService


class TransactionService(BaseService[Transaction, TransactionCreate, TransactionUpdate]):
    
    model = Transaction
    
    
    @classmethod
    def create_manual(cls, db: Session, user_id: UUID, data: TransactionCreate) -> Transaction:
        if data.amount_cents == 0:
            raise ValueError("Transaction amount cannot be 0")
        return super().create(db=db, user_id=user_id, data=data)
    
    
    @classmethod
    def reclassify(
        cls,
        db: Session,
        user_id: UUID,
        transaction_id: UUID,
        category_id: UUID | None,
    ) -> Transaction | None:
        tx = cls.get(db=db, user_id=user_id, item_id=transaction_id)
        if tx is None:
            return None
        tx.category_id = category_id
        db.commit()
        db.refresh(tx)
        return tx
    
    @classmethod
    def bulk_reclassify(
        cls,
        db: Session,
        user_id: UUID,
        transaction_ids: list[UUID],
        category_id: UUID | None
    ) -> int:
        updated = 0
        for tx_id in transaction_ids:
            tx = cls.get(db=db, user_id=user_id, item_id=tx_id)
            if tx is None:
                continue
            tx.category_id = category_id
            updated += 1
        if updated:
            db.commit()
        return updated
    
    
    @classmethod
    def import_rows(
        cls,
        db: Session,
        user_id: UUID,
        rows: Iterable[TransactionCreate],
        *,
        dry_run: bool = False,
    ) -> dict[str, int | list[dict]]:
        to_create: list[Transaction] = []
        seen = set()
        skipped_duplicates = 0
        
        for row in rows:
            tx = cls._normalize_row(row)
            
            if cls._is_duplicate_in_payload(seen, tx):
                skipped_duplicates += 1
                continue
            
            seen.add(cls._fingerprint(tx, user_id=user_id))
            obj = cls.model(
                user_id=user_id,
                **tx.model_dump(),
            )
            to_create.append(obj)
            
        if not dry_run:
            db.add_all(to_create)
            db.commit()
            
        return {
            "imported": len(to_create),
            "skipped_duplicates": skipped_duplicates,
            "errors": 0,
        }
        
    
    @staticmethod
    def _normalize_row(data: TransactionCreate) -> TransactionCreate:
        clean = data.model_dump()
        clean["description"] = (clean["description"] or "").strip()
        return TransactionCreate(**clean)
    
    
    @staticmethod
    def _fingerprint(tx: TransactionCreate, user_id: UUID) -> tuple:
        return (
            str(user_id),
            str(tx.account_id),
            tx.transaction_date.replace(tzinfo=None, microsecond=0),
            tx.amount_cents,
            (tx.description or "").strip().lower(),
        )
        
    
    @classmethod
    def _is_duplicate_in_payload(cls, seen: set[tuple], tx: TransactionCreate) -> bool:
        fp = cls._fingerprint(tx, user_id=UUID(int=0))
        if fp in seen:
            return True
        seen.add(fp)
        return False
    
    
    @classmethod
    def _auto_categorize(cls, db: Session, user_id: UUID, tx: Transaction) -> UUID | None:
        # create logic when ready for auto categorizing
        return None