"""Schemas for authentication and travel tracks."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class AuthUserData(BaseModel):
    id: str
    email: str
    nickname: str
    is_active: bool = True
    created_at: Optional[datetime] = None


class RegisterRequest(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=40)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class UpdateProfileRequest(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=40)
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=6, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)


class AuthUserResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[AuthUserData] = None


class LoginResponse(BaseModel):
    success: bool
    message: str = ""
    access_token: str = ""
    token_type: str = "bearer"
    data: Optional[AuthUserData] = None


class TravelTrackItem(BaseModel):
    id: str
    city: str
    start_date: str
    end_date: str
    searched_at: datetime
    trip_summary: str = ""
    city_longitude: Optional[float] = None
    city_latitude: Optional[float] = None


class TravelTracksResponse(BaseModel):
    success: bool
    message: str = ""
    data: List[TravelTrackItem] = Field(default_factory=list)


class OperationResponse(BaseModel):
    success: bool
    message: str = ""
