"""
Pydantic models for email-related API requests and responses.
"""

from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


class EmailLogResponse(BaseModel):
    """Response model for email log entry."""

    id: str
    user_id: str
    email_type: str
    recipient_email: EmailStr
    subject: str
    sent_at: Optional[datetime] = None
    status: str
    error_message: Optional[str] = None
    retries: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class EmailPreferences(BaseModel):
    """Email notification preferences for a user."""

    notify_on_new_jobs: bool = True
    notify_on_resume_upload: bool = True
    notify_on_password_change: bool = True
    weekly_digest: bool = True
    email_frequency: str = "weekly"  # daily, weekly, never

    class Config:
        json_schema_extra = {
            "example": {
                "notify_on_new_jobs": True,
                "notify_on_resume_upload": True,
                "notify_on_password_change": True,
                "weekly_digest": True,
                "email_frequency": "weekly",
            }
        }


class EmailPreferencesUpdate(BaseModel):
    """Request model for updating email preferences."""

    notify_on_new_jobs: Optional[bool] = None
    notify_on_resume_upload: Optional[bool] = None
    notify_on_password_change: Optional[bool] = None
    weekly_digest: Optional[bool] = None
    email_frequency: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "notify_on_new_jobs": False,
                "email_frequency": "daily",
            }
        }


class EmailTaskResponse(BaseModel):
    """Response for queued email task."""

    task_id: str
    status: str
    email_type: str
    recipient_email: EmailStr
    queued_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "pending",
                "email_type": "welcome",
                "recipient_email": "user@example.com",
                "queued_at": "2024-02-11T10:30:00",
            }
        }
