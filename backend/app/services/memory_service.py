"""记忆服务：管理短期与长期旅行记忆。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from sqlmodel import select

from ..db.database import session_scope
from ..db.models import MemoryItem, TripHistory
from ..models.schemas import FeedbackCreateRequest, MemoryFact, TripPlan, TripRequest
from .amap_service import get_amap_service


class MemoryService:
    """基于 SQLModel 的轻量记忆实现。"""

    def save_session_facts(self, request: TripRequest) -> None:
        content = (
            f"会话请求: 城市={request.city}, 天数={request.travel_days}, "
            f"交通={request.transportation}, 住宿={request.accommodation}, "
            f"偏好={','.join(request.preferences)}"
        )
        summary = f"{request.city} {request.travel_days} 天旅行规划意图"
        tags = list(sorted(set(request.preferences + request.travel_style + request.companions)))

        memory = MemoryItem(
            user_id=request.user_id,
            session_id=request.session_id,
            memory_type="session",
            content=content,
            summary=summary,
            importance_score=0.6,
            city=request.city,
            tags=tags,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        with session_scope() as session:
            session.add(memory)
            session.commit()

    def get_relevant_memories(self, user_id: str, session_id: str, city: str, top_k: int = 8) -> List[MemoryFact]:
        with session_scope() as session:
            statement = (
                select(MemoryItem)
                .where(MemoryItem.user_id == user_id)
                .where((MemoryItem.city == city) | (MemoryItem.city.is_(None)))
                .order_by(MemoryItem.importance_score.desc(), MemoryItem.created_at.desc())
                .limit(top_k)
            )
            items = session.exec(statement).all()

        return [
            MemoryFact(
                memory_type=item.memory_type,
                content=item.content,
                summary=item.summary,
                importance_score=item.importance_score,
                city=item.city,
                tags=item.tags,
            )
            for item in items
            if item.session_id == session_id or item.memory_type != "session"
        ]

    def save_trip_summary(self, request: TripRequest, plan: TripPlan) -> None:
        attractions = []
        for day in plan.days:
            for attraction in day.attractions:
                attractions.append(attraction.name)

        summary = (
            f"{plan.city} 行程 {plan.start_date} 到 {plan.end_date}，"
            f"共 {len(plan.days)} 天，包含 {len(attractions)} 个景点"
        )

        city_longitude = None
        city_latitude = None
        try:
            city_location = get_amap_service().geocode_city_http(request.city)
            if city_location is not None:
                city_longitude = city_location.longitude
                city_latitude = city_location.latitude
        except Exception as exc:  # pragma: no cover - external dependency
            print(f"Trip history geocode failed: {exc}")

        trip_history = TripHistory(
            user_id=request.user_id,
            session_id=request.session_id,
            city=request.city,
            start_date=request.start_date,
            end_date=request.end_date,
            trip_summary=summary,
            selected_attractions=attractions,
            plan_json=plan.model_dump(),
            city_longitude=city_longitude,
            city_latitude=city_latitude,
        )

        episodic_memory = MemoryItem(
            user_id=request.user_id,
            session_id=request.session_id,
            memory_type="episodic",
            content=summary,
            summary=summary,
            importance_score=0.7,
            city=request.city,
            tags=list(sorted(set(request.preferences + request.travel_style))),
            expires_at=None,
        )

        with session_scope() as session:
            session.add(trip_history)
            session.add(episodic_memory)
            session.commit()

    def save_feedback_memory(self, payload: FeedbackCreateRequest) -> str:
        summary = f"反馈: {payload.feedback_type} -> {payload.target_type}:{payload.target_name or '未知'}"
        memory = MemoryItem(
            user_id=payload.user_id,
            session_id=payload.session_id,
            memory_type="semantic",
            content=f"反馈原因: {payload.reason or '无'}",
            summary=summary,
            importance_score=0.65,
            city=payload.metadata.get("city"),
            tags=[payload.target_type, payload.feedback_type],
            expires_at=None,
        )
        with session_scope() as session:
            session.add(memory)
            session.commit()
            session.refresh(memory)
            return memory.id

    def build_memory_context(self, user_id: str, session_id: str, city: str) -> str:
        memories = self.get_relevant_memories(user_id=user_id, session_id=session_id, city=city)
        if not memories:
            return ""
        lines = ["相关记忆上下文:"]
        for memory in memories:
            text = memory.summary or memory.content
            lines.append(f"- [{memory.memory_type}] {text}")
        return "\n".join(lines)


_memory_service: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
