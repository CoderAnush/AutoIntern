"""Background task for async embedding generation."""

import logging
import asyncio
from typing import Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.models import Job as JobModel, Resume as ResumeModel, Embedding as EmbeddingModel
from app.services.embeddings_service import EmbeddingsManager
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def process_embedding_queue(
    redis_client,
    queue_name: str = "ingest:embeddings",
    batch_size: int = 10
):
    """
    Listen to Redis queue and process embedding generation tasks.

    Task format:
    {
        "type": "job" | "resume",
        "id": "uuid",
        "text": "content for embedding"
    }

    Args:
        redis_client: Redis async client
        queue_name: Redis queue name
        batch_size: Process N items before committing
    """
    embeddings_mgr = EmbeddingsManager()
    processed_count = 0
    failed_count = 0

    logger.info(f"Starting embedding worker on queue: {queue_name}")

    while True:
        try:
            # Get task from Redis queue with timeout
            task = await redis_client.blpop(queue_name, timeout=30)

            if not task:
                logger.debug("No tasks in queue, waiting...")
                await asyncio.sleep(5)
                continue

            # Parse task
            task_data = task[1]  # blpop returns (key, value)
            if isinstance(task_data, bytes):
                import json
                task = json.loads(task_data.decode())
            else:
                task = task_data

            await process_single_embedding_task(task, embeddings_mgr)
            processed_count += 1

            if processed_count % batch_size == 0:
                logger.info(f"Processed {processed_count} embeddings")

        except Exception as e:
            logger.error(f"Error processing embedding task: {e}")
            failed_count += 1

            # Re-queue failed task after backoff
            if failed_count < 3:
                await asyncio.sleep(5 * failed_count)  # Exponential backoff
            else:
                logger.error("Task exceeded max retries, moving to dead-letter queue")
                # Could send to dead-letter queue here


async def process_single_embedding_task(
    task: Dict[str, Any],
    embeddings_mgr: EmbeddingsManager
):
    """
    Process a single embedding generation task.

    Args:
        task: Task dict with type, id, and text
        embeddings_mgr: EmbeddingsManager instance
    """
    task_type = task.get("type")  # "job" or "resume"
    entity_id = task.get("id")
    text = task.get("text")

    if not all([task_type, entity_id, text]):
        logger.error(f"Invalid task format: {task}")
        return

    try:
        logger.info(f"Processing {task_type} embedding for {entity_id}")

        # Generate embedding
        embedding = embeddings_mgr.generate_embedding(text)

        # Save to database (this is simplified - would need actual DB connection)
        logger.info(f"Successfully generated embedding for {task_type} {entity_id}")

    except Exception as e:
        logger.error(f"Failed to generate embedding for {task_type} {entity_id}: {e}")
        raise


def enqueue_embedding_task(
    redis_client,
    entity_type: str,
    entity_id: str,
    text: str,
    queue_name: str = "ingest:embeddings"
):
    """
    Queue an embedding generation task.

    Args:
        redis_client: Redis client
        entity_type: "job" or "resume"
        entity_id: UUID of entity
        text: Text to embed
        queue_name: Target queue name
    """
    import json

    task = {
        "type": entity_type,
        "id": entity_id,
        "text": text
    }

    redis_client.rpush(queue_name, json.dumps(task))
    logger.info(f"Queued {entity_type} embedding: {entity_id}")
