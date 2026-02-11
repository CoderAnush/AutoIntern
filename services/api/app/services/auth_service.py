"""Authentication service with password hashing and JWT token management."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from passlib.context import CryptContext
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

# Password hashing configuration - using argon2 (more stable than bcrypt)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT Configuration
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"


class AuthService:
    """Authentication business logic for password hashing and JWT token management."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt with 12 salt rounds.

        Args:
            password: Plain text password to hash

        Returns:
            Hashed password string

        Raises:
            ValueError: If password is empty
        """
        if not password:
            raise ValueError("Password cannot be empty")

        try:
            hashed = pwd_context.hash(password)
            logger.debug("Password hashed successfully")
            return hashed
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise ValueError(f"Failed to hash password: {str(e)}")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against a hashed password.

        Args:
            plain_password: Plain text password provided by user
            hashed_password: Hashed password stored in database

        Returns:
            True if password matches, False otherwise
        """
        try:
            is_valid = pwd_context.verify(plain_password, hashed_password)
            logger.debug(f"Password verification result: {is_valid}")
            return is_valid
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    @staticmethod
    def create_access_token(
        user_id: str,
        secret_key: str,
        expires_delta: Optional[timedelta] = None
    ) -> Tuple[str, datetime]:
        """
        Create a JWT access token with user ID claim.

        Args:
            user_id: UUID of the user
            secret_key: Secret key for signing token
            expires_delta: Custom expiration time (default: 30 minutes)

        Returns:
            Tuple of (token_string, expiration_datetime)

        Raises:
            ValueError: If user_id or secret_key is empty
        """
        if not user_id or not secret_key:
            raise ValueError("user_id and secret_key cannot be empty")

        try:
            if expires_delta is None:
                expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

            expire = datetime.now(timezone.utc) + expires_delta
            to_encode = {
                "user_id": user_id,
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": "access"
            }

            encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
            logger.info(f"Access token created for user: {user_id}")
            return encoded_jwt, expire

        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise ValueError(f"Failed to create access token: {str(e)}")

    @staticmethod
    def create_refresh_token(
        user_id: str,
        secret_key: str,
        expires_delta: Optional[timedelta] = None
    ) -> Tuple[str, datetime]:
        """
        Create a JWT refresh token with longer expiration.

        Args:
            user_id: UUID of the user
            secret_key: Secret key for signing token
            expires_delta: Custom expiration time (default: 7 days)

        Returns:
            Tuple of (token_string, expiration_datetime)

        Raises:
            ValueError: If user_id or secret_key is empty
        """
        if not user_id or not secret_key:
            raise ValueError("user_id and secret_key cannot be empty")

        try:
            if expires_delta is None:
                expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

            expire = datetime.now(timezone.utc) + expires_delta
            to_encode = {
                "user_id": user_id,
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": "refresh"
            }

            encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
            logger.info(f"Refresh token created for user: {user_id}")
            return encoded_jwt, expire

        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise ValueError(f"Failed to create refresh token: {str(e)}")

    @staticmethod
    def decode_token(token: str, secret_key: str) -> dict:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token string
            secret_key: Secret key used to sign the token

        Returns:
            Dictionary with claims (user_id, exp, iat, type)

        Raises:
            ValueError: If token is invalid, expired, or signature doesn't match
        """
        if not token or not secret_key:
            raise ValueError("token and secret_key cannot be empty")

        try:
            payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")

            if user_id is None:
                raise ValueError("Token missing user_id claim")

            logger.debug(f"Token decoded successfully for user: {user_id}")
            return payload

        except JWTError as e:
            logger.error(f"JWT decode error: {e}")
            raise ValueError(f"Invalid or expired token: {str(e)}")
        except Exception as e:
            logger.error(f"Error decoding token: {e}")
            raise ValueError(f"Failed to decode token: {str(e)}")

    @staticmethod
    def get_token_expiry_seconds(token: str, secret_key: str) -> int:
        """
        Get remaining seconds until token expiration.

        Args:
            token: JWT token string
            secret_key: Secret key used to sign the token

        Returns:
            Seconds remaining until expiry (0 if expired)
        """
        try:
            payload = AuthService.decode_token(token, secret_key)
            exp_timestamp = payload.get("exp")

            if exp_timestamp is None:
                return 0

            now = datetime.now(timezone.utc).timestamp()
            remaining_seconds = int(exp_timestamp - now)
            return max(0, remaining_seconds)

        except Exception as e:
            logger.error(f"Error getting token expiry: {e}")
            return 0

    @staticmethod
    def verify_token_type(token: str, secret_key: str, expected_type: str) -> bool:
        """
        Verify that token has the expected type (access or refresh).

        Args:
            token: JWT token string
            secret_key: Secret key used to sign the token
            expected_type: Expected token type ("access" or "refresh")

        Returns:
            True if token type matches, False otherwise
        """
        try:
            payload = AuthService.decode_token(token, secret_key)
            token_type = payload.get("type")
            is_valid = token_type == expected_type
            logger.debug(f"Token type verification: expected={expected_type}, actual={token_type}, valid={is_valid}")
            return is_valid

        except Exception as e:
            logger.error(f"Error verifying token type: {e}")
            return False
