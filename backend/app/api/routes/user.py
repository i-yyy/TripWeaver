"""用户画像路由。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...models.schemas import UserProfileResponse
from ...services.profile_service import get_profile_service

router = APIRouter(prefix="/user", tags=["用户画像"])


@router.get(
    "/profile/{user_id}",
    response_model=UserProfileResponse,
    summary="获取用户画像",
    description="根据 user_id 获取个性化画像。",
)
async def get_user_profile(user_id: str) -> UserProfileResponse:
    try:
        profile = get_profile_service().get_profile_data(user_id)
        if profile is None:
            return UserProfileResponse(success=False, message="未找到用户画像", data=None)
        return UserProfileResponse(success=True, message="获取用户画像成功", data=profile)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取用户画像失败: {exc}") from exc
