from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TransactionBase(BaseModel):
    account_id: UUID
    category_id: UUID | None = None
    description: str = Field(..., min_length=1, max_length=255)
    amount_cents: int = Field(..., description="Store currency as integer cents, signed")
    transaction_date: datetime


class TransactionCreate(TransactionBase):
    import_source: str | None = Field(default=None, max_length=100)
    import_batch_id: UUID | None = None
    external_tx_id: str | None = Field(default=None, max_length=255)
    

class TransactionUpdate(BaseModel):
    account_id: UUID | None = None
    category_id: UUID | None = None
    description: str | None = Field(default=None, min_length=1, max_length=255)
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
    account_name: str | None = Field(default=None, max_length=100)
    posted_at: str 
    description: str = Field(..., min_length=1, max_length=255)
    amount: str
    external_tx_id: str | None = Field(default=None, max_length=255)
    category_hint: str | None = Field(default=None, max_length=100)
    

class TransactionImportPreviewRow(BaseModel):
    row_index: int
    normalized: TransactionCreate | None = None
    warnings: list[str] = Field(default_factory=list)
    duplicate: bool = False
    

class TransactionImportRequest(BaseModel):
    rows: list[TransactionCSVRow]
    account_id: UUID
    import_source: str | None = Field(default=None, max_length=100)
    dry_run: bool = False
    

class TransactionImportPreviewResult(BaseModel):
    importable: int
    skipped_duplicates: int
    errors: list[str] = Field(default_factory=list)
    rows: list[TransactionImportPreviewRow] = Field(default_factory=list)
    batch_id: UUID
    started_at: datetime
    finished_at: datetime


class TransactionImportResult(BaseModel):
    created: int
    skipped_duplicates: int
    errors: list[str] = Field(default_factory=list)
    rejected_rows: list[TransactionImportPreviewRow] = Field(default_factory=list)
    batch_id: UUID
    started_at: datetime
    finished_at: datetime


class TransactionReclassifyRequest(BaseModel):
    category_id: UUID | None = None


class TransactionBulkReclassifyRequest(BaseModel):
    transaction_ids: list[UUID] = Field(min_length=1)
    category_id: UUID | None = None


class TransactionBulkReclassifyResult(BaseModel):
    updated: int
