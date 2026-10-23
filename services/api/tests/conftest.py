"""
Global pytest configuration.

Sets environment variables BEFORE any app module is imported, so that:
- settings.database_url uses SQLite (no psycopg2 needed in tests)
- UUIDType maps to String(36) (SQLite-compatible)
- Secret key is available for JWT signing
- SMTP config is empty (no real emails sent)
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-chars-long!")
os.environ.setdefault("SMTP_HOST", "")
os.environ.setdefault("SMTP_USER", "")
os.environ.setdefault("SMTP_PASS", "")
os.environ.setdefault("REDIS_URL", "")
