"""Collaborative trip planning API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ...db.models import User
from ...models.auth_schemas import OperationResponse
from ...models.schemas import (
    CollabTripCommentCreateRequest,
    CollabTripCommentResponse,
    CollabTripCreateRequest,
    CollabTripInviteRequest,
    CollabTripInviteResponse,
    CollabTripListResponse,
    CollabTripResponse,
    CollabTripUpdateRequest,
    CollabTripVoteRequest,
    CollabTripVoteResponse,
)
from ...services.collab_service import get_collab_service
from ...services.security_service import get_current_user

router = APIRouter(prefix="/collab", tags=["collaborative-trips"])


@router.get("/trips", response_model=CollabTripListResponse, summary="List my collaborative trips")
async def list_collab_trips(current_user: User = Depends(get_current_user)) -> CollabTripListResponse:
    try:
        trips, pending_invites = get_collab_service().list_trips(current_user.id)
        return CollabTripListResponse(
            success=True,
            message="Collaborative trips fetched",
            data=trips,
            pending_invites=pending_invites,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch collaborative trips: {exc}") from exc


@router.post("/trips", response_model=CollabTripResponse, summary="Create a collaborative trip from a saved track")
async def create_collab_trip(
    payload: CollabTripCreateRequest,
    current_user: User = Depends(get_current_user),
) -> CollabTripResponse:
    try:
        trip = get_collab_service().create_trip(current_user.id, payload)
        return CollabTripResponse(success=True, message="Collaborative trip created", data=trip)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to create collaborative trip: {exc}") from exc


@router.get("/trips/{trip_id}", response_model=CollabTripResponse, summary="Get collaborative trip detail")
async def get_collab_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
) -> CollabTripResponse:
    try:
        trip = get_collab_service().get_trip_detail(current_user.id, trip_id)
        if trip is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collaborative trip not found")
        return CollabTripResponse(success=True, message="Collaborative trip fetched", data=trip)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch collaborative trip: {exc}") from exc


@router.put("/trips/{trip_id}/plan", response_model=CollabTripResponse, summary="Update collaborative trip plan")
async def update_collab_trip_plan(
    trip_id: str,
    payload: CollabTripUpdateRequest,
    current_user: User = Depends(get_current_user),
) -> CollabTripResponse:
    try:
        trip = get_collab_service().update_plan(current_user.id, trip_id, payload)
        return CollabTripResponse(success=True, message="Collaborative trip updated", data=trip)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update collaborative trip: {exc}") from exc


@router.delete("/trips/{trip_id}", response_model=OperationResponse, summary="Delete or leave a collaborative trip")
async def delete_collab_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
) -> OperationResponse:
    try:
        result = get_collab_service().delete_or_leave_trip(current_user.id, trip_id)
        return OperationResponse(
            success=True,
            message="Collaborative trip deleted" if result == "deleted" else "Left collaborative trip",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete collaborative trip: {exc}") from exc


@router.post("/trips/{trip_id}/invites", response_model=CollabTripInviteResponse, summary="Invite a friend")
async def invite_collab_trip_member(
    trip_id: str,
    payload: CollabTripInviteRequest,
    current_user: User = Depends(get_current_user),
) -> CollabTripInviteResponse:
    try:
        invite = get_collab_service().create_invite(current_user.id, trip_id, payload)
        return CollabTripInviteResponse(success=True, message="Invite sent", data=invite)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to invite member: {exc}") from exc


@router.post("/invites/{invite_id}/accept", response_model=CollabTripInviteResponse, summary="Accept invite")
async def accept_collab_invite(
    invite_id: str,
    current_user: User = Depends(get_current_user),
) -> CollabTripInviteResponse:
    try:
        invite = get_collab_service().respond_invite(current_user.id, invite_id, accepted=True)
        return CollabTripInviteResponse(success=True, message="Invite accepted", data=invite)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to accept invite: {exc}") from exc


@router.post("/invites/{invite_id}/reject", response_model=CollabTripInviteResponse, summary="Reject invite")
async def reject_collab_invite(
    invite_id: str,
    current_user: User = Depends(get_current_user),
) -> CollabTripInviteResponse:
    try:
        invite = get_collab_service().respond_invite(current_user.id, invite_id, accepted=False)
        return CollabTripInviteResponse(success=True, message="Invite rejected", data=invite)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to reject invite: {exc}") from exc


@router.post("/trips/{trip_id}/comments", response_model=CollabTripCommentResponse, summary="Comment on collaborative trip")
async def add_collab_trip_comment(
    trip_id: str,
    payload: CollabTripCommentCreateRequest,
    current_user: User = Depends(get_current_user),
) -> CollabTripCommentResponse:
    try:
        comment = get_collab_service().add_comment(current_user.id, trip_id, payload)
        return CollabTripCommentResponse(success=True, message="Comment added", data=comment)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to add comment: {exc}") from exc


@router.post("/trips/{trip_id}/votes", response_model=CollabTripVoteResponse, summary="Vote on trip item")
async def vote_collab_trip_item(
    trip_id: str,
    payload: CollabTripVoteRequest,
    current_user: User = Depends(get_current_user),
) -> CollabTripVoteResponse:
    try:
        vote, active = get_collab_service().toggle_vote(current_user.id, trip_id, payload)
        return CollabTripVoteResponse(success=True, message="Vote updated", data=vote, active=active)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update vote: {exc}") from exc
