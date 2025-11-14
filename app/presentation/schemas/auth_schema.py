"""Authentication request/response schemas."""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class RegisterRequest(BaseModel):
    """Register user request."""
    
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=1, max_length=255)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
                "full_name": "John Doe"
            }
        }
    }


class LoginRequest(BaseModel):
    """Login request."""
    
    email: EmailStr
    password: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }
    }


class UserResponse(BaseModel):
    """User response (without sensitive data)."""
    
    id: str
    email: str
    full_name: str
    avatar_url: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: datetime | None
    
    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """Login response with token."""
    
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
