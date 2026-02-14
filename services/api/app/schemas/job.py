from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from uuid import UUID

class JobCreate(BaseModel):
    source: Optional[str] = "manual"
    external_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    company_name: Optional[str] = None
    apply_url: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None

class JobOut(BaseModel):
    id: str
    source: Optional[str] = None
    external_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    posted_at: Optional[datetime] = None
    company_name: Optional[str] = None
    apply_url: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None

    @validator('id', pre=False)
    def convert_id_to_string(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        orm_mode = True
