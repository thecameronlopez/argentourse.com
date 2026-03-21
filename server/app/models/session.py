from .base import Base
from uuid import UUID, uuid4
from datetime import datetime, timedelta, UTC

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey


class Session(Base):
    __tablename__ = "sessions"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    session_token_hash: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    csrf_token_hash: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: (datetime.now(UTC) + timedelta(minutes=60)), nullable=False)
    
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    ip_address: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    user = relationship("User", back_populates="sessions")