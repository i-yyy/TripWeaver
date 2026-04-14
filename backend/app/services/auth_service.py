"""User registration, login and profile management."""

from __future__ import annotations

from datetime import datetime, timezone
import imghdr
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import UploadFile
from sqlmodel import delete, select

from ..config import get_settings
from ..db.database import session_scope
from ..db.models import (
    CollabTrip,
    CollabTripChange,
    CollabTripComment,
    CollabTripInvite,
    CollabTripMember,
    CollabTripVote,
    MemoryItem,
    TripHistory,
    User,
    UserFeedback,
    UserProfile,
)
from ..models.auth_schemas import AuthUserData, UpdateProfileRequest
from .profile_service import get_profile_service


class AuthService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.avatar_upload_dir = Path(self.settings.upload_dir) / "avatars"
        self.avatar_upload_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(timezone.utc)

    def is_developer_email(self, email: str | None) -> bool:
        normalized_email = (email or "").strip().lower()
        if not normalized_email:
            return False
        return normalized_email in self.settings.get_developer_email_whitelist_list()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        with session_scope() as session:
            return session.get(User, user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        normalized = email.strip().lower()
        with session_scope() as session:
            statement = select(User).where(User.email == normalized)
            return session.exec(statement).first()

    def register_user(self, nickname: str, email: str, password_hash: str) -> User:
        normalized_email = email.strip().lower()
        if self.get_user_by_email(normalized_email) is not None:
            raise ValueError("Email is already registered")

        user = User(
            email=normalized_email,
            password_hash=password_hash,
            nickname=nickname.strip(),
            is_active=True,
            updated_at=self._utcnow(),
        )
        with session_scope() as session:
            session.add(user)
            session.commit()
            session.refresh(user)

        get_profile_service().get_or_create_profile(user.id)
        return user

    def update_login_time(self, user_id: str) -> Optional[User]:
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                return None
            user.last_login_at = self._utcnow()
            user.updated_at = self._utcnow()
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def update_profile(self, user_id: str, payload: UpdateProfileRequest) -> User:
        normalized_email = payload.email.strip().lower()
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                raise ValueError("User not found")

            existing = session.exec(select(User).where(User.email == normalized_email)).first()
            if existing is not None and existing.id != user_id:
                raise ValueError("Email is already registered")

            user.nickname = payload.nickname.strip()
            user.email = normalized_email
            user.gender = payload.gender.strip()[:20]
            user.updated_at = self._utcnow()
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def update_avatar(self, user_id: str, file: UploadFile) -> User:
        content_type = (file.content_type or "").lower()
        if not content_type.startswith("image/"):
            raise ValueError("Only image files are supported")

        data = file.file.read()
        if not data:
            raise ValueError("Avatar file is empty")
        if len(data) > 5 * 1024 * 1024:
            raise ValueError("Avatar file is too large")

        detected_type = imghdr.what(None, data)
        extension_map = {
            "jpeg": ".jpg",
            "png": ".png",
            "gif": ".gif",
            "webp": ".webp",
            "bmp": ".bmp",
        }
        extension = extension_map.get(str(detected_type or "").lower())
        if extension is None:
            raise ValueError("Unsupported avatar format")

        filename = f"{uuid4().hex}{extension}"
        target_path = self.avatar_upload_dir / filename
        target_path.write_bytes(data)
        avatar_url = f"/uploads/avatars/{filename}"

        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                raise ValueError("User not found")
            user.avatar_url = avatar_url
            user.updated_at = self._utcnow()
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def update_password(self, user_id: str, password_hash: str) -> User:
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                raise ValueError("User not found")
            user.password_hash = password_hash
            user.updated_at = self._utcnow()
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def delete_account(self, user_id: str) -> None:
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                raise ValueError("User not found")

            session.exec(delete(UserProfile).where(UserProfile.user_id == user_id))
            session.exec(delete(TripHistory).where(TripHistory.user_id == user_id))
            session.exec(delete(UserFeedback).where(UserFeedback.user_id == user_id))
            session.exec(delete(MemoryItem).where(MemoryItem.user_id == user_id))
            session.exec(delete(CollabTripVote).where(CollabTripVote.user_id == user_id))
            session.exec(delete(CollabTripComment).where(CollabTripComment.user_id == user_id))
            session.exec(delete(CollabTripChange).where(CollabTripChange.user_id == user_id))
            session.exec(delete(CollabTripInvite).where(CollabTripInvite.inviter_user_id == user_id))
            session.exec(delete(CollabTripInvite).where(CollabTripInvite.invitee_user_id == user_id))
            session.exec(delete(CollabTripMember).where(CollabTripMember.user_id == user_id))
            owned_trips = session.exec(select(CollabTrip).where(CollabTrip.owner_user_id == user_id)).all()
            for trip in owned_trips:
                session.exec(delete(CollabTripVote).where(CollabTripVote.trip_id == trip.id))
                session.exec(delete(CollabTripComment).where(CollabTripComment.trip_id == trip.id))
                session.exec(delete(CollabTripChange).where(CollabTripChange.trip_id == trip.id))
                session.exec(delete(CollabTripInvite).where(CollabTripInvite.trip_id == trip.id))
                session.exec(delete(CollabTripMember).where(CollabTripMember.trip_id == trip.id))
                session.delete(trip)
            session.delete(user)
            session.commit()

    @staticmethod
    def to_user_data(user: User) -> AuthUserData:
        auth_service = get_auth_service()
        return AuthUserData(
            id=user.id,
            email=user.email or "",
            nickname=user.nickname or "",
            avatar_url=user.avatar_url or "",
            gender=user.gender or "",
            is_active=bool(user.is_active),
            is_developer=auth_service.is_developer_email(user.email),
            created_at=user.created_at,
        )


_auth_service: AuthService | None = None


def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
