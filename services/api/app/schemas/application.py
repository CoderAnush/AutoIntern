from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class ApplicationBase(BaseModel):
    company_name: str
    role_title: str
    status: str = "applied"
    notes: Optional[str] = None
    job_id: Optional[UUID] = None
    resume_id: Optional[UUID] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class ApplicationOut(ApplicationBase):
    id: UUID
    user_id: UUID
    applied_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
