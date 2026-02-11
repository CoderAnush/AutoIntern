"""
Account Lockout Service - Phase 8 Security Hardening

Implements account lockout mechanism to prevent brute force attacks by tracking
failed login attempts and locking accounts after a configurable threshold.

Failed attempts are tracked in the database:
- failed_login_attempts: Counter for consecutive failed attempts
- locked_until: DateTime when account becomes unlocked (NULL = not locked)
- last_login_attempt: Timestamp of last login attempt

Usage:
    lockout_service = AccountLockout(db_session)

    # Check if account is locked
    if await lockout_service.is_locked(user_id):
        remaining = await lockout_service.get_lockout_time_remaining(user_id)
        raise HTTPException(status_code=403, detail=f"Account locked for {remaining}s")

    # Record failed attempt
    failed_count = await lockout_service.record_failed_attempt(user_id)
    if failed_count >= 5:
        raise HTTPException(status_code=403, detail="Account locked for 15 minutes")

    # Reset attempts on successful login
    await lockout_service.reset_attempts(user_id)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.models import User

logger = logging.getLogger(__name__)


class AccountLockoutConfig:
    """Account lockout configuration."""

    MAX_FAILED_ATTEMPTS = 5  # Lock after this many failed attempts
    LOCKOUT_DURATION_MINUTES = 15  # Duration of lockout
    RESET_ATTEMPTS_AFTER_MINUTES = 30  # Reset counter if no login for this duration


class AccountLockout:
    """Manages account lockout after failed login attempts."""

    def __init__(
        self,
        db: AsyncSession,
        max_failed_attempts: int = AccountLockoutConfig.MAX_FAILED_ATTEMPTS,
        lockout_duration_minutes: int = AccountLockoutConfig.LOCKOUT_DURATION_MINUTES,
        reset_attempts_after_minutes: int = AccountLockoutConfig.RESET_ATTEMPTS_AFTER_MINUTES,
    ):
        """
        Initialize account lockout service.

        Args:
            db: Async database session
            max_failed_attempts: Max failed attempts before lockout
            lockout_duration_minutes: Duration of lockout in minutes
            reset_attempts_after_minutes: Reset counter if no login for this duration
        """
        self.db = db
        self.max_failed_attempts = max_failed_attempts
        self.lockout_duration_minutes = lockout_duration_minutes
        self.reset_attempts_after_minutes = reset_attempts_after_minutes

    async def record_failed_attempt(self, user_id: UUID) -> int:
        """
        Record a failed login attempt for a user.

        Increments failed_login_attempts counter. If it reaches the threshold,
        locks the account by setting locked_until.

        Args:
            user_id: User UUID

        Returns:
            Current failed attempt count after incrementing

        Raises:
            Exception: If database error occurs
        """
        try:
            # Get current user
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"Failed login attempt recorded for non-existent user: {user_id}")
                return 0

            # Reset attempts if window expired
            if user.last_login_attempt:
                time_since_last = datetime.utcnow() - user.last_login_attempt
                reset_window = timedelta(minutes=self.reset_attempts_after_minutes)
                if time_since_last > reset_window:
                    user.failed_login_attempts = 0
                    logger.info(f"Reset failed attempts for user {user_id} (window expired)")

            # Increment failed attempts
            user.failed_login_attempts += 1
            user.last_login_attempt = datetime.utcnow()

            # Lock account if threshold reached
            if user.failed_login_attempts >= self.max_failed_attempts:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=self.lockout_duration_minutes
                )
                logger.warning(
                    f"Account locked for user {user_id} after "
                    f"{user.failed_login_attempts} failed attempts"
                )

            await self.db.commit()

            return user.failed_login_attempts

        except Exception as e:
            logger.error(f"Error recording failed attempt for user {user_id}: {e}")
            raise

    async def get_failed_attempts(self, user_id: UUID) -> int:
        """
        Get current failed attempt count for a user.

        Args:
            user_id: User UUID

        Returns:
            Count of failed attempts (0 if user not found)
        """
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                return 0

            # Check if reset window expired
            if user.last_login_attempt:
                time_since_last = datetime.utcnow() - user.last_login_attempt
                reset_window = timedelta(minutes=self.reset_attempts_after_minutes)
                if time_since_last > reset_window:
                    # Would be reset on next attempt, but report as 0 now
                    return 0

            return user.failed_login_attempts

        except Exception as e:
            logger.error(f"Error getting failed attempts for user {user_id}: {e}")
            return 0

    async def is_locked(self, user_id: UUID) -> bool:
        """
        Check if a user's account is currently locked.

        Args:
            user_id: User UUID

        Returns:
            True if account is locked, False otherwise
        """
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                return False

            # Check if locked_until is set and in future
            if user.locked_until:
                if datetime.utcnow() < user.locked_until:
                    logger.debug(f"Account locked for user {user_id}")
                    return True
                else:
                    # Lockout expired, unlock account
                    await self.unlock_account(user_id)
                    return False

            return False

        except Exception as e:
            logger.error(f"Error checking lockout status for user {user_id}: {e}")
            return False

    async def get_lockout_time_remaining(self, user_id: UUID) -> int:
        """
        Get seconds remaining until account is unlocked.

        Args:
            user_id: User UUID

        Returns:
            Seconds until unlock (0 if not locked or already expired)
        """
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user or not user.locked_until:
                return 0

            remaining = user.locked_until - datetime.utcnow()
            remaining_seconds = max(int(remaining.total_seconds()), 0)

            return remaining_seconds

        except Exception as e:
            logger.error(f"Error getting lockout time for user {user_id}: {e}")
            return 0

    async def unlock_account(self, user_id: UUID) -> None:
        """
        Manually unlock a user's account.

        Used when lockout period expires or for admin unlock.

        Args:
            user_id: User UUID
        """
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.locked_until = None
                user.failed_login_attempts = 0
                await self.db.commit()
                logger.info(f"Account unlocked for user {user_id}")

        except Exception as e:
            logger.error(f"Error unlocking account for user {user_id}: {e}")
            raise

    async def reset_attempts(self, user_id: UUID) -> None:
        """
        Reset failed attempts counter (called after successful login).

        Args:
            user_id: User UUID
        """
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.failed_login_attempts = 0
                user.locked_until = None
                user.last_login_attempt = datetime.utcnow()
                await self.db.commit()
                logger.info(f"Failed attempts reset for user {user_id}")

        except Exception as e:
            logger.error(f"Error resetting attempts for user {user_id}: {e}")
            raise

    async def get_lockout_info(self, user_id: UUID) -> dict:
        """
        Get complete lockout information for a user.

        Args:
            user_id: User UUID

        Returns:
            Dict with lockout status, failed attempts, and remaining time
        """
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                return {
                    "is_locked": False,
                    "failed_attempts": 0,
                    "locked_until": None,
                    "remaining_seconds": 0,
                }

            is_locked = await self.is_locked(user_id)
            remaining = await self.get_lockout_time_remaining(user_id)

            return {
                "is_locked": is_locked,
                "failed_attempts": user.failed_login_attempts,
                "max_failed_attempts": self.max_failed_attempts,
                "locked_until": user.locked_until.isoformat() if user.locked_until else None,
                "remaining_seconds": remaining,
            }

        except Exception as e:
            logger.error(f"Error getting lockout info for user {user_id}: {e}")
            return {
                "is_locked": False,
                "failed_attempts": 0,
                "locked_until": None,
                "remaining_seconds": 0,
            }
