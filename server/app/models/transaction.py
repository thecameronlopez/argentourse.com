from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, BigInteger, Boolean, Float, UniqueConstraint
from datetime import datetime, UTC
from uuid import UUID, uuid4


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "account_id",
            "dedupe_fingerprint",
            name="uq_transaction_user_account_fingerprint"
        ),
    )
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), index=True, nullable=False)
    
    category_id: Mapped[UUID | None] = mapped_column(ForeignKey("categories.id"), index=True, nullable=True)
    
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    
    normalized_description: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    
    
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    import_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    import_batch_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    external_tx_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    
    
    dedupe_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    is_auto_categorized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_category_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )
    
    account = relationship("Account", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")