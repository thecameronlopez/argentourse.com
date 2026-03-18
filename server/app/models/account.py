from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, ForeignKey, DateTime
from datetime import datetime, UTC
from uuid import UUID, uuid4

class Account(Base):
    __tablename__ = "accounts"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    institution: Mapped[str | None] = mapped_column(String(100), nullable=False)
    account_type: Mapped[str] = mapped_column(String(100), nullable=False)
    current_balance_cents: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )
    
    user = relationship("User", back_populates="accounts")
    transactions = relationship(
        "Transaction", 
        back_populates="account", 
        cascade="all, delete-orphan"
    )
    
    