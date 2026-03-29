"""Map service API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ...models.schemas import POISearchResponse, RouteRequest, RouteResponse, WeatherResponse
from ...services.amap_service import get_amap_service

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/poi", response_model=POISearchResponse, summary="Search POI")
async def search_poi(
    keywords: str = Query(..., description="Search keyword", example="museum"),
    city: str = Query(..., description="City name", example="Beijing"),
    citylimit: bool = Query(True, description="Limit results within city"),
):
    try:
        service = get_amap_service()
        pois = service.search_poi(keywords, city, citylimit)
        return POISearchResponse(success=True, message="POI search succeeded", data=pois)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"POI search failed: {exc}") from exc


@router.get("/weather", response_model=WeatherResponse, summary="Get weather")
async def get_weather(
    city: str = Query(..., description="City name", example="Beijing"),
):
    try:
        service = get_amap_service()
        weather_info = service.get_weather(city)
        return WeatherResponse(success=True, message="Weather lookup succeeded", data=weather_info)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Weather lookup failed: {exc}") from exc


@router.post("/route", response_model=RouteResponse, summary="Plan route")
async def plan_route(request: RouteRequest):
    try:
        service = get_amap_service()
        route_info = service.plan_route(
            origin_address=request.origin_address,
            destination_address=request.destination_address,
            origin_city=request.origin_city,
            destination_city=request.destination_city,
            route_type=request.route_type,
        )
        return RouteResponse(success=True, message="Route planning succeeded", data=route_info)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Route planning failed: {exc}") from exc


@router.get("/health", summary="Map health")
async def health_check():
    try:
        service = get_amap_service()
        return {
            "status": "healthy",
            "service": "map-service",
            **service.health_status(),
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}") from exc
