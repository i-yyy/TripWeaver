"""用户画像服务。"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from sqlmodel import select

from ..db.database import session_scope
from ..db.models import User, UserProfile
from ..models.schemas import FeedbackCreateRequest, TripRequest, UserProfileData


class ProfileService:
    """维护并更新用户长期偏好画像。"""

    def _ensure_user(self, user_id: str) -> None:
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                user = User(id=user_id)
                session.add(user)
                session.commit()

    def get_or_create_profile(self, user_id: str) -> UserProfile:
        self._ensure_user(user_id)
        with session_scope() as session:
            statement = select(UserProfile).where(UserProfile.user_id == user_id)
            profile = session.exec(statement).first()
            if profile is None:
                profile = UserProfile(user_id=user_id)
                session.add(profile)
                session.commit()
                session.refresh(profile)
            return profile

    def get_profile_data(self, user_id: str) -> Optional[UserProfileData]:
        with session_scope() as session:
            statement = select(UserProfile).where(UserProfile.user_id == user_id)
            profile = session.exec(statement).first()
            if profile is None:
                return None
            return UserProfileData(
                user_id=profile.user_id,
                preferred_transportation=profile.preferred_transportation,
                preferred_accommodation=profile.preferred_accommodation,
                budget_level=profile.budget_level,
                pace_level=profile.pace_level,
                interest_weights=profile.interest_weights,
                dietary_restrictions=profile.dietary_restrictions,
                mobility_needs=profile.mobility_needs,
                avoid_tags=profile.avoid_tags,
                updated_at=profile.updated_at,
            )

    def update_profile_from_request(self, request: TripRequest) -> UserProfile:
        profile = self.get_or_create_profile(request.user_id)
        with session_scope() as session:
            db_profile = session.get(UserProfile, profile.id)
            if db_profile is None:
                db_profile = profile

            db_profile.preferred_transportation = request.transportation
            db_profile.preferred_accommodation = request.accommodation
            db_profile.budget_level = request.budget_level or db_profile.budget_level

            if request.dietary_restrictions:
                db_profile.dietary_restrictions = list(
                    sorted(set(db_profile.dietary_restrictions + request.dietary_restrictions))
                )

            if request.mobility_needs:
                db_profile.mobility_needs = list(sorted(set(db_profile.mobility_needs + request.mobility_needs)))

            weights = dict(db_profile.interest_weights or {})
            for tag in request.preferences + request.travel_style:
                if not tag:
                    continue
                weights[tag] = min(1.0, weights.get(tag, 0.0) + 0.1)
            db_profile.interest_weights = weights
            db_profile.updated_at = datetime.utcnow()

            session.add(db_profile)
            session.commit()
            session.refresh(db_profile)
            return db_profile

    def update_profile_from_feedback(self, payload: FeedbackCreateRequest) -> Optional[UserProfile]:
        with session_scope() as session:
            statement = select(UserProfile).where(UserProfile.user_id == payload.user_id)
            profile = session.exec(statement).first()
            if profile is None:
                return None

            tag = payload.target_name.strip()
            weights: Dict[str, float] = dict(profile.interest_weights or {})
            if tag:
                current = weights.get(tag, 0.5)
                if payload.feedback_type in {"like", "satisfied"}:
                    weights[tag] = min(1.0, current + 0.1)
                elif payload.feedback_type in {"dislike", "unsatisfied"}:
                    weights[tag] = max(0.0, current - 0.1)
            profile.interest_weights = weights

            if payload.feedback_type == "dislike" and tag:
                profile.avoid_tags = list(sorted(set(profile.avoid_tags + [tag])))

            profile.updated_at = datetime.utcnow()
            session.add(profile)
            session.commit()
            session.refresh(profile)
            return profile

    def build_profile_context(self, user_id: str) -> str:
        profile = self.get_profile_data(user_id)
        if profile is None:
            return ""

        top_interests = sorted(profile.interest_weights.items(), key=lambda kv: kv[1], reverse=True)[:6]
        interests_text = ", ".join([f"{name}:{score:.2f}" for name, score in top_interests]) or "无"
        dietary_text = ", ".join(profile.dietary_restrictions) or "无"
        mobility_text = ", ".join(profile.mobility_needs) or "无"
        avoid_text = ", ".join(profile.avoid_tags) or "无"

        return (
            "用户画像上下文:\n"
            f"- 交通偏好: {profile.preferred_transportation or '未知'}\n"
            f"- 住宿偏好: {profile.preferred_accommodation or '未知'}\n"
            f"- 预算等级: {profile.budget_level or '未知'}\n"
            f"- 兴趣权重: {interests_text}\n"
            f"- 饮食限制: {dietary_text}\n"
            f"- 行动需求: {mobility_text}\n"
            f"- 规避标签: {avoid_text}"
        )


_profile_service: Optional[ProfileService] = None


def get_profile_service() -> ProfileService:
    global _profile_service
    if _profile_service is None:
        _profile_service = ProfileService()
    return _profile_service
