"""反馈持久化服务。"""

from __future__ import annotations

from typing import Optional

from ..db.database import session_scope
from ..db.models import UserFeedback
from ..models.schemas import FeedbackCreateRequest
from .memory_service import get_memory_service
from .profile_service import get_profile_service


class FeedbackService:
    """保存反馈并联动更新画像与记忆。"""

    def create_feedback(self, payload: FeedbackCreateRequest) -> str:
        feedback = UserFeedback(
            user_id=payload.user_id,
            session_id=payload.session_id,
            target_type=payload.target_type,
            target_name=payload.target_name,
            feedback_type=payload.feedback_type,
            reason=payload.reason,
            metadata=payload.metadata,
        )
        with session_scope() as session:
            session.add(feedback)
            session.commit()
            session.refresh(feedback)

        # 尽力更新画像与记忆，不影响反馈主流程。
        try:
            get_profile_service().update_profile_from_feedback(payload)
        except Exception as exc:  # pragma: no cover - best effort update
            print(f"反馈后更新画像失败: {exc}")

        try:
            get_memory_service().save_feedback_memory(payload)
        except Exception as exc:  # pragma: no cover - best effort update
            print(f"反馈后写入记忆失败: {exc}")

        return feedback.id


_feedback_service: Optional[FeedbackService] = None


def get_feedback_service() -> FeedbackService:
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service
