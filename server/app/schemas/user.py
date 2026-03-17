from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    
    
class UserRead(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)