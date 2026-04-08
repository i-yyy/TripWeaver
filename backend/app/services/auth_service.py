"""User registration, login and profile management."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import delete, select

from ..config import get_settings
from ..db.database import session_scope
from ..db.models import MemoryItem, TripHistory, User, UserFeedback, UserProfile
from ..models.auth_schemas import AuthUserData, UpdateProfileRequest
from .profile_service import get_profile_service


class AuthService:
    def __init__(self) -> None:
        self.settings = get_settings()

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
            session.delete(user)
            session.commit()

    @staticmethod
    def to_user_data(user: User) -> AuthUserData:
        auth_service = get_auth_service()
        return AuthUserData(
            id=user.id,
            email=user.email or "",
            nickname=user.nickname or "",
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
