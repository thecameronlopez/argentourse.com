from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TransactionCreate(BaseModel):
    account_id: UUID
    category_id: UUID | None = None
    description: str
    amount_cents: int
    transaction_date: datetime
    
class TransactionRead(BaseModel):
    id: UUID
    user_id: UUID
    account_id: UUID
    category_id: UUID | None
    description: str
    amount_cents: int
    transaction_date: datetime
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)