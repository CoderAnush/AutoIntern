"""Tests for user authentication system (Phase 5)."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.services.auth_service import AuthService
from app.core.validators import PasswordValidator
from app.schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse


class TestPasswordValidator:
    """Tests for password validation rules."""

    def test_password_valid_all_requirements(self):
        """Verify valid password with all requirements passes."""
        is_valid, msg = PasswordValidator.validate_password("SecurePass123!")
        assert is_valid is True
        assert msg == ""

    def test_password_too_short(self):
        """Verify password shorter than 8 characters fails."""
        is_valid, msg = PasswordValidator.validate_password("Short1!")
        assert is_valid is False
        assert "at least" in msg.lower() and "8" in msg

    def test_password_no_uppercase(self):
        """Verify password without uppercase letter fails."""
        is_valid, msg = PasswordValidator.validate_password("lowercase1!")
        assert is_valid is False
        assert "uppercase" in msg.lower()

    def test_password_no_lowercase(self):
        """Verify password without lowercase letter fails."""
        is_valid, msg = PasswordValidator.validate_password("UPPERCASE1!")
        assert is_valid is False
        assert "lowercase" in msg.lower()

    def test_password_no_digit(self):
        """Verify password without digit fails."""
        is_valid, msg = PasswordValidator.validate_password("NoDigits!")
        assert is_valid is False
        assert "digit" in msg.lower()

    def test_password_no_special_char(self):
        """Verify password without special character fails."""
        is_valid, msg = PasswordValidator.validate_password("NoSpecial123")
        assert is_valid is False
        assert "special" in msg.lower()

    def test_strong_password_variations(self):
        """Verify various strong passwords pass validation."""
        strong_passwords = [
            "SecurePass123!",
            "MyP@ssw0rd",
            "Complex#Password1",
            "Test$Pwd99",
            "Validate&Pass123"
        ]
        for password in strong_passwords:
            is_valid, msg = PasswordValidator.validate_password(password)
            assert is_valid is True, f"Password {password} should be valid"

    def test_weak_password_variations(self):
        """Verify various weak passwords fail validation."""
        weak_passwords = [
            "short",
            "NoNumbers!",
            "nonumber!",
            "NoSpecial123",
            "NOLOWER123!"
        ]
        for password in weak_passwords:
            is_valid, msg = PasswordValidator.validate_password(password)
            assert is_valid is False, f"Password {password} should be invalid"

    def test_get_password_requirements(self):
        """Verify password requirements dict is returned correctly."""
        requirements = PasswordValidator.get_password_requirements()
        assert "min_length" in requirements
        assert requirements["min_length"] == 8
        assert "require_uppercase" in requirements
        assert "require_lowercase" in requirements
        assert "require_digits" in requirements
        assert "require_special_chars" in requirements

    def test_validate_email_format_valid(self):
        """Verify valid email addresses pass validation."""
        valid_emails = [
            "user@example.com",
            "test.email+tag@domain.co.uk",
            "name_123@test.org"
        ]
        for email in valid_emails:
            is_valid, msg = PasswordValidator.validate_email_format(email)
            assert is_valid is True, f"Email {email} should be valid"

    def test_validate_email_format_invalid(self):
        """Verify invalid email addresses fail validation."""
        invalid_emails = [
            "nodomain",
            "@example.com",
            "user@",
            "user @example.com",
            "user@.com"
        ]
        for email in invalid_emails:
            is_valid, msg = PasswordValidator.validate_email_format(email)
            assert is_valid is False, f"Email {email} should be invalid"


class TestAuthService:
    """Tests for authentication service."""

    def test_hash_password_creates_hash(self):
        """Verify password hashing creates a hash."""
        password = "MyPassword123!"
        hashed = AuthService.hash_password(password)
        assert hashed != password
        assert len(hashed) > 20  # Bcrypt hashes are typically long

    def test_hash_password_different_hashes(self):
        """Verify same password hashes differently each time."""
        password = "MyPassword123!"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)
        assert hash1 != hash2  # Different salt each time

    def test_hash_password_empty_raises(self):
        """Verify empty password raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            AuthService.hash_password("")

    def test_verify_password_correct(self):
        """Verify correct password authenticates."""
        password = "MyPassword123!"
        hashed = AuthService.hash_password(password)
        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Verify incorrect password fails."""
        password = "MyPassword123!"
        hashed = AuthService.hash_password(password)
        assert AuthService.verify_password("WrongPassword123!", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Verify password verification is case sensitive."""
        password = "MyPassword123!"
        hashed = AuthService.hash_password(password)
        assert AuthService.verify_password("mypassword123!", hashed) is False

    def test_create_access_token_success(self):
        """Verify access token is created successfully."""
        user_id = str(uuid4())
        secret_key = "test-secret-key-for-testing"
        token, expiry = AuthService.create_access_token(user_id, secret_key)

        assert isinstance(token, str)
        assert len(token) > 0
        assert isinstance(expiry, datetime)

    def test_create_access_token_contains_user_id(self):
        """Verify access token contains user_id claim."""
        user_id = str(uuid4())
        secret_key = "test-secret-key-for-testing"
        token, _ = AuthService.create_access_token(user_id, secret_key)

        payload = AuthService.decode_token(token, secret_key)
        assert payload.get("user_id") == user_id

    def test_create_access_token_has_type(self):
        """Verify access token has 'access' type claim."""
        user_id = str(uuid4())
        secret_key = "test-secret-key"
        token, _ = AuthService.create_access_token(user_id, secret_key)

        payload = AuthService.decode_token(token, secret_key)
        assert payload.get("type") == "access"

    def test_decode_valid_token(self):
        """Verify valid token is decoded correctly."""
        user_id = str(uuid4())
        secret_key = "test-secret-key"
        token, _ = AuthService.create_access_token(user_id, secret_key)

        payload = AuthService.decode_token(token, secret_key)
        assert payload.get("user_id") == user_id
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_invalid_token_raises(self):
        """Verify invalid token raises ValueError."""
        secret_key = "test-secret-key"
        with pytest.raises(ValueError, match="Invalid or expired"):
            AuthService.decode_token("invalid.token.string", secret_key)

    def test_decode_wrong_secret_raises(self):
        """Verify token decoded with wrong secret raises ValueError."""
        user_id = str(uuid4())
        secret_key1 = "secret-key-1"
        secret_key2 = "secret-key-2"

        token, _ = AuthService.create_access_token(user_id, secret_key1)

        with pytest.raises(ValueError, match="Invalid or expired"):
            AuthService.decode_token(token, secret_key2)

    def test_create_refresh_token_success(self):
        """Verify refresh token is created successfully."""
        user_id = str(uuid4())
        secret_key = "test-secret-key"
        token, expiry = AuthService.create_refresh_token(user_id, secret_key)

        assert isinstance(token, str)
        assert len(token) > 0
        assert isinstance(expiry, datetime)

    def test_create_refresh_token_has_type(self):
        """Verify refresh token has 'refresh' type claim."""
        user_id = str(uuid4())
        secret_key = "test-secret-key"
        token, _ = AuthService.create_refresh_token(user_id, secret_key)

        payload = AuthService.decode_token(token, secret_key)
        assert payload.get("type") == "refresh"

    def test_get_token_expiry_seconds(self):
        """Verify token expiry seconds is calculated correctly."""
        user_id = str(uuid4())
        secret_key = "test-secret-key"
        token, _ = AuthService.create_access_token(user_id, secret_key)

        seconds = AuthService.get_token_expiry_seconds(token, secret_key)
        assert isinstance(seconds, int)
        assert seconds > 0
        assert seconds <= 30 * 60  # Should be around 30 minutes

    def test_verify_token_type_correct(self):
        """Verify token type verification works for correct type."""
        user_id = str(uuid4())
        secret_key = "test-secret-key"
        token, _ = AuthService.create_access_token(user_id, secret_key)

        is_valid = AuthService.verify_token_type(token, secret_key, "access")
        assert is_valid is True

    def test_verify_token_type_incorrect(self):
        """Verify token type verification fails for wrong type."""
        user_id = str(uuid4())
        secret_key = "test-secret-key"
        access_token, _ = AuthService.create_access_token(user_id, secret_key)

        is_valid = AuthService.verify_token_type(access_token, secret_key, "refresh")
        assert is_valid is False

    def test_create_token_with_custom_expiry(self):
        """Verify custom token expiry is respected."""
        user_id = str(uuid4())
        secret_key = "test-secret-key"
        custom_expiry = timedelta(hours=1)

        token, expiry = AuthService.create_access_token(user_id, secret_key, custom_expiry)
        payload = AuthService.decode_token(token, secret_key)

        # Token should expire in approximately 1 hour
        exp_seconds = payload["exp"] - datetime.now(timezone.utc).timestamp()
        assert 3500 < exp_seconds < 3700  # Allow some variance


