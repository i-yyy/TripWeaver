"""Pydantic schemas used by API and agents."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from .skill_schemas import SelectedSkill


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


class TripScoreSummary(BaseModel):
    """Lightweight summary payload used by decision scoring."""

    budget_level: Optional[str] = Field(default=None, description="low/medium/high")
    travel_style: List[str] = Field(default_factory=list, description="e.g. citywalk, museum, food")
    companions: List[str] = Field(default_factory=list, description="e.g. solo, couple, family")
    dietary_restrictions: List[str] = Field(default_factory=list)
    mobility_needs: List[str] = Field(default_factory=list)
    transportation: str = Field(default="", description="Preferred transportation mode")
    free_text_input: str = Field(default="", description="Extra request")


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
    image_source: Optional[str] = None
    image_status: Optional[str] = None
    map_image_url: Optional[str] = None
    ticket_price: int = 0


class Meal(BaseModel):
    type: str
    name: str
    address: Optional[str] = None
    location: Optional[Location] = None
    description: Optional[str] = None
    estimated_cost: int = 0


class MealCandidate(BaseModel):
    meal_type: str
    name: str
    poi_id: str = ""
    address: str = ""
    location: Optional[Location] = None
    category: str = ""
    tags: List[str] = Field(default_factory=list)
    estimated_cost: int = 0
    source_query: str = ""


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


class DecisionScoreFactor(BaseModel):
    label: str
    impact: float = 0.0
    reason: str = ""
    value: str = ""


class DecisionScoreDimension(BaseModel):
    key: str
    label: str
    description: str
    score: int = 0
    detail: str = ""
    narrative: str = ""
    factors: List[DecisionScoreFactor] = Field(default_factory=list)


class DecisionScoreSnapshot(BaseModel):
    overall: int = 0
    dimensions: List[DecisionScoreDimension] = Field(default_factory=list)
    summary: str = ""
    story: str = ""
    highlights: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    budget: Budget = Field(default_factory=Budget)
    estimated_distance_km: float = 0.0
    estimated_distance_text: str = ""
    comfort_text: str = ""


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
    decision_score: Optional[DecisionScoreSnapshot] = None
    recommendation_reasons: List[RecommendationReason] = Field(default_factory=list)
    applied_skills: List[SelectedSkill] = Field(default_factory=list)


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


class CommunityCommentData(BaseModel):
    id: str
    card_id: str
    author_name: str = "旅行者"
    author_avatar_url: str = ""
    content: str
    created_at: datetime


class CommunityPostCommentData(BaseModel):
    id: str
    post_id: str
    author_name: str = "旅行者"
    author_avatar_url: str = ""
    content: str
    created_at: datetime


class CommunityTripCard(BaseModel):
    id: str
    city: str
    title: str
    subtitle: str = ""
    summary: str
    cover_image_url: str = ""
    days: int = 2
    estimated_budget: str = "medium"
    tags: List[str] = Field(default_factory=list)
    travel_style: List[str] = Field(default_factory=list)
    companions: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    author_name: str = "社区旅行者"
    like_count: int = 0
    favorite_count: int = 0
    comment_count: int = 0
    reuse_count: int = 0
    match_score: float = 0.0
    match_reasons: List[str] = Field(default_factory=list)
    liked_by_me: bool = False
    favorited_by_me: bool = False
    recent_comments: List[CommunityCommentData] = Field(default_factory=list)


class CommunityFeedData(BaseModel):
    cards: List[CommunityTripCard] = Field(default_factory=list)
    preference_tags: List[str] = Field(default_factory=list)
    recent_cities: List[str] = Field(default_factory=list)
    summary: str = ""


class CommunityPostData(BaseModel):
    id: str
    user_id: str
    author_name: str = "旅行者"
    author_avatar_url: str = ""
    content: str
    image_urls: List[str] = Field(default_factory=list)
    city: str = ""
    tags: List[str] = Field(default_factory=list)
    linked_track_id: str = ""
    linked_track_title: str = ""
    like_count: int = 0
    comment_count: int = 0
    created_at: datetime
    liked_by_me: bool = False
    followed_author: bool = False
    recent_comments: List[CommunityPostCommentData] = Field(default_factory=list)


class CommunityUserSummary(BaseModel):
    id: str
    nickname: str = "旅行者"
    email: str = ""
    avatar_url: str = ""
    gender: str = ""
    followed_by_me: bool = False


class CommunityProfileHomeData(BaseModel):
    user: CommunityUserSummary
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0
    followers: List[CommunityUserSummary] = Field(default_factory=list)
    following: List[CommunityUserSummary] = Field(default_factory=list)
    posts: List[CommunityPostData] = Field(default_factory=list)


# =====================
# Response schemas
# =====================


class TripPlanResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[TripPlan] = None


class TripScoreRequest(BaseModel):
    plan: TripPlan
    summary: Optional[TripScoreSummary] = None


class TripScoreResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[DecisionScoreSnapshot] = None


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


class CommunityFeedResponse(BaseModel):
    success: bool
    message: str = ""
    data: CommunityFeedData = Field(default_factory=CommunityFeedData)


class CommunityInteractionResponse(BaseModel):
    success: bool
    message: str = ""
    active: bool = False


class CommunityCommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=300)


class CommunityCommentResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[CommunityCommentData] = None


class CommunityPostCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=600)
    image_urls: List[str] = Field(default_factory=list, max_length=9)
    city: str = Field(default="", max_length=50)
    tags: List[str] = Field(default_factory=list, max_length=8)
    linked_track_id: str = Field(default="", max_length=80)
    linked_track_title: str = Field(default="", max_length=120)


class CommunityPostCommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=300)


class CommunityPostResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[CommunityPostData] = None


class CommunityPostFeedResponse(BaseModel):
    success: bool
    message: str = ""
    data: List[CommunityPostData] = Field(default_factory=list)


class CommunityProfileHomeResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[CommunityProfileHomeData] = None


class CollabUserData(BaseModel):
    id: str
    nickname: str = "旅行者"
    email: str = ""
    avatar_url: str = ""


class CollabTripMemberData(BaseModel):
    id: str
    trip_id: str
    user_id: str
    role: str = "viewer"
    status: str = "active"
    joined_at: datetime
    user: CollabUserData


class CollabTripInviteData(BaseModel):
    id: str
    trip_id: str
    inviter_user_id: str
    invitee_user_id: str = ""
    invitee_email: str = ""
    role: str = "editor"
    status: str = "pending"
    created_at: datetime
    responded_at: Optional[datetime] = None
    inviter: Optional[CollabUserData] = None
    invitee: Optional[CollabUserData] = None
    trip_title: str = ""
    city: str = ""


class CollabTripCommentData(BaseModel):
    id: str
    trip_id: str
    day_index: Optional[int] = None
    user_id: str
    content: str
    created_at: datetime
    user: CollabUserData


class CollabTripVoteData(BaseModel):
    id: str
    trip_id: str
    target_type: str = "attraction"
    target_id: str
    user_id: str
    vote_type: str = "want"
    created_at: datetime
    user: CollabUserData


class CollabTripChangeData(BaseModel):
    id: str
    trip_id: str
    user_id: str
    change_type: str = "update"
    summary: str = ""
    before_json: Dict[str, Any] = Field(default_factory=dict)
    after_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    user: CollabUserData


class CollabTripSummaryData(BaseModel):
    id: str
    owner_user_id: str
    source_track_id: str = ""
    title: str
    city: str = ""
    start_date: str = ""
    end_date: str = ""
    status: str = "draft"
    version: int = 1
    updated_at: datetime
    created_at: datetime
    owner: CollabUserData
    my_role: str = "viewer"
    member_count: int = 0
    comment_count: int = 0


class CollabTripDetailData(CollabTripSummaryData):
    plan_json: Dict[str, Any] = Field(default_factory=dict)
    members: List[CollabTripMemberData] = Field(default_factory=list)
    invites: List[CollabTripInviteData] = Field(default_factory=list)
    comments: List[CollabTripCommentData] = Field(default_factory=list)
    votes: List[CollabTripVoteData] = Field(default_factory=list)
    changes: List[CollabTripChangeData] = Field(default_factory=list)


class CollabTripCreateRequest(BaseModel):
    source_track_id: str = Field(..., min_length=1, max_length=80)
    title: str = Field(default="", max_length=120)


class CollabTripUpdateRequest(BaseModel):
    plan_json: Dict[str, Any] = Field(default_factory=dict)
    summary: str = Field(default="更新了协同行程", max_length=240)


class CollabTripInviteRequest(BaseModel):
    identifier: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="editor", max_length=20)


class CollabTripCommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)
    day_index: Optional[int] = None


class CollabTripVoteRequest(BaseModel):
    target_type: str = Field(default="attraction", max_length=40)
    target_id: str = Field(..., min_length=1, max_length=255)
    vote_type: str = Field(default="want", max_length=40)


class CollabTripListResponse(BaseModel):
    success: bool
    message: str = ""
    data: List[CollabTripSummaryData] = Field(default_factory=list)
    pending_invites: List[CollabTripInviteData] = Field(default_factory=list)


class CollabTripResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[CollabTripDetailData] = None


class CollabTripInviteResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[CollabTripInviteData] = None


class CollabTripCommentResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[CollabTripCommentData] = None


class CollabTripVoteResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[CollabTripVoteData] = None
    active: bool = False


class CommunityPostCommentResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[CommunityPostCommentData] = None


class CommunityFollowResponse(BaseModel):
    success: bool
    message: str = ""
    active: bool = False


class CommunityImageUploadResponse(BaseModel):
    success: bool
    message: str = ""
    url: str = ""


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
