"""Pydantic schemas for authentication endpoints."""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    """User registration request model."""

    email: EmailStr
    password: str

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }


class UserLogin(BaseModel):
    """User login request model."""

    email: EmailStr
    password: str

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }


class UserResponse(BaseModel):
    """User response model (excludes password_hash)."""

    id: str
    email: str
    created_at: datetime

    @validator('id', pre=False)
    def convert_id_to_string(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class TokenResponse(BaseModel):
    """Token response model returned after login/refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until access token expiry

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class PasswordChange(BaseModel):
    """Password change request model."""

    old_password: str
    new_password: str

    class Config:
        schema_extra = {
            "example": {
                "old_password": "OldPass123!",
                "new_password": "NewPass456!"
            }
        }


class TokenRefresh(BaseModel):
    """Token refresh request model."""

    refresh_token: str

    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class PasswordChangeResponse(BaseModel):
    """Password change success response."""

    msg: str = "Password changed successfully"

    class Config:
        schema_extra = {
            "example": {
                "msg": "Password changed successfully"
            }
        }
