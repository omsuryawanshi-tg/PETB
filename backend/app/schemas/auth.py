"""
Pydantic schemas for authentication: signup, login, user profile, and JWT tokens.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")
    full_name: str = Field(..., min_length=1, max_length=150, description="Full name")
    age: Optional[int] = Field(default=None, ge=1, le=120, description="Age in years")
    gender: Optional[str] = Field(default=None, description="Gender")
    preferred_language: str = Field(default="en", description="Preferred language (en/hi)")


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Registered email")
    password: str = Field(..., description="Account password")


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    role: str
    preferred_language: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer")
    user: UserOut
