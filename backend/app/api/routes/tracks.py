"""Travel track API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ...db.models import User
from ...models.auth_schemas import TravelTracksResponse
from ...services.security_service import get_current_user
from ...services.tracks_service import get_tracks_service

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get("", response_model=TravelTracksResponse, summary="List travel tracks")
async def list_tracks(current_user: User = Depends(get_current_user)) -> TravelTracksResponse:
    try:
        items = get_tracks_service().list_tracks(current_user.id)
        return TravelTracksResponse(success=True, message="Travel tracks fetched", data=items)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tracks: {exc}") from exc
