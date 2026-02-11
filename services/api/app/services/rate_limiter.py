"""
Rate Limiting Service - Phase 8 Security Hardening

Implements Redis-based sliding window rate limiting to prevent brute force attacks
on authentication endpoints and enforce API usage limits.

Usage:
    rate_limiter = RateLimiter(redis_url="redis://localhost:6379/0")
    is_allowed, count, reset_seconds = await rate_limiter.is_allowed(
        key=f"login:{email}",
        max_requests=5,
        window_seconds=300
    )
    if not is_allowed:
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded. Try again in {reset_seconds}s")
"""

import redis.asyncio as redis
import time
import logging
from typing import Tuple, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-based sliding window rate limiter."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize rate limiter.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis_client = await redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Rate limiter connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Rate limiter disconnected from Redis")

    async def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """
        Check if a request is allowed under rate limit.

        Uses sliding window algorithm:
        1. Get current counter for key
        2. If counter >= max_requests, reject (rate limited)
        3. If counter < max_requests, increment and allow
        4. Set expiry to window_seconds

        Args:
            key: Unique identifier (e.g., "login:user@example.com")
            max_requests: Max requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of:
            - is_allowed (bool): True if request allowed
            - current_count (int): Current request count in window
            - reset_after_seconds (int): Seconds until counter resets
        """
        if not self.redis_client:
            await self.connect()

        try:
            # Get current count
            current_count = await self.redis_client.incr(key)

            # Set expiry on first request
            if current_count == 1:
                await self.redis_client.expire(key, window_seconds)
                ttl = window_seconds
            else:
                # Get remaining TTL
                ttl = await self.redis_client.ttl(key)
                if ttl == -1:
                    # Key exists but no expiry (shouldn't happen, but handle it)
                    await self.redis_client.expire(key, window_seconds)
                    ttl = window_seconds
                elif ttl == -2:
                    # Key doesn't exist (race condition)
                    current_count = 1
                    await self.redis_client.expire(key, window_seconds)
                    ttl = window_seconds

            # Check if rate limit exceeded
            is_allowed = current_count <= max_requests

            logger.debug(
                f"Rate limit check: key={key}, count={current_count}, "
                f"max={max_requests}, allowed={is_allowed}, ttl={ttl}s"
            )

            return is_allowed, current_count, max(ttl, 0)

        except Exception as e:
            logger.error(f"Rate limiter error for key {key}: {e}")
            # On error, allow the request (fail open for availability)
            return True, 0, 0

    async def get_request_count(self, key: str) -> int:
        """
        Get current request count for a key.

        Args:
            key: Rate limit key

        Returns:
            Current count (0 if key doesn't exist)
        """
        if not self.redis_client:
            await self.connect()

        try:
            count = await self.redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Failed to get request count for {key}: {e}")
            return 0

    async def reset(self, key: str) -> None:
        """
        Manually reset rate limit counter for a key.

        Args:
            key: Rate limit key to reset
        """
        if not self.redis_client:
            await self.connect()

        try:
            await self.redis_client.delete(key)
            logger.info(f"Rate limit counter reset for: {key}")
        except Exception as e:
            logger.error(f"Failed to reset rate limit for {key}: {e}")

    async def clear_all(self) -> None:
        """Clear all rate limit counters (use with caution)."""
        if not self.redis_client:
            await self.connect()

        try:
            # Find all rate limit keys (pattern: *:{identifier})
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor, match="rate_limit:*", count=100
                )
                if keys:
                    deleted_count += await self.redis_client.delete(*keys)
                if cursor == 0:
                    break

            logger.info(f"Cleared {deleted_count} rate limit counters")
        except Exception as e:
            logger.error(f"Failed to clear rate limits: {e}")

    async def get_remaining_time(self, key: str) -> int:
        """
        Get remaining time in seconds until counter resets.

        Args:
            key: Rate limit key

        Returns:
            Seconds until reset (0 if key doesn't exist or no expiry)
        """
        if not self.redis_client:
            await self.connect()

        try:
            ttl = await self.redis_client.ttl(key)
            return max(ttl, 0)
        except Exception as e:
            logger.error(f"Failed to get remaining time for {key}: {e}")
            return 0


# Configuration constants for rate limiting
class RateLimitConfig:
    """Rate limiting configuration."""

    # Authentication endpoints (strict limits)
    LOGIN_MAX_REQUESTS = 5
    LOGIN_WINDOW_SECONDS = 300  # 5 per 5 minutes

    REGISTER_MAX_REQUESTS = 3
    REGISTER_WINDOW_SECONDS = 3600  # 3 per hour

    PASSWORD_CHANGE_MAX_REQUESTS = 3
    PASSWORD_CHANGE_WINDOW_SECONDS = 3600  # 3 per hour

    # General API endpoints (moderate limits)
    API_MAX_REQUESTS = 100
    API_WINDOW_SECONDS = 60  # 100 per minute

    # Upload endpoints (more lenient)
    UPLOAD_MAX_REQUESTS = 10
    UPLOAD_WINDOW_SECONDS = 60  # 10 per minute

    # Search endpoints
    SEARCH_MAX_REQUESTS = 50
    SEARCH_WINDOW_SECONDS = 60  # 50 per minute


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


async def get_rate_limiter(
    redis_url: str = "redis://localhost:6379/0",
) -> RateLimiter:
    """
    Get or create global rate limiter instance.

    Args:
        redis_url: Redis connection URL

    Returns:
        RateLimiter instance
    """
    global _rate_limiter

    if _rate_limiter is None:
        _rate_limiter = RateLimiter(redis_url)
        await _rate_limiter.connect()

    return _rate_limiter
