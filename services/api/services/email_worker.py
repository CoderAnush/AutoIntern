"""
Background worker for processing and sending queued emails.

Run this in a separate process/container:
    python -m services.email_worker

The worker:
1. Connects to Redis queue
2. Dequeues email tasks in FIFO order
3. Renders and sends emails via SMTP
4. Logs success/failure to database
5. Retries failed emails up to 3 times
6. Handles graceful shutdown
"""

import asyncio
import logging
import sys
import signal
from datetime import datetime
from uuid import UUID

from app.services.email_service import EmailService
from app.services.email_queue import EmailQueue
from app.models.models import EmailLog
from app.db.session import AsyncSessionLocal, engine
from app.models.base import Base
from app.core.config import settings

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class EmailWorker:
    """Background worker for processing email queue."""

    def __init__(self):
        """Initialize email worker with email service and queue."""
        self.email_service = EmailService(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            sender_email=settings.sender_email,
            sender_password=settings.sender_password,
        )
        self.email_queue = EmailQueue(settings.redis_url)
        self.is_running = True
        self.processed_count = 0
        self.sent_count = 0
        self.failed_count = 0

    async def connect(self) -> None:
        """Connect to Redis and database."""
        try:
            await self.email_queue.connect()
            logger.info("Connected to Redis email queue")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis and database."""
        await self.email_queue.disconnect()
        logger.info("Disconnected from Redis")

    async def process_emails(self) -> None:
        """
        Main worker loop: continuously dequeue and process emails.

        Handles:
        - Email task dequeuing
        - Routing to appropriate email handler
        - Success/failure logging
        - Automatic retries with exponential backoff
        - Graceful shutdown on SIGTERM
        """
        logger.info("Starting email worker...")

        while self.is_running:
            try:
                # Dequeue next email task
                task = await self.email_queue.dequeue_email()

                if not task:
                    # No tasks in queue, wait before retrying
                    await asyncio.sleep(5)
                    continue

                task_id = task.get("id")
                email_type = task.get("type")
                user_id = task.get("user_id")
                retries = task.get("retries", 0)

                self.processed_count += 1
                logger.info(f"[{self.processed_count}] Processing {email_type} email task {task_id} (retry {retries})")

                # Route to appropriate handler based on email type
                success = False
                error_msg = None

                try:
                    if email_type == "welcome":
                        success = await self._handle_welcome(task)
                    elif email_type == "resume_upload":
                        success = await self._handle_resume_upload(task)
                    elif email_type == "job_alert":
                        success = await self._handle_job_alert(task)
                    elif email_type == "password_change":
                        success = await self._handle_password_change(task)
                    else:
                        logger.warning(f"Unknown email type: {email_type}")
                        error_msg = f"Unknown email type: {email_type}"

                except Exception as e:
                    logger.error(f"Error processing {email_type} email: {e}")
                    error_msg = str(e)

                # Log result to database
                if success:
                    await self.email_queue.mark_sent(task_id)
                    await self._log_email(task, "sent", None)
                    self.sent_count += 1
                    logger.info(f"✓ Email sent: {task_id}")
                else:
                    await self.email_queue.mark_failed(task_id, task, error_msg or "Unknown error")
                    await self._log_email(task, "failed", error_msg)
                    self.failed_count += 1
                    logger.warning(f"✗ Email failed: {task_id} - {error_msg}")

            except asyncio.CancelledError:
                logger.info("Email worker cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error in email worker: {e}")
                await asyncio.sleep(5)  # Wait before retrying

        logger.info(f"Email worker stopped. Stats: {self.processed_count} processed, {self.sent_count} sent, {self.failed_count} failed")

    async def _handle_welcome(self, task: dict) -> bool:
        """Send welcome email to new user."""
        return await self.email_service.send_welcome_email(
            user_email=task.get("user_email"),
            user_name=task.get("user_name"),
        )

    async def _handle_resume_upload(self, task: dict) -> bool:
        """Send resume upload confirmation email."""
        return await self.email_service.send_resume_upload_confirmation(
            user_email=task.get("user_email"),
            resume_name=task.get("resume_name"),
            skills=task.get("skills", []),
        )

    async def _handle_job_alert(self, task: dict) -> bool:
        """Send job match alert email."""
        return await self.email_service.send_job_alert_email(
            user_email=task.get("user_email"),
            resume_name=task.get("resume_name"),
            match_count=task.get("match_count", 0),
            top_jobs=task.get("top_jobs", []),
        )

    async def _handle_password_change(self, task: dict) -> bool:
        """Send password change notification email."""
        return await self.email_service.send_password_change_notification(
            user_email=task.get("user_email"),
            user_name=task.get("user_name", "User"),
        )

    async def _log_email(self, task: dict, status: str, error_msg: str = None) -> None:
        """
        Log email result to database.

        Args:
            task: Original email task
            status: 'sent' or 'failed'
            error_msg: Error message if failed
        """
        try:
            async with AsyncSessionLocal() as session:
                email_log = EmailLog(
                    id=task.get("id"),
                    user_id=UUID(task.get("user_id")),
                    email_type=task.get("type"),
                    recipient_email=task.get("user_email"),
                    subject=f"{task.get('type').replace('_', ' ').title()} Email",
                    sent_at=datetime.utcnow() if status == "sent" else None,
                    status=status,
                    error_message=error_msg,
                    retries=task.get("retries", 0),
                )
                session.add(email_log)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to log email to database: {e}")

    def stop(self) -> None:
        """Stop the worker gracefully."""
        logger.info("Stopping email worker...")
        self.is_running = False


async def main() -> None:
    """Main entry point for email worker."""
    worker = EmailWorker()

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        worker.stop()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Initialize database (ensure tables exist)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await worker.connect()
        await worker.process_emails()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error in email worker: {e}")
        sys.exit(1)
    finally:
        try:
            await worker.disconnect()
        except Exception as e:
            logger.error(f"Error during worker shutdown: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Email worker terminated")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Email worker failed: {e}")
        sys.exit(1)
