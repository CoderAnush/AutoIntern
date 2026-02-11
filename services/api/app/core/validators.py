"""Password validation rules and utilities."""

import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)

# Password validation configuration
MIN_PASSWORD_LENGTH = 8
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_DIGITS = True
REQUIRE_SPECIAL_CHARS = True

# Special characters allowed in passwords
ALLOWED_SPECIAL_CHARS = set("!@#$%^&*()_+-=[]{}|;:,.<>?")


class PasswordValidator:
    """Validates password strength and complexity requirements."""

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        Validate password against strength requirements.

        Requirements:
        - Minimum 8 characters
        - At least 1 uppercase letter (A-Z)
        - At least 1 lowercase letter (a-z)
        - At least 1 digit (0-9)
        - At least 1 special character (!@#$%^&*)

        Args:
            password: Password string to validate

        Returns:
            Tuple of (is_valid: bool, error_message: str)
            - (True, ""): Password meets all requirements
            - (False, "error message"): Password fails validation with specific reason
        """
        if not password:
            return False, "Password cannot be empty"

        # Check length
        if len(password) < MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long (provided: {len(password)})"

        # Check for uppercase
        if REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter (A-Z)"

        # Check for lowercase
        if REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter (a-z)"

        # Check for digits
        if REQUIRE_DIGITS and not re.search(r"\d", password):
            return False, "Password must contain at least one digit (0-9)"

        # Check for special characters
        if REQUIRE_SPECIAL_CHARS:
            has_special = any(c in ALLOWED_SPECIAL_CHARS for c in password)
            if not has_special:
                special_chars_str = "".join(sorted(ALLOWED_SPECIAL_CHARS))
                return False, f"Password must contain at least one special character ({special_chars_str})"

        logger.debug("Password validation successful")
        return True, ""

    @staticmethod
    def get_password_requirements() -> dict:
        """
        Get current password requirements for API documentation.

        Returns:
            Dictionary with password policy details
        """
        return {
            "min_length": MIN_PASSWORD_LENGTH,
            "require_uppercase": REQUIRE_UPPERCASE,
            "require_lowercase": REQUIRE_LOWERCASE,
            "require_digits": REQUIRE_DIGITS,
            "require_special_chars": REQUIRE_SPECIAL_CHARS,
            "allowed_special_chars": "".join(sorted(ALLOWED_SPECIAL_CHARS)),
            "description": f"Minimum {MIN_PASSWORD_LENGTH} characters with uppercase, lowercase, digit, and special character"
        }

    @staticmethod
    def validate_email_format(email: str) -> Tuple[bool, str]:
        """
        Validate email format using regex pattern.

        Args:
            email: Email string to validate

        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not email:
            return False, "Email cannot be empty"

        # Basic email validation pattern
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(email_pattern, email):
            return False, "Invalid email format"

        # Additional length check
        if len(email) > 255:
            return False, "Email must be less than 255 characters"

        logger.debug(f"Email validation successful for: {email}")
        return True, ""

    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Validate username format (future use).

        Args:
            username: Username string to validate

        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not username:
            return False, "Username cannot be empty"

        # Username should be 3-30 characters, alphanumeric with underscores/hyphens
        if len(username) < 3 or len(username) > 30:
            return False, "Username must be between 3 and 30 characters"

        # Allow alphanumeric, underscore, hyphen
        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            return False, "Username can only contain letters, numbers, underscores, and hyphens"

        logger.debug(f"Username validation successful for: {username}")
        return True, ""
