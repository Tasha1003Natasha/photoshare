"""PhotoShare schemas: user."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from src.entity.models import Role


class UserSchema(BaseModel):
    """Validated UserSchema data contract for API requests or responses."""
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=8)


class UserResponse(BaseModel):
    """Validated UserResponse data contract for API requests or responses."""
    id: int = 1
    username: str
    email: EmailStr
    avatar: str
    role: Role

    class Config:
        from_attributes = True


class TokenSchema(BaseModel):
    """Validated TokenSchema data contract for API requests or responses."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    """Validated RequestEmail data contract for API requests or responses."""
    email: EmailStr


class UserRoleUpdate(BaseModel):
    """Validated UserRoleUpdate data contract for API requests or responses."""
    email: EmailStr
    role: Role


class UserRoleResponse(BaseModel):
    """Validated UserRoleResponse data contract for API requests or responses."""
    id: int
    email: EmailStr
    role: Role


class ResetPassword(BaseModel):
    """Validated ResetPassword data contract for API requests or responses."""
    token: str
    password: str = Field(min_length=6, max_length=8)
