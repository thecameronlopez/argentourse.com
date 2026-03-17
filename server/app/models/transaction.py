from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, BigInteger
from datetime import datetime, UTC
from uuid import UUID, uuid4


class Transaction(Base):
    __tablename__ = "transactions"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), index=True, nullable=False)
    
    category_id: Mapped[UUID] = mapped_column(ForeignKey("categories.id"), index=True)
    
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False
    )
    
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