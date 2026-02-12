from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from uuid import UUID

class JobCreate(BaseModel):
    source: Optional[str] = "manual"
    external_id: Optional[str]
    title: str
    description: Optional[str]
    location: Optional[str]

class JobOut(BaseModel):
    id: str
    source: Optional[str]
    external_id: Optional[str]
    title: str
    description: Optional[str]
    location: Optional[str]
    posted_at: Optional[datetime]

    @validator('id', pre=False)
    def convert_id_to_string(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        orm_mode = True
