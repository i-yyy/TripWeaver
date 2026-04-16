"""Community feed API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile

from ...db.models import User
from ...models.schemas import (
    CommunityCommentCreateRequest,
    CommunityCommentResponse,
    CommunityFeedResponse,
    CommunityImageUploadResponse,
    CommunityInteractionResponse,
    CommunityFollowResponse,
    CommunityPostCommentCreateRequest,
    CommunityPostCommentResponse,
    CommunityPostCreateRequest,
    CommunityPostFeedResponse,
    CommunityProfileHomeResponse,
    CommunityPostResponse,
    TripPlanResponse,
)
from ...services.community_service import get_community_service
from ...services.security_service import get_current_user

router = APIRouter(prefix="/community", tags=["community"])


@router.get(
    "/feed",
    response_model=CommunityFeedResponse,
    summary="Get personalized community travel feed",
)
async def get_personalized_feed(
    limit: int = Query(default=8, ge=1, le=20),
    refresh_token: str = Query(default="", max_length=80),
    current_user: User = Depends(get_current_user),
) -> CommunityFeedResponse:
    try:
        data = get_community_service().build_feed(current_user.id, limit=limit, refresh_token=refresh_token)
        return CommunityFeedResponse(success=True, message="Community feed fetched", data=data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch community feed: {exc}") from exc


@router.post(
    "/uploads/image",
    response_model=CommunityImageUploadResponse,
    summary="Upload one community image from local device",
)
async def upload_community_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> CommunityImageUploadResponse:
    del current_user
    try:
        relative_url = get_community_service().save_uploaded_image(file)
        absolute_url = str(request.base_url).rstrip("/") + relative_url
        return CommunityImageUploadResponse(success=True, message="Image uploaded", url=absolute_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {exc}") from exc


@router.post(
    "/cards/{card_id}/like",
    response_model=CommunityInteractionResponse,
    summary="Like or unlike a community trip card",
)
async def toggle_card_like(
    card_id: str,
    current_user: User = Depends(get_current_user),
) -> CommunityInteractionResponse:
    try:
        active = get_community_service().toggle_interaction(current_user.id, card_id, "like")
        return CommunityInteractionResponse(
            success=True,
            message="Liked" if active else "Unliked",
            active=active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update like: {exc}") from exc


@router.post(
    "/cards/{card_id}/favorite",
    response_model=CommunityInteractionResponse,
    summary="Favorite or unfavorite a community trip card",
)
async def toggle_card_favorite(
    card_id: str,
    current_user: User = Depends(get_current_user),
) -> CommunityInteractionResponse:
    try:
        active = get_community_service().toggle_interaction(current_user.id, card_id, "favorite")
        return CommunityInteractionResponse(
            success=True,
            message="Favorited" if active else "Unfavorited",
            active=active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update favorite: {exc}") from exc


@router.post(
    "/cards/{card_id}/reuse",
    response_model=CommunityInteractionResponse,
    summary="Record community card reuse",
)
async def reuse_card(
    card_id: str,
    current_user: User = Depends(get_current_user),
) -> CommunityInteractionResponse:
    try:
        get_community_service().record_reuse(current_user.id, card_id)
        return CommunityInteractionResponse(success=True, message="Reuse recorded", active=True)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to record reuse: {exc}") from exc


@router.post(
    "/cards/{card_id}/comments",
    response_model=CommunityCommentResponse,
    summary="Comment on a community trip card",
)
async def add_card_comment(
    card_id: str,
    payload: CommunityCommentCreateRequest,
    current_user: User = Depends(get_current_user),
) -> CommunityCommentResponse:
    try:
        comment = get_community_service().add_comment(
            user_id=current_user.id,
            author_name=current_user.nickname or current_user.email or "旅行者",
            card_id=card_id,
            content=payload.content,
        )
        return CommunityCommentResponse(success=True, message="Comment posted", data=comment)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to add comment: {exc}") from exc


@router.get(
    "/posts",
    response_model=CommunityPostFeedResponse,
    summary="List community moments posts",
)
async def list_posts(
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
) -> CommunityPostFeedResponse:
    try:
        data = get_community_service().list_posts(current_user.id, limit=limit)
        return CommunityPostFeedResponse(success=True, message="Posts fetched", data=data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch posts: {exc}") from exc


@router.get(
    "/profile/me",
    response_model=CommunityProfileHomeResponse,
    summary="Get current user's community profile homepage",
)
async def get_my_community_profile(
    limit: int = Query(default=60, ge=1, le=100),
    current_user: User = Depends(get_current_user),
) -> CommunityProfileHomeResponse:
    try:
        data = get_community_service().get_profile_home(current_user.id, current_user.id, limit=limit)
        return CommunityProfileHomeResponse(success=True, message="Community profile fetched", data=data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch community profile: {exc}") from exc


@router.get(
    "/profile/{profile_user_id}",
    response_model=CommunityProfileHomeResponse,
    summary="Get one community author's public homepage",
)
async def get_community_profile(
    profile_user_id: str,
    limit: int = Query(default=60, ge=1, le=100),
    current_user: User = Depends(get_current_user),
) -> CommunityProfileHomeResponse:
    try:
        data = get_community_service().get_profile_home(current_user.id, profile_user_id, limit=limit)
        if data is None:
            raise HTTPException(status_code=404, detail="Community profile not found")
        return CommunityProfileHomeResponse(success=True, message="Community profile fetched", data=data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch community profile: {exc}") from exc


@router.post(
    "/posts",
    response_model=CommunityPostResponse,
    summary="Publish a community moments post",
)
async def create_post(
    payload: CommunityPostCreateRequest,
    current_user: User = Depends(get_current_user),
) -> CommunityPostResponse:
    try:
        post = get_community_service().create_post(
            user_id=current_user.id,
            author_name=current_user.nickname or current_user.email or "旅行者",
            payload=payload,
        )
        return CommunityPostResponse(success=True, message="Post published", data=post)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to publish post: {exc}") from exc


@router.post(
    "/posts/{post_id}/like",
    response_model=CommunityInteractionResponse,
    summary="Like or unlike a community post",
)
async def toggle_post_like(
    post_id: str,
    current_user: User = Depends(get_current_user),
) -> CommunityInteractionResponse:
    try:
        active = get_community_service().toggle_post_like(current_user.id, post_id)
        return CommunityInteractionResponse(success=True, message="Post like updated", active=active)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update post like: {exc}") from exc


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommunityPostCommentResponse,
    summary="Comment on a community post",
)
async def add_post_comment(
    post_id: str,
    payload: CommunityPostCommentCreateRequest,
    current_user: User = Depends(get_current_user),
) -> CommunityPostCommentResponse:
    try:
        comment = get_community_service().add_post_comment(
            user_id=current_user.id,
            author_name=current_user.nickname or current_user.email or "旅行者",
            post_id=post_id,
            content=payload.content,
        )
        return CommunityPostCommentResponse(success=True, message="Post comment added", data=comment)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to add post comment: {exc}") from exc


@router.get(
    "/posts/{post_id}/plan",
    response_model=TripPlanResponse,
    summary="Get trip plan linked from one community post",
)
async def get_post_linked_plan(
    post_id: str,
    current_user: User = Depends(get_current_user),
) -> TripPlanResponse:
    del current_user
    try:
        plan = get_community_service().get_post_linked_plan(post_id)
        if plan is None:
            raise HTTPException(status_code=404, detail="Linked trip plan not found")
        return TripPlanResponse(success=True, message="Linked trip plan fetched", data=plan)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch linked trip plan: {exc}") from exc


@router.post(
    "/users/{target_user_id}/follow",
    response_model=CommunityFollowResponse,
    summary="Follow or unfollow a community author",
)
async def toggle_follow(
    target_user_id: str,
    current_user: User = Depends(get_current_user),
) -> CommunityFollowResponse:
    try:
        active = get_community_service().toggle_follow(current_user.id, target_user_id)
        return CommunityFollowResponse(success=True, message="Follow updated", active=active)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update follow: {exc}") from exc
