"""Facade that preserves the existing trip planner entrypoint."""

from __future__ import annotations

import logging
from typing import Optional

from ..models.agent_schemas import SupervisorAgentInput
from ..models.schemas import RecommendationReason, TripPlan, TripRequest
from ..models.skill_schemas import SelectedSkill
from .supervisor_agent import SupervisorAgent

logger = logging.getLogger(__name__)

_multi_agent_planner: Optional["MultiAgentTripPlanner"] = None


class MultiAgentTripPlanner:
    """Compatibility facade for the new structured multi-agent planner."""

    def __init__(self, supervisor_agent: SupervisorAgent | None = None) -> None:
        self.supervisor_agent = supervisor_agent or SupervisorAgent()
        self.attraction_agent = self.supervisor_agent.attraction_agent
        self.weather_agent = self.supervisor_agent.weather_agent
        self.hotel_agent = self.supervisor_agent.hotel_agent
        self.planning_agent = self.supervisor_agent.planning_agent

    async def plan_trip(
        self,
        request: TripRequest,
        profile_context: str = "",
        memory_context: str = "",
        rag_context: str = "",
        recommendation_reasons: Optional[list[RecommendationReason]] = None,
        skills: Optional[list[SelectedSkill]] = None,
    ) -> TripPlan:
        result = await self.supervisor_agent.execute(
            SupervisorAgentInput(
                request=request,
                profile_context=profile_context,
                memory_context=memory_context,
                rag_context=rag_context,
                recommendation_reasons=recommendation_reasons or [],
                skills=skills or [],
            )
        )
        if result.status.degraded:
            logger.warning("Trip planner returned degraded plan for city=%s", request.city)
        return result.planning_result.trip_plan


def get_trip_planner_agent() -> MultiAgentTripPlanner:
    global _multi_agent_planner
    if _multi_agent_planner is None:
        _multi_agent_planner = MultiAgentTripPlanner()
    return _multi_agent_planner
