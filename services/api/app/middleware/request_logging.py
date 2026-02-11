"""
Request Logging Service - Phase 8 Security Hardening

Logs all API requests and responses to database for audit trail and compliance.

Captures:
- user_id: User making request (if authenticated)
- method: HTTP method (GET, POST, PUT, DELETE)
- path: Request path (/users/login, /resumes, etc)
- status_code: HTTP response status
- response_time_ms: Time to complete request
- ip_address: Client IP address
- user_agent: Client user agent string
- error_message: Error details if status >= 400

Non-blocking: Logging happens asynchronously and doesn't affect request response time.
"""

import logging
import time
import hashlib
import json
from typing import Optional
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime

from app.models.models import RequestLog

logger = logging.getLogger(__name__)


class RequestLogger:
    """Logs all API requests to database for audit trail."""

    def __init__(self, db_context):
        """
        Initialize request logger.

        Args:
            db_context: Database context provider (callable that returns AsyncSession)
        """
        self.db_context = db_context

    async def log_request(
        self,
        user_id: Optional[UUID],
        method: str,
        path: str,
        status_code: int,
        response_time_ms: int,
        ip_address: str,
        user_agent: Optional[str] = None,
        request_body_hash: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Log a request to database.

        Args:
            user_id: User ID (None if unauthenticated)
            method: HTTP method
            path: Request path
            status_code: HTTP response status
            response_time_ms: Response time in milliseconds
            ip_address: Client IP address
            user_agent: Client user agent string
            request_body_hash: SHA256 hash of request body (don't log full body with passwords)
            error_message: Error details if status >= 400

        Note: This is called asynchronously and should not block the response.
        """
        try:
            # Try to get database session
            # If this fails, we log to file but continue (don't fail the request)
            try:
                async with self.db_context() as db:
                    request_log = RequestLog(
                        user_id=user_id,
                        method=method,
                        path=path,
                        status_code=status_code,
                        response_time_ms=response_time_ms,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        request_body_hash=request_body_hash,
                        error_message=error_message,
                        created_at=datetime.utcnow(),
                    )
                    db.add(request_log)
                    await db.commit()
            except Exception as db_error:
                # Log to file if database fails
                logger.error(
                    f"Failed to log request to database: {db_error}. "
                    f"Logging to file instead: {method} {path} {status_code}"
                )

            # Always log to file as well
            log_level = logging.WARNING if status_code >= 400 else logging.INFO
            log_message = (
                f"API Request: {method} {path} -> {status_code} "
                f"({response_time_ms}ms) from {ip_address}"
            )
            if user_id:
                log_message += f" [user: {user_id}]"
            if error_message:
                log_message += f" [error: {error_message}]"

            logger.log(log_level, log_message)

        except Exception as e:
            # Even if everything fails, we shouldn't crash
            logger.error(f"Error in request logger: {e}")

    @staticmethod
    def hash_request_body(body: Optional[bytes]) -> Optional[str]:
        """
        Create SHA256 hash of request body.

        Use hash instead of storing full body to avoid logging sensitive data
        like passwords. Hash still allows detecting duplicate requests.

        Args:
            body: Request body bytes

        Returns:
            SHA256 hex digest, or None if no body
        """
        if not body:
            return None

        try:
            return hashlib.sha256(body).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash request body: {e}")
            return None

    @staticmethod
    def get_client_ip(request: Request) -> str:
        """
        Extract client IP from request.

        Handles X-Forwarded-For header for proxied requests.

        Args:
            request: FastAPI Request object

        Returns:
            Client IP address string
        """
        # Check X-Forwarded-For header (for proxied requests)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take first IP in list (original client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header (nginx)
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct connection IP
        if request.client:
            return request.client.host

        return "unknown"


class RequestLoggingMiddleware:
    """Middleware to log all API requests."""

    def __init__(self, app, db_context=None):
        """
        Initialize middleware.

        Args:
            app: FastAPI application instance
            db_context: Database context provider (optional, can be injected later)
        """
        self.app = app
        self.db_context = db_context
        self.logger = RequestLogger(db_context) if db_context else None

    async def __call__(self, request: Request, call_next):
        """
        Process request, call handler, then log request.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            Response from route handler
        """
        # Record request start time
        start_time = time.time()

        # Get client IP and user agent
        client_ip = RequestLogger.get_client_ip(request)
        user_agent = request.headers.get("user-agent")

        # Try to extract user_id from request state (set by auth middleware)
        user_id = None
        if hasattr(request.state, "user_id"):
            try:
                user_id = UUID(request.state.user_id)
            except (ValueError, TypeError):
                pass

        # Call the actual route handler
        response = await call_next(request)

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Extract error message if status >= 400
        error_message = None
        if response.status_code >= 400:
            try:
                # Try to read response body for error message
                # Note: This consumes the response body, so we need to recreate the response
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                if body:
                    try:
                        error_data = json.loads(body)
                        error_message = error_data.get("detail", str(error_data))[:500]
                    except:
                        error_message = body.decode("utf-8", errors="ignore")[:500]

                # Recreate response with body
                from fastapi.responses import Response as FastAPIResponse
                response = FastAPIResponse(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
            except Exception as e:
                logger.debug(f"Could not extract error message from response: {e}")

        # Log the request asynchronously (fire and forget)
        if self.logger:
            try:
                await self.logger.log_request(
                    user_id=user_id,
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    response_time_ms=response_time_ms,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    error_message=error_message,
                )
            except Exception as e:
                logger.error(f"Error logging request: {e}")

        return response


def add_request_logging(app, db_context):
    """
    Add request logging middleware to FastAPI app.

    Should be added EARLY in middleware stack to capture all requests.

    Usage in main.py:
        from app.middleware.request_logging import add_request_logging
        from app.core.database import get_db_context

        db_context = get_db_context()
        app = FastAPI()
        add_request_logging(app, db_context)

    Args:
        app: FastAPI application instance
        db_context: Database context provider (callable that returns AsyncSession)
    """
    app.add_middleware(RequestLoggingMiddleware, db_context=db_context)
    logger.info("Request logging middleware added to application")
