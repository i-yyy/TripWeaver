"""Pydantic schemas used by API and agents."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


# =====================
# Request schemas
# =====================


class TripRequest(BaseModel):
    """Trip planning request."""

    user_id: str = Field(..., description="Stable user id")
    session_id: str = Field(..., description="Current planning session id")

    city: str = Field(..., description="Destination city", examples=["Beijing"])
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")
    travel_days: int = Field(..., ge=1, le=30, description="Number of travel days")

    transportation: str = Field(..., description="Preferred transportation mode")
    accommodation: str = Field(..., description="Preferred accommodation type")
    preferences: List[str] = Field(default_factory=list, description="Interest tags")
    free_text_input: str = Field(default="", description="Extra request")

    budget_level: Optional[str] = Field(default=None, description="low/medium/high")
    travel_style: List[str] = Field(default_factory=list, description="e.g. citywalk, museum, food")
    companions: List[str] = Field(default_factory=list, description="e.g. solo, couple, family")
    dietary_restrictions: List[str] = Field(default_factory=list)
    mobility_needs: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "session_id": "sess_20260325_01",
                "city": "Beijing",
                "start_date": "2026-04-01",
                "end_date": "2026-04-03",
                "travel_days": 3,
                "transportation": "public transit",
                "accommodation": "comfortable hotel",
                "preferences": ["history", "food"],
                "free_text_input": "Need rain backup plan",
                "budget_level": "medium",
                "travel_style": ["museum", "citywalk"],
                "companions": ["family"],
                "dietary_restrictions": ["no seafood"],
                "mobility_needs": ["low walking load"],
            }
        }


class POISearchRequest(BaseModel):
    keywords: str = Field(..., description="Search keyword")
    city: str = Field(..., description="City")
    citylimit: bool = Field(default=True, description="Limit results within city")


class RouteRequest(BaseModel):
    origin_address: str = Field(..., description="Origin address")
    destination_address: str = Field(..., description="Destination address")
    origin_city: Optional[str] = Field(default=None, description="Origin city")
    destination_city: Optional[str] = Field(default=None, description="Destination city")
    route_type: str = Field(default="walking", description="walking/driving/transit")


class DayRouteStopRequest(BaseModel):
    name: str = Field(..., description="Stop name")
    address: str = Field(default="", description="Stop address")
    location: Optional["Location"] = Field(default=None, description="Preferred stop coordinates")
    image_url: Optional[str] = Field(default=None, description="Stop image url")


class DayRouteRequest(BaseModel):
    city: str = Field(default="", description="Destination city")
    route_type: str = Field(default="walking", description="walking/driving/transit")
    hotel: Optional[DayRouteStopRequest] = Field(default=None, description="Hotel stop")
    attractions: List[DayRouteStopRequest] = Field(default_factory=list, description="Ordered attractions")


class FeedbackCreateRequest(BaseModel):
    """Feedback request from frontend."""

    user_id: str
    session_id: str
    target_type: str = Field(..., description="attraction/hotel/plan")
    target_name: str = Field(default="", description="Target name")
    feedback_type: str = Field(..., description="like/dislike/replace/satisfied/unsatisfied")
    reason: str = Field(default="")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# =====================
# Domain schemas
# =====================


class Location(BaseModel):
    longitude: float
    latitude: float


class Attraction(BaseModel):
    name: str
    address: str
    location: Location
    visit_duration: int
    description: str
    category: Optional[str] = "attraction"
    rating: Optional[float] = None
    photos: List[str] = Field(default_factory=list)
    poi_id: str = ""
    image_url: Optional[str] = None
    map_image_url: Optional[str] = None
    ticket_price: int = 0


class Meal(BaseModel):
    type: str
    name: str
    address: Optional[str] = None
    location: Optional[Location] = None
    description: Optional[str] = None
    estimated_cost: int = 0


class Hotel(BaseModel):
    name: str
    address: str = ""
    location: Optional[Location] = None
    price_range: str = ""
    rating: str = ""
    distance: str = ""
    type: str = ""
    estimated_cost: int = 0
    map_image_url: Optional[str] = None


class DayPlan(BaseModel):
    date: str
    day_index: int
    description: str
    transportation: str
    transportation_detail: str = ""
    transportation_cost: int = 0
    accommodation: str
    hotel: Optional[Hotel] = None
    attractions: List[Attraction] = Field(default_factory=list)
    meals: List[Meal] = Field(default_factory=list)
    route_summary: str = ""
    route_map_url: Optional[str] = None


class WeatherInfo(BaseModel):
    date: str
    day_weather: str = ""
    night_weather: str = ""
    day_temp: Union[int, str] = 0
    night_temp: Union[int, str] = 0
    wind_direction: str = ""
    wind_power: str = ""

    @field_validator("day_temp", "night_temp", mode="before")
    @classmethod
    def parse_temperature(cls, value: Union[int, str]) -> int:
        if isinstance(value, str):
            value = value.replace("°C", "").replace("℃", "").strip()
            try:
                return int(value)
            except ValueError:
                return 0
        return int(value)


class Budget(BaseModel):
    total_attractions: int = 0
    total_hotels: int = 0
    total_meals: int = 0
    total_transportation: int = 0
    total: int = 0


class RecommendationReason(BaseModel):
    source_type: str = Field(default="knowledge_base", description="knowledge_base/profile/memory")
    title: str = Field(default="", description="前端展示标题")
    reason: str = Field(default="", description="推荐理由")
    snippet: str = Field(default="", description="命中片段摘要")
    score: float = Field(default=0.0, description="综合相关性分数")
    rerank_mode: str = Field(default="", description="重排模式")
    source_doc: Optional[str] = Field(default=None, description="来源文档路径")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class TripPlan(BaseModel):
    city: str
    start_date: str
    end_date: str
    days: List[DayPlan]
    weather_info: List[WeatherInfo] = Field(default_factory=list)
    overall_suggestions: str
    budget: Optional[Budget] = None
    recommendation_reasons: List[RecommendationReason] = Field(default_factory=list)


class POIInfo(BaseModel):
    id: str
    name: str
    type: str
    address: str
    location: Location
    tel: Optional[str] = None


class RouteInfo(BaseModel):
    distance: float
    duration: int
    route_type: str
    description: str


class RouteMarker(BaseModel):
    label: str
    title: str
    kind: str
    address: str = ""
    location: Location
    image_url: Optional[str] = None


class RouteSegment(BaseModel):
    start_label: str
    end_label: str
    route_type: str
    distance: float = 0.0
    duration: int = 0
    description: str = ""
    polyline: List[Location] = Field(default_factory=list)


class DayRouteInfo(BaseModel):
    route_type: str
    summary: str = ""
    distance: float = 0.0
    duration: int = 0
    markers: List[RouteMarker] = Field(default_factory=list)
    segments: List[RouteSegment] = Field(default_factory=list)
    fallback_static_map_url: Optional[str] = None


class UserProfileData(BaseModel):
    user_id: str
    preferred_transportation: Optional[str] = None
    preferred_accommodation: Optional[str] = None
    budget_level: Optional[str] = None
    pace_level: Optional[str] = None
    interest_weights: Dict[str, float] = Field(default_factory=dict)
    dietary_restrictions: List[str] = Field(default_factory=list)
    mobility_needs: List[str] = Field(default_factory=list)
    avoid_tags: List[str] = Field(default_factory=list)
    updated_at: Optional[datetime] = None


class MemoryFact(BaseModel):
    memory_type: str
    content: str
    summary: str = ""
    importance_score: float = 0.5
    city: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


# =====================
# Response schemas
# =====================


class TripPlanResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[TripPlan] = None


class POISearchResponse(BaseModel):
    success: bool
    message: str = ""
    data: List[POIInfo] = Field(default_factory=list)


class RouteResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[RouteInfo] = None


class DayRouteResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[DayRouteInfo] = None


class WeatherResponse(BaseModel):
    success: bool
    message: str = ""
    data: List[WeatherInfo] = Field(default_factory=list)


class FeedbackResponse(BaseModel):
    success: bool
    message: str = ""
    feedback_id: Optional[str] = None


class UserProfileResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[UserProfileData] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
