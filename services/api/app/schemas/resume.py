from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


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

    class Config:
        orm_mode = True
