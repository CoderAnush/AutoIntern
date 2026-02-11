"""Security dependencies for protected routes using JWT tokens."""

import logging
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import AuthService
from app.core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
) -> dict:
    """
    Dependency to validate JWT token and extract user info from protected routes.

    This dependency:
    1. Extracts Bearer token from Authorization header
    2. Validates JWT signature
    3. Checks token expiry
    4. Validates token is 'access' type
    5. Returns user claims

    Args:
        credentials: HTTPAuthCredentials from Authorization header

    Returns:
        Dictionary with user_id and email

    Raises:
        HTTPException(401): If token is missing, invalid, expired, or wrong type
    """
    token = credentials.credentials

    try:
        # Validate token signature and expiry
        payload = AuthService.decode_token(token, settings.secret_key)

        # Verify this is an access token, not a refresh token
        if not AuthService.verify_token_type(token, settings.secret_key, "access"):
            logger.warning("Invalid token type in Authorization header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Use access token for this endpoint.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload.get("user_id")
        if user_id is None:
            logger.warning("Token missing user_id claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.debug(f"User authenticated: {user_id}")
        return {"user_id": user_id, "email": payload.get("email")}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthCredentials] = Depends(security),
) -> Optional[dict]:
    """
    Optional version of get_current_user for semi-protected routes.

    Returns user info if valid token provided, None otherwise.
    Does not raise 401, allowing unauthenticated access.

    Args:
        credentials: Optional HTTPAuthCredentials from Authorization header

    Returns:
        Dictionary with user_id if token valid, None otherwise
    """
    if not credentials:
        return None

    token = credentials.credentials

    try:
        payload = AuthService.decode_token(token, settings.secret_key)

        # Verify this is an access token
        if not AuthService.verify_token_type(token, settings.secret_key, "access"):
            return None

        user_id = payload.get("user_id")
        if user_id is None:
            return None

        logger.debug(f"Optional user authenticated: {user_id}")
        return {"user_id": user_id, "email": payload.get("email")}

    except Exception as e:
        logger.debug(f"Optional user not authenticated: {e}")
        return None


def create_token_response(user_id: str, secret_key: str) -> dict:
    """
    Create both access and refresh tokens for authenticated user.

    Args:
        user_id: UUID of authenticated user
        secret_key: Secret key for signing tokens

    Returns:
        Dictionary with access_token, refresh_token, token_type, expires_in
    """
    try:
        # Create access token (30 min)
        access_token, access_expiry = AuthService.create_access_token(
            user_id=user_id,
            secret_key=secret_key
        )

        # Create refresh token (7 days)
        refresh_token, refresh_expiry = AuthService.create_refresh_token(
            user_id=user_id,
            secret_key=secret_key
        )

        # Calculate seconds until access token expiry
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        expires_in = int((access_expiry - now).total_seconds())

        logger.info(f"Token response created for user: {user_id}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in
        }

    except Exception as e:
        logger.error(f"Error creating token response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create authentication tokens"
        )


def get_token_expiry_seconds(token: str, secret_key: str) -> int:
    """
    Get remaining seconds until token expiration.

    Args:
        token: JWT token string
        secret_key: Secret key used to sign token

    Returns:
        Seconds remaining until expiry
    """
    try:
        return AuthService.get_token_expiry_seconds(token, secret_key)
    except Exception as e:
        logger.error(f"Error getting token expiry: {e}")
        return 0
