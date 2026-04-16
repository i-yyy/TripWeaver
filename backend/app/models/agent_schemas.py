"""Structured schemas for internal multi-agent collaboration."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .schemas import Attraction, Hotel, MealCandidate, RecommendationReason, TripPlan, TripRequest, WeatherInfo
from .skill_schemas import SelectedSkill


class AgentExecutionStatus(BaseModel):
    success: bool = True
    degraded: bool = False
    warnings: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class SupervisorAgentInput(BaseModel):
    request: TripRequest
    profile_context: str = ""
    memory_context: str = ""
    rag_context: str = ""
    recommendation_reasons: List[RecommendationReason] = Field(default_factory=list)
    skills: List[SelectedSkill] = Field(default_factory=list)


class AttractionAgentInput(BaseModel):
    request: TripRequest
    profile_context: str = ""
    rag_context: str = ""
    limit: int = 12
    skills: List[SelectedSkill] = Field(default_factory=list)


class AttractionAgentOutput(BaseModel):
    status: AgentExecutionStatus = Field(default_factory=AgentExecutionStatus)
    search_queries: List[str] = Field(default_factory=list)
    attractions: List[Attraction] = Field(default_factory=list)


class WeatherAgentInput(BaseModel):
    request: TripRequest


class WeatherAgentOutput(BaseModel):
    status: AgentExecutionStatus = Field(default_factory=AgentExecutionStatus)
    weather_info: List[WeatherInfo] = Field(default_factory=list)
    summary: str = ""
    suggestions: List[str] = Field(default_factory=list)


class HotelAgentInput(BaseModel):
    request: TripRequest
    profile_context: str = ""
    limit: int = 8
    skills: List[SelectedSkill] = Field(default_factory=list)


class HotelAgentOutput(BaseModel):
    status: AgentExecutionStatus = Field(default_factory=AgentExecutionStatus)
    search_queries: List[str] = Field(default_factory=list)
    hotels: List[Hotel] = Field(default_factory=list)


class MealAgentInput(BaseModel):
    request: TripRequest
    attractions: List[Attraction] = Field(default_factory=list)
    hotels: List[Hotel] = Field(default_factory=list)
    skills: List[SelectedSkill] = Field(default_factory=list)


class MealAgentOutput(BaseModel):
    status: AgentExecutionStatus = Field(default_factory=AgentExecutionStatus)
    meal_candidates_by_day: Dict[int, Dict[str, List[MealCandidate]]] = Field(default_factory=dict)


class PlanningAgentInput(BaseModel):
    request: TripRequest
    profile_context: str = ""
    memory_context: str = ""
    rag_context: str = ""
    recommendation_reasons: List[RecommendationReason] = Field(default_factory=list)
    skills: List[SelectedSkill] = Field(default_factory=list)
    attraction_result: AttractionAgentOutput
    weather_result: WeatherAgentOutput
    hotel_result: HotelAgentOutput
    meal_result: MealAgentOutput = Field(default_factory=MealAgentOutput)
    supervisor_warnings: List[str] = Field(default_factory=list)


class PlanningAgentOutput(BaseModel):
    status: AgentExecutionStatus = Field(default_factory=AgentExecutionStatus)
    trip_plan: TripPlan
    raw_response: Optional[str] = None


class SupervisorAgentOutput(BaseModel):
    status: AgentExecutionStatus = Field(default_factory=AgentExecutionStatus)
    attraction_result: AttractionAgentOutput
    weather_result: WeatherAgentOutput
    hotel_result: HotelAgentOutput
    meal_result: MealAgentOutput
    planning_result: PlanningAgentOutput
