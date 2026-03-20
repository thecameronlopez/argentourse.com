from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TransactionBase(BaseModel):
    account_id: UUID
    category_id: UUID | None = None
    description: str = Field(..., min_length=1, max_length=255)
    amount_cents: int = Field(..., description="Store dollars as (int) cents")
    transaction_date: datetime


class TransactionCreate(TransactionBase):
    import_source: str | None = None
    import_batch_id: UUID | None = None
    external_tx_id: str | None = None
    

class TransactionUpdate(BaseModel):
    account_id: UUID | None = None
    category_id: UUID | None = None
    description: str | None = None
    amount_cents: int | None = None
    transaction_date: datetime | None = None
    
    
    
class TransactionRead(TransactionBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    import_source: str | None = None
    import_batch_id: UUID | None = None
    external_tx_id: str | None = None
    is_auto_categorized: bool = False
    auto_category_confidence: float | None = None
    
    model_config = ConfigDict(from_attributes=True)
    
    
class TransactionCSVRow(BaseModel):
    account_name: str | None = None
    posted_at: str 
    description: str
    amount: str | float
    external_tx_id: str | None = None
    category_hint: str | None = None
    

class TransactionImportPreviewRow(BaseModel):
    row_index: int
    normalized: TransactionCreate | None = None
    warnings: list[str] = []
    duplicate: bool = False
    

class TransactionImportRequest(BaseModel):
    rows: list[TransactionCSVRow]
    account_id: UUID
    dry_run: bool = False
    

class TransactionImportResult(BaseModel):
    created: int
    skipped_duplicates: int
    errors: list[str] = []
    rejected_rows: list[TransactionImportPreviewRow] = []
    batch_id: UUID
    started_at: datetime
    finished_at: datetime