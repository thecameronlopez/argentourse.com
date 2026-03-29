from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class AccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    institution: str = Field(..., min_length=1, max_length=100)
    account_type: str = Field(..., min_length=1, max_length=100)

class AccountCreate(AccountBase):
    current_balance_cents: int = 0
    
class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    institution: str | None = Field(default=None, max_length=100)
    account_type: str | None = Field(default=None, min_length=1, max_length=100)
    current_balance_cents: int | None = None
    
class AccountRead(AccountBase):
    id: UUID
    user_id: UUID
    current_balance_cents: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
