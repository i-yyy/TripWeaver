"""SQLModel persistence models for user profile, memory and feedback."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import JSON, Column, String
from sqlmodel import Field, SQLModel


def _uuid() -> str:
    return str(uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    email: Optional[str] = Field(default=None, sa_column=Column(String(255), unique=True, index=True, nullable=True))
    password_hash: Optional[str] = Field(default=None, nullable=True)
    nickname: str = Field(default="", nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    last_login_at: Optional[datetime] = Field(default=None)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)


class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profiles"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    user_id: str = Field(index=True, nullable=False)
    preferred_transportation: Optional[str] = Field(default=None)
    preferred_accommodation: Optional[str] = Field(default=None)
    budget_level: Optional[str] = Field(default=None)
    pace_level: Optional[str] = Field(default=None)
    interest_weights: Dict[str, float] = Field(default_factory=dict, sa_column=Column(JSON))
    dietary_restrictions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    mobility_needs: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    avoid_tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)


class TripHistory(SQLModel, table=True):
    __tablename__ = "trip_histories"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    user_id: str = Field(index=True, nullable=False)
    session_id: str = Field(index=True, nullable=False)
    city: str = Field(index=True, nullable=False)
    start_date: str = Field(nullable=False)
    end_date: str = Field(nullable=False)
    trip_summary: str = Field(default="")
    selected_attractions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    plan_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    city_longitude: Optional[float] = Field(default=None)
    city_latitude: Optional[float] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)


class UserFeedback(SQLModel, table=True):
    __tablename__ = "user_feedbacks"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    user_id: str = Field(index=True, nullable=False)
    session_id: str = Field(index=True, nullable=False)
    target_type: str = Field(nullable=False, index=True)
    target_name: str = Field(nullable=False)
    feedback_type: str = Field(nullable=False, index=True)
    reason: str = Field(default="")
    feedback_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSON),
    )
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)


class MemoryItem(SQLModel, table=True):
    __tablename__ = "memory_items"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    user_id: str = Field(index=True, nullable=False)
    session_id: str = Field(index=True, nullable=False)
    memory_type: str = Field(nullable=False, index=True)
    content: str = Field(nullable=False)
    summary: str = Field(default="")
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    city: Optional[str] = Field(default=None, index=True)
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    expires_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
