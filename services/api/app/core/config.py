from pydantic import BaseSettings, validator
from typing import List
import os

class Settings(BaseSettings):
    class Config:
        # Load from .env file in the project root
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")

    # Use absolute path for SQLite database
    _db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "autointern.db")
    database_url: str = f"sqlite+aiosqlite:///{_db_path}"  # Default to SQLite for local dev
    secret_key: str = "dev-secret-key-not-for-production"
    jwt_algorithm: str = "HS256"
    migrate_on_start: bool = False  # set to true in local dev to create tables on startup

    # MinIO/S3 Configuration
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket_name: str = "resumes"

    # Resume configuration
    max_resume_size_mb: int = 10

    # JWT Configuration
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Password Configuration
    min_password_length: int = 8
    require_special_chars: bool = True
    require_numbers: bool = True
    require_uppercase: bool = True
    require_lowercase: bool = True

    # CORS Configuration
    # In production, set CORS_ORIGINS env var to your Vercel URL:
    # e.g. CORS_ORIGINS=https://autointern.vercel.app
    cors_origins: str = "*"  # Comma-separated origins, or "*" for all
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    def get_cors_origins(self) -> List[str]:
        """Parse CORS_ORIGINS env var: comma-separated string or single '*'"""
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # Email Configuration (Phase 7)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = "noreply@autointern.com"
    sender_password: str = ""  # Set via environment variable

    # Redis Configuration (Phase 7)
    redis_url: str = "redis://localhost:6379/0"

    # Admin Configuration
    admin_api_key: str = ""  # Set via environment variable for admin access

    # AI Configuration (Gemini)
    gemini_api_key: str = ""  # Set GEMINI_API_KEY in .env — get one free at aistudio.google.com


    @validator('database_url', pre=True)
    def _strip_database_url(cls, v):
        return v.strip() if isinstance(v, str) else v

    @validator('redis_url', pre=True)
    def _strip_redis_url(cls, v):
        return v.strip() if isinstance(v, str) else v

    @validator('minio_endpoint', pre=True)
    def _strip_minio_endpoint(cls, v):
        return v.strip() if isinstance(v, str) else v


settings = Settings()