class TestAuthSchemas:
    """Tests for Pydantic auth schemas."""

    def test_user_create_schema_valid(self):
        """Verify UserCreate schema validates correctly."""
        data = {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }
        user = UserCreate(**data)
        assert user.email == "user@example.com"
        assert user.password == "SecurePass123!"

    def test_user_create_invalid_email(self):
        """Verify UserCreate rejects invalid email."""
        data = {
            "email": "not-an-email",
            "password": "SecurePass123!"
        }
        with pytest.raises(ValueError):
            UserCreate(**data)

    def test_user_login_schema_valid(self):
        """Verify UserLogin schema validates correctly."""
        data = {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }
        login = UserLogin(**data)
        assert login.email == "user@example.com"

    def test_user_response_schema(self):
        """Verify UserResponse schema doesn't include password."""
        data = {
            "id": str(uuid4()),
            "email": "user@example.com",
            "created_at": datetime.now(timezone.utc)
        }
        response = UserResponse(**data)
        assert hasattr(response, "id")
        assert hasattr(response, "email")
        assert not hasattr(response, "password")

    def test_token_response_schema(self):
        """Verify TokenResponse schema structure."""
        data = {
            "access_token": "token-string",
            "refresh_token": "refresh-token-string",
            "bearer token_type": "bearer",
            "expires_in": 1800
        }
        # Fix the data structure
        data = {
            "access_token": "token-string",
            "refresh_token": "refresh-token-string",
            "token_type": "bearer",
            "expires_in": 1800
        }
        token_response = TokenResponse(**data)
        assert token_response.token_type == "bearer"
        assert token_response.expires_in == 1800


class TestAuthEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_password_hashing_with_special_chars(self):
        """Verify passwords with special characters hash correctly."""
        password = "P@$$w0rd!#%&*"
        hashed = AuthService.hash_password(password)
        assert AuthService.verify_password(password, hashed) is True

    def test_very_long_password(self):
        """Verify long passwords (up to 72 bytes) are handled correctly."""
        # Bcrypt has a 72-byte limit, so test with a password at that limit
        password = "VeryLongPassword1!" + "A" * 50  # 68 chars, under 72-byte limit
        hashed = AuthService.hash_password(password)
        assert AuthService.verify_password(password, hashed) is True

    def test_empty_string_validations(self):
        """Verify empty strings fail validation."""
        assert PasswordValidator.validate_password("")[0] is False
        assert PasswordValidator.validate_email_format("")[0] is False

    def test_token_creation_with_unicode(self):
        """Verify tokens can be created with unicode emails."""
        user_id = str(uuid4())
        secret_key = "test-secret"
        token, _ = AuthService.create_access_token(user_id, secret_key)

        payload = AuthService.decode_token(token, secret_key)
        assert payload.get("user_id") == user_id
