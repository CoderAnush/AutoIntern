from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from .base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Email notification preferences (Phase 7)
    notify_on_new_jobs = Column(Boolean, default=True, nullable=False)
    notify_on_resume_upload = Column(Boolean, default=True, nullable=False)
    notify_on_password_change = Column(Boolean, default=True, nullable=False)
    weekly_digest = Column(Boolean, default=True, nullable=False)
    email_frequency = Column(String(50), default="weekly", nullable=False)  # daily, weekly, never

    # Account lockout tracking (Phase 8)
    failed_login_attempts = Column(Integer, default=0, nullable=False)  # Counter for failed login attempts
    locked_until = Column(DateTime(timezone=True), nullable=True)  # NULL = not locked
    last_login_attempt = Column(DateTime(timezone=True), nullable=True)  # Timestamp of last login attempt

class Company(Base):
    __tablename__ = "companies"
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255))
    career_page = Column(String(512))

class Job(Base):
    __tablename__ = "jobs"
    id = Column(UUID(as_uuid=True), primary_key=True)
    source = Column(String(64))
    external_id = Column(String(255), index=True)
    title = Column(String(512))
    description = Column(Text)
    location = Column(String(255))
    posted_at = Column(DateTime)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    raw = Column(JSONB)
    dedupe_signature = Column(String(255), index=True, nullable=True)

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    file_name = Column(String(255), nullable=True)
    parsed_text = Column(Text)
    skills = Column(JSONB)
    storage_url = Column(String(512))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(UUID(as_uuid=True), primary_key=True)
    parent_type = Column(String(64))
    parent_id = Column(UUID(as_uuid=True))
    model_name = Column(String(128))
    vector = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EmailLog(Base):
    """Email sending logs and audit trail (Phase 7)."""
    __tablename__ = "email_logs"
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    email_type = Column(String(50), nullable=False)  # welcome, upload, alert, password_change
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, sent, failed
    error_message = Column(Text, nullable=True)
    retries = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class RequestLog(Base):
    """Request logging and audit trail (Phase 8)."""
    __tablename__ = "request_logs"
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)  # NULL for unauthenticated
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE, PATCH
    path = Column(String(512), nullable=False)  # /users/login, /resumes, /recommendations/jobs-for-resume/{id}
    status_code = Column(Integer, nullable=False, index=True)  # HTTP status (200, 401, 500, etc)
    response_time_ms = Column(Integer, nullable=False)  # Response time in milliseconds
    ip_address = Column(String(45), nullable=False)  # IPv4 or IPv6 address
    user_agent = Column(String(512), nullable=True)  # Client user agent string
    request_body_hash = Column(String(64), nullable=True)  # SHA256 hash (don't store actual body with passwords)
    error_message = Column(Text, nullable=True)  # Error details if status >= 400
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

