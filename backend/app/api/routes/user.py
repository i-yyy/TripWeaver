"""User profile routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ...db.models import User
from ...models.schemas import UserProfileResponse
from ...services.profile_service import get_profile_service
from ...services.security_service import get_current_user

router = APIRouter(prefix="/user", tags=["user-profile"])


@router.get(
    "/profile/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
)
async def get_my_profile(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    try:
        profile = get_profile_service().get_profile_data(current_user.id)
        if profile is None:
            return UserProfileResponse(success=False, message="User profile was not found", data=None)
        return UserProfileResponse(success=True, message="User profile fetched successfully", data=profile)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user profile: {exc}") from exc


@router.get(
    "/profile/{user_id}",
    response_model=UserProfileResponse,
    summary="Get user profile",
)
async def get_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only access your own profile")
    return await get_my_profile(current_user)
