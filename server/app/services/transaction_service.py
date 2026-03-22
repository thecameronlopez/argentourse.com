from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from hashlib import sha256
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session as DBSession

from app.core.errors import (
    AccountNotFoundError,
    CategoryNotFoundError,
    DuplicateTransactionError,
    InvalidTransactionError,
    TransactionNotFoundError
)
from app.models import Account, Category, Transaction
from app.schemas import (
    TransactionCreate,
    TransactionCSVRow,
    TransactionImportPreviewRow,
    TransactionImportPreviewResult,
    TransactionImportRequest,
    TransactionImportResult,
    TransactionUpdate
)
from app.services.base_service import BaseService


class TransactionService(BaseService[Transaction, TransactionCreate, TransactionUpdate]):
    model = Transaction
    
    
    @classmethod
    def create_manual(cls, db: DBSession, user_id: UUID, data: TransactionCreate) -> Transaction:
        cls._validate_account_ownership(db, user_id, data.account_id)
        cls._validate_category_ownership(db, user_id, data.category_id)
        
        if data.amount_cents == 0:
            raise InvalidTransactionError("Transaction amount cannot be 0")
        
        normalized = cls._normalize_transaction_create(data)
        fingerprint = cls._build_dedupe_fingerprint(
            user_id=user_id,
            account_id=normalized.account_id,
            transaction_date=normalized.transaction_date,
            amount_cents=normalized.amount_cents,
            description=normalized.description
        )
        
        if cls._find_existing_by_fingerprint(db, user_id, fingerprint) is not None:
            raise DuplicateTransactionError()
        
        tx = cls.model(
            user_id=user_id,
            account_id=normalized.account_id,
            category_id=normalized.category_id,
            description=normalized.description,
            normalized_description=cls._normalize_description(normalized.description),
            amount_cents=normalized.amount_cents,
            transaction_date=normalized.transaction_date,
            import_source=None,
            import_batch_id=None,
            external_tx_id=None,
            dedupe_fingerprint=fingerprint,
            is_auto_categorized=False,
            auto_category_confidence=None,
        )
        
        try:
            db.add(tx)
            db.commit()
        except Exception:
            db.rollback()
            raise
        
        db.refresh(tx)
        return tx
    
    
    @classmethod
    def preview_import(
        cls,
        db: DBSession,
        user_id: UUID,
        data: TransactionImportRequest,
    ) -> TransactionImportPreviewResult:
        started_at = datetime.now(UTC)
        batch_id = uuid4()
        
        cls._validate_account_ownership(db, user_id, data.account_id)
        
        seen_fingerprints: set[str] = set()
        preview_rows: list[TransactionImportPreviewRow] = []
        importable = 0
        skipped_duplicates = 0
        errors: list[str] = []
        
        for index, row in enumerate(data.rows):
            warnings: list[str] = []
            try:
                normalized = cls._normalize_csv_row(
                    row=row,
                    account_id=data.account_id,
                    import_source=data.import_source,
                    batch_id=batch_id
                )
                
                fingerprint = cls._build_dedupe_fingerprint(
                    user_id=user_id,
                    account_id=normalized.account_id,
                    transaction_date=normalized.transaction_date,
                    amount_cents=normalized.amount_cents,
                    description=normalized.description
                )
                
                duplicate = False
                
                if fingerprint in seen_fingerprints:
                    warnings.append("Duplicate row in import payload")
                    duplicate = True
                
                elif cls._find_existing_by_fingerprint(db, user_id, fingerprint) is not None:
                    warnings.append("Duplicate transaction already exists")
                    duplicate = True
                
                category_id, confidence = cls._auto_categorize(db, user_id, normalized)
                normalized.category_id = category_id
                
                if category_id is not None and confidence is not None:
                    warnings.append(f"Auto-categorized with confidence {confidence:.2f}")
                    
                if duplicate:
                    skipped_duplicates += 1
                else:
                    importable += 1
                    seen_fingerprints.add(fingerprint)
                    
                preview_rows.append(
                    TransactionImportPreviewRow(
                        row_index=index,
                        normalized=normalized,
                        warnings=warnings,
                        duplicate=duplicate,
                    )
                )
            except InvalidTransactionError as exc:
                errors.append(str(exc))
                preview_rows.append(
                    TransactionImportPreviewRow(
                        row_index=index,
                        normalized=None,
                        warnings=[str(exc)],
                        duplicate=False,
                    )
                )
                
        finished_at = datetime.now(UTC)
        
        return TransactionImportPreviewResult(
            importable=importable,
            skipped_duplicates=skipped_duplicates,
            errors=errors,
            rows=preview_rows,
            batch_id=batch_id,
            started_at=started_at,
            finished_at=finished_at
        )
    
    @classmethod
    def import_rows(
        cls,
        db: DBSession,
        user_id: UUID,
        data: TransactionImportRequest,
    ) -> TransactionImportResult:
        started_at = datetime.now(UTC)
        batch_id = uuid4()
        
        cls._validate_account_ownership(db, user_id, data.account_id)
        
        seen_fingerprints: set[str] = set()
        rejected_rows: list[TransactionImportPreviewRow] = []
        errors: list[str] = []
        to_create: list[Transaction] = []
        skipped_duplicates = 0
        
        for index, row in enumerate(data.rows):
            warnings: list[str] = []
            try:
                normalized = cls._normalize_csv_row(
                    row=row,
                    account_id=data.account_id,
                    import_source=data.import_source,
                    batch_id=batch_id,
                )
                
                fingerprint = cls._build_dedupe_fingerprint(
                    user_id=user_id,
                    account_id=normalized.account_id,
                    transaction_date=normalized.transaction_date,
                    amount_cents=normalized.amount_cents,
                    description=normalized.description,
                )
                
                duplicate = False
                
                if fingerprint in seen_fingerprints:
                    warnings.append("Duplicate row in import payload")
                    duplicate = True
                elif cls._find_existing_by_fingerprint(db, user_id, fingerprint) is not None:
                    warnings.append("Duplicate transaction already exists")
                    duplicate = True
                
                category_id, confidence = cls._auto_categorize(db, user_id, normalized)
                
                if duplicate:
                    skipped_duplicates += 1
                    rejected_rows.append(
                        TransactionImportPreviewRow(
                            row_index=index,
                            normalized=normalized,
                            warnings=warnings,
                            duplicate=True,
                        )
                    )
                    continue
                
                seen_fingerprints.add(fingerprint)
                
                tx = cls.model(
                    user_id=user_id,
                    account_id=normalized.account_id,
                    category_id=category_id,
                    description=normalized.description,
                    normalized_description=cls._normalize_description(normalized.description),
                    amount_cents=normalized.amount_cents,
                    transaction_date=normalized.transaction_date,
                    import_source=normalized.import_source,
                    import_batch_id=normalized.import_batch_id,
                    external_tx_id=normalized.external_tx_id,
                    dedupe_fingerprint=fingerprint,
                    is_auto_categorized=category_id is not None,
                    auto_category_confidence=confidence,
                )
                to_create.append(tx)
            except InvalidTransactionError as exc:
                errors.append(str(exc))
                rejected_rows.append(
                    TransactionImportPreviewRow(
                        row_index=index,
                        normalized=None,
                        warnings=[str(exc)],
                        duplicate=False,
                    )
                )
        
        if to_create:
            try:
                db.add_all(to_create)
                db.commit()
            except Exception:
                db.rollback()
                raise
        
        finished_at = datetime.now(UTC)
        
        return TransactionImportResult(
            created=len(to_create),
            skipped_duplicates=skipped_duplicates,
            errors=errors,
            rejected_rows=rejected_rows,
            batch_id=batch_id,
            started_at=started_at,
            finished_at=finished_at,
        )
        
    
    
    @classmethod
    def reclassify(
        cls,
        db: DBSession,
        user_id: UUID,
        transaction_id: UUID,
        category_id: UUID | None,
    ) -> Transaction:
        tx = cls._get_owned_transaction(db, user_id, transaction_id)
        cls._validate_category_ownership(db, user_id, category_id)
        
        tx.category_id = category_id
        tx.is_auto_categorized = False
        tx.auto_category_confidence = None
        
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(tx)
        return tx
    
    
    @classmethod
    def bulk_reclassify(
        cls,
        db: DBSession,
        user_id: UUID,
        transaction_ids: list[UUID],
        category_id: UUID | None,
    ) -> int:
        cls._validate_category_ownership(db, user_id, category_id)
        
        updated = 0
        for tx_id in transaction_ids:
            tx = db.scalar(
                select(cls.model).where(
                    cls.model.id == tx_id,
                    cls.model.user_id == user_id
                )
            )
            if tx is None:
                continue
            
            tx.category_id = category_id
            tx.is_auto_categorized = False
            tx.auto_category_confidence = None
            updated += 1
            
        
        if updated:
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
        
        return updated
        
        
        
    @classmethod
    def _validate_account_ownership(cls, db: DBSession, user_id: UUID, account_id: UUID) -> Account:
        account = db.scalar(
            select(Account).where(
                Account.id == account_id,
                Account.user_id == user_id
            )
        )
        if account is None:
            raise AccountNotFoundError()
        return account
    
    
    
    @classmethod
    def _validate_category_ownership(
        cls,
        db: DBSession,
        user_id: UUID,
        category_id: UUID | None,
    ) -> Category | None:
        if category_id is None:
            return None
        
        category = db.scalar(
            select(Category).where(
                Category.id == category_id,
                Category.user_id == user_id,
            )
        )
        if category is None:
            raise CategoryNotFoundError()
        return category
    
    @classmethod
    def _get_owned_transaction(cls, db: DBSession, user_id: UUID, transaction_id: UUID) -> Transaction:
        tx =  db.scalar(
            select(cls.model).where(
                cls.model.id == transaction_id,
                cls.model.user_id == user_id,
            )
        )
        if tx is None:
            raise TransactionNotFoundError()
        return tx
    
    @classmethod
    def _normalize_csv_row(
        cls,
        row: TransactionCSVRow,
        account_id: UUID,
        import_source: str | None,
        batch_id: UUID,
    ) -> TransactionCreate:
        description = (row.description or "").strip()
        if not description:
            raise InvalidTransactionError("Transaction description cannot be empty")
        
        amount_cents = cls._parse_amount_to_cents(row.amount)
        if amount_cents == 0:
            raise InvalidTransactionError("Transaction amount cannot be 0")
        
        transaction_date = cls._parse_posted_at(row.posted_at)
        
        return TransactionCreate(
            account_id=account_id,
            category_id=None,
            description=description,
            amount_cents=amount_cents,
            transaction_date=transaction_date,
            import_source=import_source,
            import_batch_id=batch_id,
            external_tx_id=row.external_tx_id
        )
        
        
    @classmethod
    def _normalize_transaction_create(cls, data: TransactionCreate) -> TransactionCreate:
        description = (data.description or "").strip()
        if not description:
            raise InvalidTransactionError("Transaction description cannot be empty")
        if data.amount_cents == 0:
            raise InvalidTransactionError("Transaction amount cannot be 0")
        
        return TransactionCreate(
            account_id=data.account_id,
            category_id=data.category_id,
            description=description,
            amount_cents=data.amount_cents,
            transaction_date=data.transaction_date,
            import_source=data.import_source,
            import_batch_id=data.import_batch_id,
            external_tx_id=data.external_tx_id
        )
        
        
    @staticmethod
    def _normalize_description(description: str) -> str:
        return " ".join(description.strip().lower().split())
    
    @classmethod
    def _build_dedupe_fingerprint(
        cls,
        user_id: UUID,
        account_id: UUID,
        transaction_date: datetime,
        amount_cents: int,
        description: str,
    ) -> str:
        normalized_date = transaction_date.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        normalized_description = cls._normalize_description(description)
        
        source = "|".join(
            [
                str(user_id),
                str(account_id),
                normalized_date.isoformat(),
                str(amount_cents),
                normalized_description
            ]
        )
        return sha256(source.encode("utf-8")).hexdigest()
    
    
    @classmethod
    def _find_existing_by_fingerprint(
        cls,
        db: DBSession, 
        user_id: UUID,
        fingerprint: str,
    ) -> Transaction | None:
        return db.scalar(
            select(cls.model).where(
                cls.model.user_id == user_id,
                cls.model.dedupe_fingerprint == fingerprint
            )
        )
        
        
    @classmethod
    def _auto_categorize(
        cls,
        db: DBSession,
        user_id: UUID,
        tx: TransactionCreate
    ) -> tuple[UUID | None, float | None]:
        normalized_description = cls._normalize_description(tx.description)
        
        prior = db.scalar(
            select(cls.model).where(
                cls.model.user_id == user_id,
                cls.model.normalized_description == normalized_description,
                cls.model.category_id.is_not(None),
                cls.model.is_auto_categorized.is_(False)
            )
        )
        if prior is None:
            return None, None
        
        return prior.category_id, 0.95
    
    @staticmethod
    def _parse_amount_to_cents(amount: str) -> int:
        raw = amount.strip().replace("$", "").replace(",", "")

        paren_negative = raw.startswith("(") and raw.endswith(")")
        if paren_negative:
            raw = raw[1:-1].strip()

        try:
            value = Decimal(raw)
        except InvalidOperation as exc:
            raise InvalidTransactionError("Invalid transaction amount") from exc

        if paren_negative:
            value = -abs(value)

        cents = int((value * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return cents
    
    @staticmethod
    def _parse_posted_at(posted_at: str) -> datetime:
        raw = posted_at.strip()
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
            try:
                parsed = datetime.strptime(raw, fmt)
                return parsed.replace(tzinfo=UTC)
            except ValueError:
                continue
        raise InvalidTransactionError("Invalid transaction date")
