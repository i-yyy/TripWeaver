"""Travel history retrieval for the map view."""

from __future__ import annotations

import logging
from typing import List

from sqlmodel import select

from ..db.database import session_scope
from ..db.models import TripHistory
from ..models.auth_schemas import TravelTrackItem
from .amap_service import get_amap_service

logger = logging.getLogger(__name__)


class TracksService:
    def list_tracks(self, user_id: str) -> List[TravelTrackItem]:
        with session_scope() as session:
            statement = (
                select(TripHistory)
                .where(TripHistory.user_id == user_id)
                .order_by(TripHistory.created_at.desc())
            )
            items = session.exec(statement).all()

            updated = False
            for item in items:
                if item.city_longitude is not None and item.city_latitude is not None:
                    continue
                try:
                    location = get_amap_service().geocode_city_http(item.city)
                except Exception as exc:
                    logger.warning("Track geocode backfill failed for city=%s: %s", item.city, exc)
                    continue
                if location is None:
                    continue
                item.city_longitude = location.longitude
                item.city_latitude = location.latitude
                session.add(item)
                updated = True

            if updated:
                session.commit()

        return [
            TravelTrackItem(
                id=item.id,
                city=item.city,
                start_date=item.start_date,
                end_date=item.end_date,
                searched_at=item.created_at,
                trip_summary=item.trip_summary,
                city_longitude=item.city_longitude,
                city_latitude=item.city_latitude,
            )
            for item in items
        ]


_tracks_service: TracksService | None = None


def get_tracks_service() -> TracksService:
    global _tracks_service
    if _tracks_service is None:
        _tracks_service = TracksService()
    return _tracks_service
