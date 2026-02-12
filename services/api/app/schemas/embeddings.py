"""Pydantic schemas for embeddings and recommendations."""

from pydantic import BaseModel, validator
from typing import List
from datetime import datetime
from uuid import UUID


class EmbeddingOut(BaseModel):
    """Response model for embedding metadata."""
    id: str
    parent_type: str  # "job" or "resume"
    parent_id: str
    model_name: str  # "sentence-transformers/all-MiniLM-L6-v2"
    vector: List[float]  # 384-dimensional vector
    created_at: datetime

    @validator('id', 'parent_id', pre=False)
    def convert_ids_to_string(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        orm_mode = True


class RecommendationResult(BaseModel):
    """Result of job recommendation for a resume."""
    job_id: str
    job_title: str
    job_description: str
    job_location: str
    resume_id: str
    similarity_score: float  # 0.0-1.0 cosine similarity from FAISS
    matched_skills: List[str]  # Skills that appear in both resume and job
    skill_gaps: List[str]  # Required skills in job not found in resume

    @validator('job_id', 'resume_id', pre=False)
    def convert_ids_to_string(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class ResumeQualityScore(BaseModel):
    """Quality assessment breakdown for a resume."""
    resume_id: str
    text_length_score: float  # 0-100 (penalizes very short resumes)
    skill_count_score: float  # 0-100 (normalized against expected skill count)
    completeness_score: float  # 0-100 (presence of tech + soft skills)
    overall_quality_score: float  # 0-100 (average of three component scores)

    @validator('resume_id', pre=False)
    def convert_id_to_string(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
