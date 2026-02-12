"""User authentication routes for registration, login, and profile management."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import User as UserModel
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    PasswordChange,
    TokenRefresh,
    PasswordChangeResponse
)
from app.services.auth_service import AuthService
from app.core.validators import PasswordValidator
from app.core.security import get_current_user, create_token_response
from app.core.config import settings
from uuid import uuid4

# Phase 8: Security Hardening
from app.services.rate_limiter import get_rate_limiter, RateLimitConfig
from app.services.account_lockout import AccountLockout

logger = logging.getLogger(__name__)

router = APIRouter()

# Phase 8 deployment - Redis pooling and UUID serializeation fixes applied


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user with email and password.

    Validation:
    - Email format validation (EmailStr)
    - Email must not already exist
    - Password must meet strength requirements
    - Rate limiting: 3 registrations per hour per email

    Args:
        user_data: UserCreate with email and password
        db: AsyncSession for database operations

    Returns:
        UserResponse with id, email, created_at (201 Created)

    Raises:
        429: Too many registration attempts (rate limited)
        400: Email already exists or password too weak
    """
    try:
        # Phase 8: Rate limiting on registration endpoint
        rate_limiter = await get_rate_limiter(settings.redis_url)

        is_allowed, count, reset_seconds = await rate_limiter.is_allowed(
            key=f"register:{user_data.email.lower()}",
            max_requests=RateLimitConfig.REGISTER_MAX_REQUESTS,
            window_seconds=RateLimitConfig.REGISTER_WINDOW_SECONDS
        )

        if not is_allowed:
            logger.warning(f"Registration rate limit exceeded for: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many registration attempts. Try again in {reset_seconds} seconds.",
                headers={"Retry-After": str(reset_seconds)}
            )

        # Validate password strength
        is_valid_password, error_msg = PasswordValidator.validate_password(user_data.password)
        if not is_valid_password:
            logger.warning(f"Registration failed - weak password for {user_data.email}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password is too weak: {error_msg}"
            )

        # Check if email already registered
        existing_user_result = await db.execute(
            select(UserModel).where(UserModel.email == user_data.email.lower())
        )
        existing_user = existing_user_result.scalars().first()

        if existing_user:
            logger.warning(f"Registration failed - email already registered: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password
        password_hash = AuthService.hash_password(user_data.password)

        # Create user
        new_user = UserModel(
            id=str(uuid4()),
            email=user_data.email.lower(),
            password_hash=password_hash,
            is_active=True
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"User registered successfully: {new_user.email}")

        # Queue welcome email (Phase 7)
        try:
            from app.services.email_queue import EmailQueue
            email_queue = EmailQueue(settings.redis_url)
            await email_queue.connect()

            user_name = new_user.email.split("@")[0]  # Get first part of email as display name
            await email_queue.enqueue_welcome_email(
                user_id=str(new_user.id),
                user_email=new_user.email,
                user_name=user_name
            )

            logger.info(f"Welcome email queued for: {new_user.email}")
        except Exception as e:
            logger.error(f"Failed to queue welcome email for {new_user.email}: {e}")
            # Don't fail registration if email queueing fails

        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            created_at=new_user.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Login with email and password to receive tokens.

    Security Features (Phase 8):
    - Rate limiting: 5 login attempts per 5 minutes per email
    - Account lockout: After 5 failed attempts, lock for 15 minutes

    Returns:
    - access_token: 30-minute JWT for API requests
    - refresh_token: 7-day JWT for getting new access tokens

    Args:
        credentials: UserLogin with email and password
        db: AsyncSession for database operations

    Returns:
        TokenResponse with access_token, refresh_token, expires_in (200 OK)

    Raises:
        429: Too many login attempts (rate limited)
        403: Account locked due to failed attempts
        401: User not found or invalid password
    """
    try:
        email_lower = credentials.email.lower()

        # Phase 8: Rate limiting on login endpoint (5 per 5 minutes)
        rate_limiter = await get_rate_limiter(settings.redis_url)

        is_allowed, count, reset_seconds = await rate_limiter.is_allowed(
            key=f"login:{email_lower}",
            max_requests=RateLimitConfig.LOGIN_MAX_REQUESTS,
            window_seconds=RateLimitConfig.LOGIN_WINDOW_SECONDS
        )

        if not is_allowed:
            logger.warning(f"Login rate limit exceeded for: {email_lower}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many login attempts. Try again in {reset_seconds} seconds.",
                headers={"Retry-After": str(reset_seconds)}
            )

        # Find user by email
        user_result = await db.execute(
            select(UserModel).where(UserModel.email == email_lower)
        )
        user = user_result.scalars().first()

        if not user:
            logger.warning(f"Login failed - user not found: {email_lower}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Phase 8: Check account lockout
        lockout_service = AccountLockout(db)
        if await lockout_service.is_locked(user.id):
            remaining_seconds = await lockout_service.get_lockout_time_remaining(user.id)
            logger.warning(f"Login failed - account locked for: {email_lower}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is locked due to too many failed attempts. Try again in {remaining_seconds} seconds.",
                headers={"Retry-After": str(remaining_seconds)}
            )

        # Verify password
        if not AuthService.verify_password(credentials.password, user.password_hash):
            # Record failed login attempt
            failed_attempts = await lockout_service.record_failed_attempt(user.id)
            logger.warning(f"Login failed - invalid password for: {email_lower} (attempt {failed_attempts})")

            # Check if now locked
            if await lockout_service.is_locked(user.id):
                remaining_seconds = await lockout_service.get_lockout_time_remaining(user.id)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Too many failed login attempts. Account locked for {remaining_seconds} seconds.",
                    headers={"Retry-After": str(remaining_seconds)}
                )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Verify user is active
        if not user.is_active:
            logger.warning(f"Login failed - user inactive: {email_lower}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )

        # Successful login - reset failed attempts
        await lockout_service.reset_attempts(user.id)
        logger.info(f"User logged in successfully: {user.email}")

        # Create tokens
        token_response = create_token_response(user.id, settings.secret_key)

        return TokenResponse(**token_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process login"
        )


@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """
    Refresh an expired access token using a valid refresh token.

    The refresh token must be valid and not expired (7 days max).
    Returns a new access token and refresh token pair.

    Args:
        token_data: TokenRefresh with refresh_token
        db: AsyncSession for database operations

    Returns:
        TokenResponse with new access_token, refresh_token, expires_in

    Raises:
        401: Refresh token invalid, expired, or wrong type
    """
    try:
        # Validate refresh token
        try:
            payload = AuthService.decode_token(token_data.refresh_token, settings.secret_key)
        except ValueError as e:
            logger.warning(f"Invalid refresh token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        # Verify this is a refresh token
        if not AuthService.verify_token_type(token_data.refresh_token, settings.secret_key, "refresh"):
            logger.warning("Refresh token validation failed - wrong token type")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Use refresh token for this endpoint."
            )

        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims"
            )

        # Verify user still exists and is active
        user = await db.get(UserModel, user_id)
        if not user or not user.is_active:
            logger.warning(f"Refresh failed - user not found or inactive: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or account inactive"
            )

        # Create new token pair
        token_response = create_token_response(user.id, settings.secret_key)

        logger.info(f"Token refreshed for user: {user.email}")

        return TokenResponse(**token_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get currently authenticated user's profile information.

    Protected endpoint requiring valid access token.

    Returns:
        UserResponse with user id, email, and created_at

    Raises:
        401: No valid token provided
    """
    try:
        user_id = current_user.get("user_id")
        user = await db.get(UserModel, user_id)

        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        logger.debug(f"User profile retrieved: {user.email}")

        return UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.post("/change-password", response_model=PasswordChangeResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change password for currently authenticated user.

    Protected endpoint requiring valid access token.
    Validates old password and enforces new password strength rules.

    Security Features (Phase 8):
    - Rate limiting: 3 password changes per hour

    Args:
        password_data: PasswordChange with old_password and new_password
        current_user: Current authenticated user
        db: AsyncSession for database operations

    Returns:
        PasswordChangeResponse with success message

    Raises:
        429: Too many password change attempts (rate limited)
        400: Old password incorrect, new password weak, or passwords identical
    """
    try:
        user_id = current_user.get("user_id")

        # Phase 8: Rate limiting on password change endpoint (3 per hour)
        rate_limiter = await get_rate_limiter(settings.redis_url)

        is_allowed, count, reset_seconds = await rate_limiter.is_allowed(
            key=f"change_password:{user_id}",
            max_requests=RateLimitConfig.PASSWORD_CHANGE_MAX_REQUESTS,
            window_seconds=RateLimitConfig.PASSWORD_CHANGE_WINDOW_SECONDS
        )

        if not is_allowed:
            logger.warning(f"Password change rate limit exceeded for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many password change attempts. Try again in {reset_seconds} seconds.",
                headers={"Retry-After": str(reset_seconds)}
            )

        user = await db.get(UserModel, user_id)

        if not user:
            logger.warning(f"User not found for password change: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify old password
        if not AuthService.verify_password(password_data.old_password, user.password_hash):
            logger.warning(f"Password change failed - incorrect old password for: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Old password is incorrect"
            )

        # Validate new password strength
        is_valid_password, error_msg = PasswordValidator.validate_password(password_data.new_password)
        if not is_valid_password:
            logger.warning(f"Password change failed - weak new password for: {user.email}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"New password is too weak: {error_msg}"
            )

        # Check new password is different from old
        if password_data.old_password == password_data.new_password:
            logger.warning(f"Password change failed - passwords identical for: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from old password"
            )

        # Hash and update new password
        new_password_hash = AuthService.hash_password(password_data.new_password)
        user.password_hash = new_password_hash
        await db.commit()

        logger.info(f"Password changed successfully for user: {user.email}")

        # Queue password change notification email (Phase 7)
        try:
            from app.services.email_queue import EmailQueue
            email_queue = EmailQueue(settings.redis_url)
            await email_queue.connect()

            user_name = user.email.split("@")[0]  # Get first part of email as display name
            await email_queue.enqueue_password_change_email(
                user_id=str(user.id),
                user_email=user.email,
                user_name=user_name
            )

            logger.info(f"Password change notification email queued for: {user.email}")
        except Exception as e:
            logger.error(f"Failed to queue password change email for {user.email}: {e}")
            # Don't fail password change if email queueing fails

        return PasswordChangeResponse(msg="Password changed successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout user (placeholder endpoint).

    In JWT-based systems, logout is typically client-side (delete token from storage).
    This endpoint serves as a confirmation endpoint and could be extended to:
    - Add token to blacklist in Redis (if implementing token blacklist)
    - Trigger audit logging
    - Notify user of session termination

    Protected endpoint requiring valid access token.

    Returns:
        204 No Content
    """
    try:
        user_id = current_user.get("user_id")
        logger.info(f"User logged out: {user_id}")
        # In production, could add token to blacklist, trigger events, etc.
        return None

    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout"
        )
