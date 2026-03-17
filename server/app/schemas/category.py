from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

class CategoryCreate(BaseModel):
    name: str
    category_type: str
    
class CategoryRead(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    category_type: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)