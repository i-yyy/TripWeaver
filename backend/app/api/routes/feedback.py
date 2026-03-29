"""Feedback API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ...db.models import User
from ...models.schemas import FeedbackCreateRequest, FeedbackResponse
from ...services.feedback_service import get_feedback_service
from ...services.security_service import get_current_user

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post(
    "/submit",
    response_model=FeedbackResponse,
    summary="Submit feedback",
    description="Store attraction, hotel, or trip feedback for personalization.",
)
async def submit_feedback(
    payload: FeedbackCreateRequest,
    current_user: User = Depends(get_current_user),
) -> FeedbackResponse:
    try:
        payload.user_id = current_user.id
        feedback_id = get_feedback_service().create_feedback(payload)
        return FeedbackResponse(success=True, message="Feedback submitted successfully", feedback_id=feedback_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {exc}") from exc
