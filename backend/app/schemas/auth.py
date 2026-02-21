"""Authentication-related schemas."""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request payload."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    """Registration request payload."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UpdateEmailRequest(BaseModel):
    """Update email request."""

    email: EmailStr


class ChangePasswordRequest(BaseModel):
    """Change password request."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


class UserResponse(BaseModel):
    """User information response."""

    id: int
    username: str
    email: Optional[str] = None
    is_admin: bool
    is_active: bool
    membership_tier: str

    class Config:
        from_attributes = True
