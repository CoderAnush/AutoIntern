from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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

    class Config:
        orm_mode = True
