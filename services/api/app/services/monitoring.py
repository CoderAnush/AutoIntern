"""
Monitoring Service - Phase 8 Security Hardening

Provides health checks and performance metrics for monitoring system status
and supporting Kubernetes liveness/readiness probes.

Endpoints:
- GET /health - General health check
- GET /health/live - Kubernetes liveness probe
- GET /health/ready - Kubernetes readiness probe (checks dependencies)
- GET /metrics/summary - Performance metrics (protected)
- GET /metrics/errors/recent - Recent error statistics (protected)
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import redis.asyncio as redis

from app.models.models import RequestLog

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitor system health and provide metrics."""

    def __init__(
        self,
        db_session: Optional[AsyncSession] = None,
        redis_url: str = "redis://localhost:6379/0",
    ):
        """
        Initialize health monitor.

        Args:
            db_session: Async database session
            redis_url: Redis connection URL
        """
        self.db_session = db_session
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis_client = await redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Health monitor connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for health monitoring: {e}")

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()

    async def check_database(self) -> bool:
        """
        Check if database is healthy by running a simple query.

        Args:
            None

        Returns:
            True if database is healthy, False otherwise
        """
        if not self.db_session:
            return False

        try:
            # Simple health check query
            await self.db_session.execute(select(func.now()))
            logger.debug("Database health check: OK")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def check_redis(self) -> bool:
        """
        Check if Redis is healthy by running PING command.

        Args:
            None

        Returns:
            True if Redis is healthy, False otherwise
        """
        if not self.redis_client:
            try:
                await self.connect()
            except Exception:
                return False

        try:
            await self.redis_client.ping()
            logger.debug("Redis health check: OK")
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def check_server(self) -> bool:
        """
        Check if server is running.

        This always returns True since we're executing this code.

        Returns:
            Always True
        """
        return True

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics from request logs.

        Calculates:
        - requests_total: Total requests since tracking started
        - requests_per_minute: Average requests per minute (last hour)
        - error_rate: Percentage of requests with status >= 400
        - average_response_time_ms: Average response time
        - error_rate_by_status: Count of each error status

        Returns:
            Dict with metrics or empty dict if data unavailable
        """
        if not self.db_session:
            return {
                "requests_total": 0,
                "requests_per_minute": 0,
                "error_rate": 0,
                "average_response_time_ms": 0,
                "database_connections": 0,
                "cache_hit_rate": 0,
            }

        try:
            # Get metrics from last hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)

            # Total requests
            total_result = await self.db_session.execute(
                select(func.count(RequestLog.id)).where(
                    RequestLog.created_at >= one_hour_ago
                )
            )
            total_requests = total_result.scalar() or 0

            # Requests per minute
            requests_per_minute = total_requests // 60 if total_requests > 0 else 0

            # Error rate
            error_result = await self.db_session.execute(
                select(func.count(RequestLog.id)).where(
                    and_(
                        RequestLog.created_at >= one_hour_ago,
                        RequestLog.status_code >= 400,
                    )
                )
            )
            error_count = error_result.scalar() or 0
            error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0

            # Average response time
            avg_time_result = await self.db_session.execute(
                select(func.avg(RequestLog.response_time_ms)).where(
                    RequestLog.created_at >= one_hour_ago
                )
            )
            avg_response_time = avg_time_result.scalar() or 0

            return {
                "requests_total": total_requests,
                "requests_per_minute": int(requests_per_minute),
                "error_rate": round(error_rate, 2),
                "average_response_time_ms": int(avg_response_time),
                "errors_last_hour": error_count,
            }

        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {}

    async def get_recent_errors(self, hours: int = 1) -> Dict[str, Any]:
        """
        Get recent errors grouped by status and path.

        Args:
            hours: Number of hours to look back

        Returns:
            Dict with error statistics
        """
        if not self.db_session:
            return {"errors": []}

        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            # Get errors grouped by status and path
            result = await self.db_session.execute(
                select(
                    RequestLog.status_code,
                    RequestLog.path,
                    func.count(RequestLog.id).label("count"),
                    func.max(RequestLog.created_at).label("last_error"),
                ).where(
                    and_(
                        RequestLog.created_at >= cutoff_time,
                        RequestLog.status_code >= 400,
                    )
                )
                .group_by(RequestLog.status_code, RequestLog.path)
                .order_by(func.count(RequestLog.id).desc())
            )

            errors = []
            for row in result.all():
                errors.append({
                    "status": row.status_code,
                    "path": row.path,
                    "count": row.count,
                    "last_occurrence": row.last_error.isoformat() if row.last_error else None,
                })

            return {
                "time_period_hours": hours,
                "errors": errors,
                "total_errors": sum(e["count"] for e in errors),
            }

        except Exception as e:
            logger.error(f"Failed to get recent errors: {e}")
            return {"errors": []}

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall health status.

        Returns:
            Dict with:
            - status: "healthy", "degraded", or "unhealthy"
            - timestamp: Current ISO timestamp
            - db: "ok" or "error"
            - redis: "ok" or "error"
            - details: Detailed health information
        """
        db_ok = await self.check_database()
        redis_ok = await self.check_redis()

        if db_ok and redis_ok:
            status = "healthy"
        elif db_ok or redis_ok:
            status = "degraded"
        else:
            status = "unhealthy"

        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "db": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
            "checks_passed": sum([db_ok, redis_ok]),
            "checks_total": 2,
        }


# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None


async def get_health_monitor(
    db_session: Optional[AsyncSession] = None,
    redis_url: str = "redis://localhost:6379/0",
) -> HealthMonitor:
    """
    Get or create global health monitor instance.

    Args:
        db_session: Async database session
        redis_url: Redis connection URL

    Returns:
        HealthMonitor instance
    """
    global _health_monitor

    if _health_monitor is None:
        _health_monitor = HealthMonitor(db_session, redis_url)
        await _health_monitor.connect()

    return _health_monitor
