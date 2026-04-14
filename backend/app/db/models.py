"""SQLModel persistence models for user profile, memory and feedback."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import JSON, Column, String
from sqlmodel import Field, SQLModel


def _uuid() -> str:
    return str(uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    email: Optional[str] = Field(default=None, sa_column=Column(String(255), unique=True, index=True, nullable=True))
    password_hash: Optional[str] = Field(default=None, nullable=True)
    nickname: str = Field(default="", nullable=False)
    avatar_url: str = Field(default="", nullable=False)
    gender: str = Field(default="", nullable=False)
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


class CommunityInteraction(SQLModel, table=True):
    __tablename__ = "community_interactions"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    user_id: str = Field(index=True, nullable=False)
    card_id: str = Field(index=True, nullable=False)
    interaction_type: str = Field(index=True, nullable=False)
    active: bool = Field(default=True, nullable=False)
    interaction_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)


class CommunityComment(SQLModel, table=True):
    __tablename__ = "community_comments"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    user_id: str = Field(index=True, nullable=False)
    card_id: str = Field(index=True, nullable=False)
    author_name: str = Field(default="旅行者", nullable=False)
    content: str = Field(nullable=False)
    status: str = Field(default="published", index=True, nullable=False)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)


class CommunityTripCardRecord(SQLModel, table=True):
    __tablename__ = "community_trip_cards"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    source_type: str = Field(default="curated", index=True, nullable=False)
    source_ref_id: str = Field(default="", index=True, nullable=False)
    author_user_id: str = Field(default="", index=True, nullable=False)
    author_name: str = Field(default="旅行者", nullable=False)
    city: str = Field(default="", index=True, nullable=False)
    title: str = Field(nullable=False)
    subtitle: str = Field(default="", nullable=False)
    summary: str = Field(default="", nullable=False)
    cover_image_url: str = Field(default="", nullable=False)
    days: int = Field(default=2, nullable=False)
    estimated_budget: str = Field(default="medium", index=True, nullable=False)
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    travel_style: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    companions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    highlights: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    like_count: int = Field(default=0, nullable=False)
    favorite_count: int = Field(default=0, nullable=False)
    comment_count: int = Field(default=0, nullable=False)
    reuse_count: int = Field(default=0, nullable=False)
    status: str = Field(default="published", index=True, nullable=False)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)


class CommunityPost(SQLModel, table=True):
    __tablename__ = "community_posts"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    user_id: str = Field(index=True, nullable=False)
    author_name: str = Field(default="旅行者", nullable=False)
    content: str = Field(nullable=False)
    image_urls: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    city: str = Field(default="", index=True, nullable=False)
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    linked_track_id: str = Field(default="", index=True, nullable=False)
    linked_track_title: str = Field(default="", nullable=False)
    like_count: int = Field(default=0, nullable=False)
    comment_count: int = Field(default=0, nullable=False)
    status: str = Field(default="published", index=True, nullable=False)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)


class CommunityPostLike(SQLModel, table=True):
    __tablename__ = "community_post_likes"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    post_id: str = Field(index=True, nullable=False)
    user_id: str = Field(index=True, nullable=False)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)


class CommunityPostComment(SQLModel, table=True):
    __tablename__ = "community_post_comments"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    post_id: str = Field(index=True, nullable=False)
    user_id: str = Field(index=True, nullable=False)
    author_name: str = Field(default="旅行者", nullable=False)
    content: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)


class CommunityFollow(SQLModel, table=True):
    __tablename__ = "community_follows"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    follower_user_id: str = Field(index=True, nullable=False)
    followed_user_id: str = Field(index=True, nullable=False)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)


class CollabTrip(SQLModel, table=True):
    __tablename__ = "collab_trips"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    owner_user_id: str = Field(index=True, nullable=False)
    source_track_id: str = Field(default="", index=True, nullable=False)
    title: str = Field(nullable=False)
    city: str = Field(default="", index=True, nullable=False)
    start_date: str = Field(default="", nullable=False)
    end_date: str = Field(default="", nullable=False)
    plan_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    status: str = Field(default="draft", index=True, nullable=False)
    version: int = Field(default=1, nullable=False)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)


class CollabTripMember(SQLModel, table=True):
    __tablename__ = "collab_trip_members"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    trip_id: str = Field(index=True, nullable=False)
    user_id: str = Field(index=True, nullable=False)
    role: str = Field(default="viewer", index=True, nullable=False)
    status: str = Field(default="active", index=True, nullable=False)
    joined_at: datetime = Field(default_factory=_utcnow, nullable=False)


class CollabTripInvite(SQLModel, table=True):
    __tablename__ = "collab_trip_invites"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    trip_id: str = Field(index=True, nullable=False)
    inviter_user_id: str = Field(index=True, nullable=False)
    invitee_user_id: str = Field(default="", index=True, nullable=False)
    invitee_email: str = Field(default="", index=True, nullable=False)
    role: str = Field(default="editor", nullable=False)
    status: str = Field(default="pending", index=True, nullable=False)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    responded_at: Optional[datetime] = Field(default=None)


class CollabTripChange(SQLModel, table=True):
    __tablename__ = "collab_trip_changes"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    trip_id: str = Field(index=True, nullable=False)
    user_id: str = Field(index=True, nullable=False)
    change_type: str = Field(default="update", index=True, nullable=False)
    summary: str = Field(default="", nullable=False)
    before_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    after_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)


class CollabTripComment(SQLModel, table=True):
    __tablename__ = "collab_trip_comments"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    trip_id: str = Field(index=True, nullable=False)
    day_index: Optional[int] = Field(default=None, index=True)
    user_id: str = Field(index=True, nullable=False)
    content: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)


class CollabTripVote(SQLModel, table=True):
    __tablename__ = "collab_trip_votes"

    id: str = Field(default_factory=_uuid, primary_key=True, index=True)
    trip_id: str = Field(index=True, nullable=False)
    target_type: str = Field(default="attraction", index=True, nullable=False)
    target_id: str = Field(index=True, nullable=False)
    user_id: str = Field(index=True, nullable=False)
    vote_type: str = Field(default="want", index=True, nullable=False)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
