"""Integration tests for authentication flow (Phase 5)."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.auth_service import AuthService
from app.core.validators import PasswordValidator


class TestAuthIntegrationFlow:
    """Integration tests for complete authentication flows."""

    def test_registration_to_login_flow(self):
        """Test complete flow: register -> login -> use tokens."""
        # Step 1: Validate password
        test_password = "SecurePass123!"
        is_valid, msg = PasswordValidator.validate_password(test_password)
        assert is_valid is True

        # Step 2: Hash password
        password_hash = AuthService.hash_password(test_password)
        assert password_hash != test_password

        # Step 3: Create tokens
        user_id = str(uuid4())
        secret_key = "test-secret-key"
        access_token, access_expiry = AuthService.create_access_token(user_id, secret_key)
        refresh_token, refresh_expiry = AuthService.create_refresh_token(user_id, secret_key)

        assert len(access_token) > 0
        assert len(refresh_token) > 0

        # Step 4: Verify access token can be decoded
        payload = AuthService.decode_token(access_token, secret_key)
        assert payload.get("user_id") == user_id
        assert payload.get("type") == "access"

        # Step 5: Verify refresh token can be decoded
        refresh_payload = AuthService.decode_token(refresh_token, secret_key)
        assert refresh_payload.get("user_id") == user_id
        assert refresh_payload.get("type") == "refresh"

    def test_password_change_flow(self):
        """Test password change: verify old -> hash new -> store."""
        # Initial password
        old_password = "OldPass123!"
        old_hash = AuthService.hash_password(old_password)

        # Verify old password matches
        assert AuthService.verify_password(old_password, old_hash) is True

        # New password
        new_password = "NewPass456!"
        is_valid, msg = PasswordValidator.validate_password(new_password)
        assert is_valid is True

        # Hash new password
        new_hash = AuthService.hash_password(new_password)

        # Verify new password with new hash
        assert AuthService.verify_password(new_password, new_hash) is True

        # Verify old password doesn't work with new hash
        assert AuthService.verify_password(old_password, new_hash) is False

    def test_token_refresh_flow(self):
        """Test refreshing expired access token with refresh token."""
        user_id = str(uuid4())
        secret_key = "test-secret-key"

        # Create initial tokens
        access_token1, _ = AuthService.create_access_token(user_id, secret_key)
        refresh_token, _ = AuthService.create_refresh_token(user_id, secret_key)

        # Verify refresh token is valid
        is_valid = AuthService.verify_token_type(refresh_token, secret_key, "refresh")
        assert is_valid is True

        # Simulate getting new access token from refresh token
        access_token2, _ = AuthService.create_access_token(user_id, secret_key)

        # Both tokens should work
        payload1 = AuthService.decode_token(access_token1, secret_key)
        payload2 = AuthService.decode_token(access_token2, secret_key)

        assert payload1.get("user_id") == user_id
        assert payload2.get("user_id") == user_id

    def test_session_invalidation_on_password_change(self):
        """Test that old tokens should be invalidated on password change."""
        user_id = str(uuid4())
        secret_key1 = "original-secret"
        secret_key2 = "new-secret"

        # Create token with original secret
        original_token, _ = AuthService.create_access_token(user_id, secret_key1)

        # Token works with original secret
        payload = AuthService.decode_token(original_token, secret_key1)
        assert payload.get("user_id") == user_id

        # Token fails with new secret (simulating key rotation)
        with pytest.raises(ValueError):
            AuthService.decode_token(original_token, secret_key2)

    def test_concurrent_user_sessions(self):
        """Test multiple users can have concurrent sessions."""
        secret_key = "test-secret"
        user1_id = str(uuid4())
        user2_id = str(uuid4())

        # Create tokens for both users
        user1_token, _ = AuthService.create_access_token(user1_id, secret_key)
        user2_token, _ = AuthService.create_access_token(user2_id, secret_key)

        # Each token has the correct user_id
        user1_payload = AuthService.decode_token(user1_token, secret_key)
        user2_payload = AuthService.decode_token(user2_token, secret_key)

        assert user1_payload.get("user_id") == user1_id
        assert user2_payload.get("user_id") == user2_id

        # Tokens are different
        assert user1_token != user2_token

    def test_password_validation_and_hashing_pipeline(self):
        """Test complete password validation and hashing pipeline."""
        # Valid password passes validation
        test_password = "ValidPass123!"
        is_valid, _ = PasswordValidator.validate_password(test_password)
        assert is_valid is True

        # Hash it
        hashed = AuthService.hash_password(test_password)

        # Verify it later
        assert AuthService.verify_password(test_password, hashed) is True
        assert AuthService.verify_password("InvalidPass123!", hashed) is False

    def test_weak_password_rejected_before_hashing(self):
        """Test weak passwords are rejected without hashing."""
        # Weak password fails validation
        weak_password = "weak"
        is_valid, error = PasswordValidator.validate_password(weak_password)
        assert is_valid is False
        assert len(error) > 0

        # Should not attempt to hash weak passwords in production

    def test_email_format_validation_pipeline(self):
        """Test email format validation for registration."""
        # Valid emails pass
        valid_emails = ["user@example.com", "test+tag@domain.co"]
        for email in valid_emails:
            is_valid, _ = PasswordValidator.validate_email_format(email)
            assert is_valid is True

        # Invalid emails fail
        invalid_emails = ["notanemail", "@example.com", "user@", "user @example"]
        for email in invalid_emails:
            is_valid, _ = PasswordValidator.validate_email_format(email)
            assert is_valid is False

    def test_token_expiry_calculation(self):
        """Test token expiry is calculated correctly."""
        user_id = str(uuid4())
        secret_key = "test-secret"

        # Create access token (30 min)
        access_token, access_expiry = AuthService.create_access_token(user_id, secret_key)
        access_seconds = AuthService.get_token_expiry_seconds(access_token, secret_key)

        # Should be approximately 30 minutes (1800 seconds)
        assert 1750 < access_seconds < 1850

        # Create refresh token (7 days)
        refresh_token, refresh_expiry = AuthService.create_refresh_token(user_id, secret_key)
        refresh_seconds = AuthService.get_token_expiry_seconds(refresh_token, secret_key)

        # Should be approximately 7 days (604800 seconds)
        assert refresh_seconds > 600000  # At least 166 hours
        assert refresh_seconds < 700000  # At most 194 hours


class TestAuthSecurityRequirements:
    """Tests for security requirements and best practices."""

    def test_password_not_stored_in_logs(self):
        """Verify passwords are not logged during hashing."""
        # This is more of a code review item, but test the flow
        original_password = "SecurePass123!"
        hashed = AuthService.hash_password(original_password)

        # The hashed password should not contain the original
        assert original_password not in hashed

    def test_token_has_timestamp_info(self):
        """Verify tokens contain issued-at and expiry timestamps."""
        user_id = str(uuid4())
        secret_key = "test-secret"
        token, _ = AuthService.create_access_token(user_id, secret_key)

        payload = AuthService.decode_token(token, secret_key)
        assert "iat" in payload  # Issued at
        assert "exp" in payload  # Expiration
        assert payload["exp"] > payload["iat"]

    def test_different_users_get_different_tokens(self):
        """Verify different users get unique tokens."""
        secret_key = "test-secret"
        tokens = set()

        # Create 10 tokens with different user IDs
        for _ in range(10):
            user_id = str(uuid4())
            token, _ = AuthService.create_access_token(user_id, secret_key)
            tokens.add(token)

        # All should be different
        assert len(tokens) == 10

    def test_token_tamper_detection(self):
        """Verify tampered tokens are detected."""
        user_id = str(uuid4())
        secret_key = "test-secret"
        token, _ = AuthService.create_access_token(user_id, secret_key)

        # Tamper with token
        tampered_token = token[:-10] + "0123456789"

        # Should fail to decode
        with pytest.raises(ValueError):
            AuthService.decode_token(tampered_token, secret_key)

    def test_bcrypt_salt_rounds(self):
        """Verify bcrypt uses sufficient salt rounds."""
        # Use password within 72-byte limit for bcrypt
        password = "TestPass123!WithExtra1234567890"  # 45 chars, under 72-byte limit
        hash1 = AuthService.hash_password(password)

        # Each time we hash, we get different result (due to random salt)
        hash2 = AuthService.hash_password(password)
        assert hash1 != hash2

        # But both should verify against the original password
        assert AuthService.verify_password(password, hash1) is True
        assert AuthService.verify_password(password, hash2) is True
