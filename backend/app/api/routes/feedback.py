"""反馈路由。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...models.schemas import FeedbackCreateRequest, FeedbackResponse
from ...services.feedback_service import get_feedback_service

router = APIRouter(prefix="/feedback", tags=["反馈"])


@router.post(
    "/submit",
    response_model=FeedbackResponse,
    summary="提交反馈",
    description="提交景点/酒店/整体行程反馈，用于个性化学习。",
)
async def submit_feedback(payload: FeedbackCreateRequest) -> FeedbackResponse:
    try:
        feedback_id = get_feedback_service().create_feedback(payload)
        return FeedbackResponse(success=True, message="反馈提交成功", feedback_id=feedback_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"反馈提交失败: {exc}") from exc
