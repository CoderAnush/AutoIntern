"""
Security Headers Middleware - Phase 8 Security Hardening

Adds OWASP-recommended security headers to all HTTP responses to protect against:
- XSS (Cross-Site Scripting)
- Clickjacking
- MIME type sniffing
- CSS/JS injection
- HSTS downgrade attacks

Headers added:
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- X-Frame-Options: DENY
- Content-Security-Policy: Restricts resource loading
- Strict-Transport-Security: HTTPS enforcement (1 year)
- Referrer-Policy: Limits referrer info leakage
- Permissions-Policy: Disables unnecessary browser features
"""

import logging
from fastapi import Request
from fastapi.responses import Response

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """Middleware to add security headers to all responses."""

    def __init__(self, app):
        """
        Initialize middleware.

        Args:
            app: FastAPI application instance
        """
        self.app = app

    async def __call__(self, request: Request, call_next):
        """
        Process request and add security headers to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            Response with security headers added
        """
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection (legacy, for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Clickjacking protection - deny all framing
        response.headers["X-Frame-Options"] = "DENY"

        # Content Security Policy
        # - default-src 'self': Only allow resources from same origin by default
        # - script-src 'self' 'unsafe-inline': Allow scripts from same origin and inline
        # - style-src 'self' 'unsafe-inline': Allow styles from same origin and inline
        # Note: In production, remove 'unsafe-inline' and use nonces or CSP hashes
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp

        # HSTS: Force HTTPS for 1 year (31536000 seconds)
        # includeSubDomains: Apply to all subdomains
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        # Referrer Policy: Don't leak referrer across origins except same-site
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature Policy): Disable unnecessary features
        # - geolocation=(): disable geolocation
        # - camera=(): disable camera
        # - microphone=(): disable microphone
        # - accelerometer=(), magnetometer=(), gyroscope=(): disable motion sensors
        permissions = (
            "geolocation=(), "
            "camera=(), "
            "microphone=(), "
            "accelerometer=(), "
            "magnetometer=(), "
            "gyroscope=()"
        )
        response.headers["Permissions-Policy"] = permissions

        # Custom server header (don't advertise exact technology)
        response.headers["Server"] = "AutoIntern"

        # Remove potentially dangerous headers if present
        response.headers.pop("X-Powered-By", None)
        response.headers.pop("X-AspNet-Version", None)
        response.headers.pop("X-Runtime-Version", None)

        logger.debug(f"Security headers added to response for {request.method} {request.url.path}")

        return response


def add_security_headers(app):
    """
    Add security headers middleware to FastAPI app.

    Should be added AFTER CORS middleware to avoid CORS issues.

    Usage in main.py:
        from app.middleware.security_headers import add_security_headers
        app = FastAPI()
        # ... CORS middleware first ...
        add_security_headers(app)

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers middleware added to application")
