from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from .base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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
    parsed_text = Column(Text)
    skills = Column(JSONB)
    storage_url = Column(String(512))

class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(UUID(as_uuid=True), primary_key=True)
    parent_type = Column(String(64))
    parent_id = Column(UUID(as_uuid=True))
    model_name = Column(String(128))
    vector = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
