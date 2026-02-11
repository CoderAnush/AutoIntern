"""
Email queue service for managing async email tasks using Redis.
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Optional, List
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class EmailQueue:
    """
    Redis-based queue for async email tasks.
    Supports enqueueing, dequeueing, and status tracking of email tasks.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize email queue with Redis connection.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.queue_key = "email_queue"
        self.sent_key = "email_sent"
        self.failed_key = "email_failed"
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
        logger.info("Connected to Redis for email queue")

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")

    async def enqueue_welcome_email(self, user_id: str, user_email: str, user_name: str) -> str:
        """
        Queue a welcome email task.

        Args:
            user_id: User ID
            user_email: User's email address
            user_name: User's display name

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "type": "welcome",
            "user_id": user_id,
            "user_email": user_email,
            "user_name": user_name,
            "created_at": datetime.utcnow().isoformat(),
            "retries": 0,
            "max_retries": 3,
        }

        await self.redis_client.lpush(self.queue_key, json.dumps(task))
        logger.info(f"Enqueued welcome email task {task_id} for {user_email}")

        return task_id

    async def enqueue_resume_upload_email(
        self, user_id: str, user_email: str, resume_name: str, skills: List[str]
    ) -> str:
        """
        Queue a resume upload confirmation email task.

        Args:
            user_id: User ID
            user_email: User's email address
            resume_name: Name of resume file
            skills: List of detected skills

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "type": "resume_upload",
            "user_id": user_id,
            "user_email": user_email,
            "resume_name": resume_name,
            "skills": skills,
            "created_at": datetime.utcnow().isoformat(),
            "retries": 0,
            "max_retries": 3,
        }

        await self.redis_client.lpush(self.queue_key, json.dumps(task))
        logger.info(f"Enqueued resume upload email task {task_id} for {user_email}")

        return task_id

    async def enqueue_job_alert_email(
        self, user_id: str, user_email: str, resume_name: str, match_count: int, top_jobs: List[dict]
    ) -> str:
        """
        Queue a job match alert email task.

        Args:
            user_id: User ID
            user_email: User's email address
            resume_name: Name of resume
            match_count: Number of matches found
            top_jobs: List of top job matches

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "type": "job_alert",
            "user_id": user_id,
            "user_email": user_email,
            "resume_name": resume_name,
            "match_count": match_count,
            "top_jobs": top_jobs,
            "created_at": datetime.utcnow().isoformat(),
            "retries": 0,
            "max_retries": 3,
        }

        await self.redis_client.lpush(self.queue_key, json.dumps(task))
        logger.info(f"Enqueued job alert email task {task_id} for {user_email}")

        return task_id

    async def enqueue_password_change_email(
        self, user_id: str, user_email: str, user_name: str = "User"
    ) -> str:
        """
        Queue a password change notification email task.

        Args:
            user_id: User ID
            user_email: User's email address
            user_name: User's display name

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "type": "password_change",
            "user_id": user_id,
            "user_email": user_email,
            "user_name": user_name,
            "created_at": datetime.utcnow().isoformat(),
            "retries": 0,
            "max_retries": 3,
        }

        await self.redis_client.lpush(self.queue_key, json.dumps(task))
        logger.info(f"Enqueued password change email task {task_id} for {user_email}")

        return task_id

    async def dequeue_email(self) -> Optional[dict]:
        """
        Dequeue the next email task from the queue.

        Returns:
            Email task dict or None if queue is empty
        """
        task_json = await self.redis_client.rpop(self.queue_key)

        if not task_json:
            return None

        try:
            return json.loads(task_json)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse email task: {e}")
            return None

    async def mark_sent(self, task_id: str) -> None:
        """
        Mark an email task as successfully sent.

        Args:
            task_id: Task ID
        """
        timestamp = datetime.utcnow().isoformat()
        await self.redis_client.hset(self.sent_key, task_id, timestamp)
        logger.info(f"Marked email task {task_id} as sent")

    async def mark_failed(self, task_id: str, task: dict, error: str) -> None:
        """
        Mark an email task as failed and requeue if retries available.

        Args:
            task_id: Task ID
            task: Original task dict
            error: Error message
        """
        retries = task.get("retries", 0) + 1
        max_retries = task.get("max_retries", 3)

        logger.error(f"Email task {task_id} failed (attempt {retries}/{max_retries}): {error}")

        if retries < max_retries:
            # Requeue task with incremented retry count
            task["retries"] = retries
            await self.redis_client.lpush(self.queue_key, json.dumps(task))
            logger.info(f"Requeued email task {task_id} (retry {retries}/{max_retries})")
        else:
            # Store in failed queue
            failed_entry = {
                "id": task_id,
                "task": task,
                "error": error,
                "failed_at": datetime.utcnow().isoformat(),
            }
            await self.redis_client.hset(self.failed_key, task_id, json.dumps(failed_entry))
            logger.error(f"Email task {task_id} permanently failed after {max_retries} retries")

    async def get_task_status(self, task_id: str) -> Optional[str]:
        """
        Get status of an email task.

        Args:
            task_id: Task ID

        Returns:
            Status: 'sent', 'failed', 'pending', or None if not found
        """
        # Check if sent
        if await self.redis_client.hexists(self.sent_key, task_id):
            return "sent"

        # Check if failed
        if await self.redis_client.hexists(self.failed_key, task_id):
            return "failed"

        # Check if in queue (this is expensive, so only do if needed)
        queue_size = await self.redis_client.llen(self.queue_key)
        if queue_size > 0:
            return "pending"

        return None

    async def get_queue_size(self) -> int:
        """
        Get number of pending email tasks.

        Returns:
            Number of tasks in queue
        """
        return await self.redis_client.llen(self.queue_key)

    async def get_sent_count(self) -> int:
        """
        Get number of successfully sent emails.

        Returns:
            Number of sent tasks
        """
        return await self.redis_client.hlen(self.sent_key)

    async def get_failed_count(self) -> int:
        """
        Get number of permanently failed emails.

        Returns:
            Number of failed tasks
        """
        return await self.redis_client.hlen(self.failed_key)

    async def clear_queue(self) -> None:
        """Clear all pending email tasks (use with caution!)."""
        await self.redis_client.delete(self.queue_key)
        logger.warning("Cleared email queue")

    async def get_failed_emails(self, limit: int = 50) -> List[dict]:
        """
        Get list of failed email tasks.

        Args:
            limit: Maximum number of failed emails to return

        Returns:
            List of failed email entries
        """
        failed_dict = await self.redis_client.hgetall(self.failed_key)

        failed_list = []
        for task_id, entry_json in list(failed_dict.items())[:limit]:
            try:
                entry = json.loads(entry_json)
                failed_list.append(entry)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse failed email entry: {task_id}")

        return failed_list
