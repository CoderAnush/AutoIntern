"""
Email notification routes for managing preferences and viewing history.
"""

import logging
from typing import List
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.models import EmailLog, User
from app.schemas.email import EmailLogResponse, EmailPreferences, EmailPreferencesUpdate
from sqlalchemy.orm import selectinload
from sqlalchemy import select, desc

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("/preferences", response_model=EmailPreferences)
async def get_email_preferences(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get user's email notification preferences.

    Returns:
        EmailPreferences with all notification settings
    """
    # Query user by ID
    statement = select(User).where(User.id == current_user["user_id"])
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return EmailPreferences(
        notify_on_new_jobs=user.notify_on_new_jobs,
        notify_on_resume_upload=user.notify_on_resume_upload,
        notify_on_password_change=user.notify_on_password_change,
        weekly_digest=user.weekly_digest,
        email_frequency=user.email_frequency,
    )


@router.put("/preferences", response_model=EmailPreferences)
async def update_email_preferences(
    preferences: EmailPreferencesUpdate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Update user's email notification preferences.

    Args:
        preferences: Updated preference settings

    Returns:
        Updated EmailPreferences
    """
    # Validate email_frequency
    valid_frequencies = ["daily", "weekly", "never"]
    if preferences.email_frequency and preferences.email_frequency not in valid_frequencies:
        raise HTTPException(
            status_code=400,
            detail=f"email_frequency must be one of: {', '.join(valid_frequencies)}"
        )

    # Query and update user
    statement = select(User).where(User.id == current_user["user_id"])
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update only provided fields
    if preferences.notify_on_new_jobs is not None:
        user.notify_on_new_jobs = preferences.notify_on_new_jobs
    if preferences.notify_on_resume_upload is not None:
        user.notify_on_resume_upload = preferences.notify_on_resume_upload
    if preferences.notify_on_password_change is not None:
        user.notify_on_password_change = preferences.notify_on_password_change
    if preferences.weekly_digest is not None:
        user.weekly_digest = preferences.weekly_digest
    if preferences.email_frequency is not None:
        user.email_frequency = preferences.email_frequency

    await session.commit()
    await session.refresh(user)

    return EmailPreferences(
        notify_on_new_jobs=user.notify_on_new_jobs,
        notify_on_resume_upload=user.notify_on_resume_upload,
        notify_on_password_change=user.notify_on_password_change,
        weekly_digest=user.weekly_digest,
        email_frequency=user.email_frequency,
    )


@router.get("/logs", response_model=List[EmailLogResponse])
async def get_email_logs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get user's email sending history.

    Args:
        limit: Maximum number of logs to return (1-100)
        offset: Number of logs to skip

    Returns:
        List of EmailLogResponse with pagination
    """
    # Query email logs for user, ordered by most recent first
    statement = (
        select(EmailLog)
        .where(EmailLog.user_id == current_user["user_id"])
        .order_by(desc(EmailLog.created_at))
        .limit(limit)
        .offset(offset)
    )

    result = await session.execute(statement)
    email_logs = result.scalars().all()

    return [
        EmailLogResponse(
            id=str(log.id),
            user_id=str(log.user_id),
            email_type=log.email_type,
            recipient_email=log.recipient_email,
            subject=log.subject,
            sent_at=log.sent_at,
            status=log.status,
            error_message=log.error_message,
            retries=log.retries,
            created_at=log.created_at,
        )
        for log in email_logs
    ]


@router.post("/test")
async def test_email(email: str = Query(..., description="Email to test")):
    """
    Send test email (for development/testing).

    Args:
        email: Email address to send test to

    Returns:
        Success message with task ID
    """
    from app.services.email_queue import EmailQueue
    from app.core.config import settings

    # Validate email format
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email format")

    try:
        # Connect to Redis and queue test email
        email_queue = EmailQueue(settings.redis_url)
        await email_queue.connect()

        task_id = await email_queue.enqueue_welcome_email(
            user_id="test-user",
            user_email=email,
            user_name="Test User",
        )

        await email_queue.disconnect()

        return {
            "status": "success",
            "message": f"Test email queued successfully",
            "task_id": task_id,
            "recipient": email,
        }

    except Exception as e:
        logger.error(f"Failed to queue test email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to queue test email - Redis connection error"
        )
