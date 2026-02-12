from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class SkillExtracted(BaseModel):
    """Single extracted skill with metadata."""
    name: str
    source: str = "nlp"  # nlp or rule-based


class ResumeCreate(BaseModel):
    """Resume upload request model."""
    file: Optional[str]  # Will be overridden by UploadFile in route
    user_id: str  # From JWT token (for now, query param)


class ResumeOut(BaseModel):
    """Resume response model."""
    id: str
    user_id: str
    file_name: Optional[str]
    parsed_text: Optional[str]
    skills: List[str]  # List of extracted skill names
    storage_url: Optional[str]
    created_at: Optional[datetime]

    @validator('id', 'user_id', pre=False)
    def convert_ids_to_string(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        orm_mode = True
