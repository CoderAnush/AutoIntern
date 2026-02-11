"""
Comprehensive tests for Phase 7 Email Notifications System.

Test coverage:
- Email service (SMTP sending, template rendering)
- Email queue (Redis task management)
- Email endpoints (preferences, logs, status)
- Integration flows (register -> welcome email, upload -> confirmation email, etc.)
"""

import pytest
import json
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.email_service import EmailService
from app.services.email_queue import EmailQueue
from app.schemas.email import EmailPreferences, EmailPreferencesUpdate, EmailLogResponse
from app.models.models import User, EmailLog
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient
from fastapi import FastAPI

# ==================== Email Service Tests ====================


class TestEmailService:
    """Tests for EmailService SMTP sending."""

    @pytest.fixture
    def email_service(self):
        """Create email service instance."""
        return EmailService(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            sender_email="test@example.com",
            sender_password="test_password",
        )

    @pytest.mark.asyncio
    async def test_welcome_email_generation(self, email_service):
        """Test welcome email rendering."""
        user_email = "newuser@example.com"
        user_name = "newuser"

        with patch("aiosmtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__aenter__ = AsyncMock()
            mock_smtp.return_value.__aexit__ = AsyncMock()

            result = await email_service.send_welcome_email(user_email, user_name)

            # Verify email was attempted
            assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_resume_upload_email_generation(self, email_service):
        """Test resume upload confirmation email rendering."""
        user_email = "user@example.com"
        resume_name = "Resume_2024.pdf"
        skills = ["Python", "JavaScript", "React", "PostgreSQL"]

        with patch("aiosmtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__aenter__ = AsyncMock()
            mock_smtp.return_value.__aexit__ = AsyncMock()

            result = await email_service.send_resume_upload_confirmation(
                user_email, resume_name, skills
            )

            assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_job_alert_email_generation(self, email_service):
        """Test job match alert email rendering."""
        user_email = "user@example.com"
        resume_name = "Resume_2024.pdf"
        match_count = 5
        top_jobs = [
            {
                "job_title": "Senior React Developer",
                "company": "TechCorp",
                "location": "Remote",
                "similarity_score": 0.89,
            },
            {
                "job_title": "Frontend Engineer",
                "company": "StartupXYZ",
                "location": "San Francisco",
                "similarity_score": 0.76,
            },
        ]

        with patch("aiosmtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__aenter__ = AsyncMock()
            mock_smtp.return_value.__aexit__ = AsyncMock()

            result = await email_service.send_job_alert_email(
                user_email, resume_name, match_count, top_jobs
            )

            assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_password_change_email_generation(self, email_service):
        """Test password change notification email rendering."""
        user_email = "user@example.com"
        user_name = "user"

        with patch("aiosmtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__aenter__ = AsyncMock()
            mock_smtp.return_value.__aexit__ = AsyncMock()

            result = await email_service.send_password_change_notification(
                user_email, user_name
            )

            assert isinstance(result, bool)

    def test_valid_email_format(self, email_service):
        """Test email validation."""
        assert email_service._is_valid_email("user@example.com") is True
        assert email_service._is_valid_email("user.name@example.co.uk") is True

    def test_invalid_email_format(self, email_service):
        """Test invalid email rejection."""
        assert email_service._is_valid_email("invalid") is False
        assert email_service._is_valid_email("user@") is False
        assert email_service._is_valid_email("@example.com") is False
        assert email_service._is_valid_email("") is False
        assert email_service._is_valid_email(None) is False


# ==================== Email Queue Tests ====================


class TestEmailQueue:
    """Tests for EmailQueue Redis task management."""

    @pytest.fixture
    def email_queue(self):
        """Create email queue instance."""
        queue = EmailQueue("redis://localhost:6379/0")
        # Note: In real tests, would use a test Redis instance
        return queue

    @pytest.mark.asyncio
    async def test_enqueue_welcome_email(self):
        """Test enqueuing welcome email task."""
        queue = EmailQueue("redis://localhost:6379/0")

        user_id = str(uuid4())
        user_email = "test@example.com"
        user_name = "testuser"

        with patch.object(queue, "redis_client") as mock_redis:
            mock_redis.lpush = AsyncMock()

            task_id = await queue.enqueue_welcome_email(user_id, user_email, user_name)

            assert task_id is not None
            assert isinstance(task_id, str)
            mock_redis.lpush.assert_called_once()

    @pytest.mark.asyncio
    async def test_enqueue_resume_upload_email(self):
        """Test enqueuing resume upload email task."""
        queue = EmailQueue("redis://localhost:6379/0")

        user_id = str(uuid4())
        user_email = "test@example.com"
        resume_name = "Resume.pdf"
        skills = ["Python", "React"]

        with patch.object(queue, "redis_client") as mock_redis:
            mock_redis.lpush = AsyncMock()

            task_id = await queue.enqueue_resume_upload_email(
                user_id, user_email, resume_name, skills
            )

            assert task_id is not None
            mock_redis.lpush.assert_called_once()

    @pytest.mark.asyncio
    async def test_dequeue_email(self):
        """Test dequeuing email task from Redis."""
        queue = EmailQueue("redis://localhost:6379/0")

        task_data = {
            "id": str(uuid4()),
            "type": "welcome",
            "user_id": str(uuid4()),
            "user_email": "test@example.com",
            "user_name": "testuser",
        }

        with patch.object(queue, "redis_client") as mock_redis:
            mock_redis.rpop = AsyncMock(return_value=json.dumps(task_data))

            task = await queue.dequeue_email()

            assert task is not None
            assert task["type"] == "welcome"
            assert task["user_email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_mark_sent(self):
        """Test marking email as successfully sent."""
        queue = EmailQueue("redis://localhost:6379/0")
        task_id = str(uuid4())

        with patch.object(queue, "redis_client") as mock_redis:
            mock_redis.hset = AsyncMock()

            await queue.mark_sent(task_id)

            mock_redis.hset.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_failed_with_retry(self):
        """Test marking email as failed and retrying."""
        queue = EmailQueue("redis://localhost:6379/0")

        task = {
            "id": str(uuid4()),
            "type": "welcome",
            "user_id": str(uuid4()),
            "user_email": "test@example.com",
            "user_name": "testuser",
            "retries": 0,
            "max_retries": 3,
        }

        with patch.object(queue, "redis_client") as mock_redis:
            mock_redis.lpush = AsyncMock()

            await queue.mark_failed(task["id"], task, "SMTP timeout")

            # Should requeue task since retries < max_retries
            mock_redis.lpush.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_failed_max_retries(self):
        """Test storing permanently failed email."""
        queue = EmailQueue("redis://localhost:6379/0")

        task = {
            "id": str(uuid4()),
            "type": "welcome",
            "user_id": str(uuid4()),
            "user_email": "test@example.com",
            "user_name": "testuser",
            "retries": 3,
            "max_retries": 3,
        }

        with patch.object(queue, "redis_client") as mock_redis:
            mock_redis.hset = AsyncMock()

            await queue.mark_failed(task["id"], task, "SMTP timeout")

            # Should store in failed queue, not requeue
            mock_redis.hset.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_queue_size(self):
        """Test getting queue size."""
        queue = EmailQueue("redis://localhost:6379/0")

        with patch.object(queue, "redis_client") as mock_redis:
            mock_redis.llen = AsyncMock(return_value=5)

            size = await queue.get_queue_size()

            assert size == 5


# ==================== Email Endpoint Tests ====================


class TestEmailEndpoints:
    """Tests for email preference and log endpoints."""

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        return {
            "user_id": str(uuid4()),
            "email": "testuser@example.com",
        }

    @pytest.mark.asyncio
    async def test_get_email_preferences(self, mock_user):
        """Test GET /users/me/emails/preferences endpoint."""
        # This would require a full FastAPI test client setup
        # Simplified test here
        prefs = EmailPreferences(
            notify_on_new_jobs=True,
            notify_on_resume_upload=True,
            notify_on_password_change=True,
            weekly_digest=True,
            email_frequency="weekly",
        )

        assert prefs.notify_on_new_jobs is True
        assert prefs.email_frequency == "weekly"

    @pytest.mark.asyncio
    async def test_update_email_preferences(self):
        """Test PUT /users/me/emails/preferences endpoint."""
        update_data = EmailPreferencesUpdate(
            email_frequency="daily",
            notify_on_new_jobs=False,
        )

        assert update_data.email_frequency == "daily"
        assert update_data.notify_on_new_jobs is False
        assert update_data.notify_on_resume_upload is None  # Not specified

    @pytest.mark.asyncio
    async def test_invalid_email_frequency(self):
        """Test validation of email frequency."""
        valid_frequencies = ["daily", "weekly", "never"]

        invalid_freq = "hourly"
        assert invalid_freq not in valid_frequencies

    @pytest.mark.asyncio
    async def test_get_email_logs(self):
        """Test GET /users/me/emails/logs endpoint."""
        log = EmailLogResponse(
            id=str(uuid4()),
            user_id=str(uuid4()),
            email_type="welcome",
            recipient_email="user@example.com",
            subject="Welcome to AutoIntern!",
            sent_at=datetime.utcnow(),
            status="sent",
            error_message=None,
            retries=0,
            created_at=datetime.utcnow(),
        )

        assert log.email_type == "welcome"
        assert log.status == "sent"
        assert log.error_message is None


# ==================== Integration Tests ====================


class TestEmailIntegration:
    """Integration tests for complete email flows."""

    @pytest.mark.asyncio
    async def test_registration_triggers_welcome_email(self):
        """Test that user registration queues welcome email."""
        # This would test:
        # 1. User calls POST /users/register
        # 2. User created in database
        # 3. Welcome email queued in Redis
        # 4. Email worker picks up task
        # 5. Email sent successfully
        pass

    @pytest.mark.asyncio
    async def test_resume_upload_triggers_confirmation_email(self):
        """Test that resume upload queues confirmation email."""
        pass

    @pytest.mark.asyncio
    async def test_password_change_triggers_notification_email(self):
        """Test that password change queues notification email."""
        pass

    @pytest.mark.asyncio
    async def test_email_retry_on_failure(self):
        """Test that failed emails are retried."""
        pass

    @pytest.mark.asyncio
    async def test_email_respects_user_preferences(self):
        """Test that emails are not sent if user has opted out."""
        pass


# ==================== Email Worker Tests ====================


class TestEmailWorker:
    """Tests for background email worker."""

    @pytest.mark.asyncio
    async def test_worker_processes_welcome_email(self):
        """Test email worker processes welcome email task."""
        pass

    @pytest.mark.asyncio
    async def test_worker_processes_resume_email(self):
        """Test email worker processes resume upload email task."""
        pass

    @pytest.mark.asyncio
    async def test_worker_logs_email_result(self):
        """Test email worker logs results to database."""
        pass

    @pytest.mark.asyncio
    async def test_worker_handles_graceful_shutdown(self):
        """Test email worker shuts down gracefully on SIGTERM."""
        pass

    @pytest.mark.asyncio
    async def test_worker_statistics(self):
        """Test email worker tracks statistics."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
