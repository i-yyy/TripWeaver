"""Supervisor agent that orchestrates structured sub-agents."""

from __future__ import annotations

import asyncio
import logging
from typing import List

from ..models.agent_schemas import (
    AgentExecutionStatus,
    AttractionAgentInput,
    HotelAgentInput,
    PlanningAgentInput,
    SupervisorAgentInput,
    SupervisorAgentOutput,
    WeatherAgentInput,
)
from .attraction_agent import AttractionAgent
from .hotel_agent import HotelAgent
from .planning_agent import PlanningAgent
from .weather_agent import WeatherAgent

logger = logging.getLogger(__name__)


class SupervisorAgent:
    def __init__(
        self,
        attraction_agent: AttractionAgent | None = None,
        weather_agent: WeatherAgent | None = None,
        hotel_agent: HotelAgent | None = None,
        planning_agent: PlanningAgent | None = None,
    ) -> None:
        self.attraction_agent = attraction_agent or AttractionAgent()
        self.weather_agent = weather_agent or WeatherAgent()
        self.hotel_agent = hotel_agent or HotelAgent()
        self.planning_agent = planning_agent or PlanningAgent()
        self.tools: List[str] = []

    async def execute(self, payload: SupervisorAgentInput) -> SupervisorAgentOutput:
        request = payload.request
        logger.info("SupervisorAgent start city=%s days=%s", request.city, request.travel_days)

        attraction_task = asyncio.create_task(
            self.attraction_agent.execute(
                AttractionAgentInput(
                    request=request,
                    profile_context=payload.profile_context,
                    rag_context=payload.rag_context,
                )
            )
        )
        weather_task = asyncio.create_task(self.weather_agent.execute(WeatherAgentInput(request=request)))
        hotel_task = asyncio.create_task(
            self.hotel_agent.execute(
                HotelAgentInput(
                    request=request,
                    profile_context=payload.profile_context,
                )
            )
        )
        attraction_result, weather_result, hotel_result = await asyncio.gather(
            attraction_task,
            weather_task,
            hotel_task,
        )

        warnings: List[str] = []
        for result in (attraction_result, weather_result, hotel_result):
            warnings.extend(result.status.warnings)

        planning_result = await self.planning_agent.execute(
            PlanningAgentInput(
                request=request,
                profile_context=payload.profile_context,
                memory_context=payload.memory_context,
                rag_context=payload.rag_context,
                recommendation_reasons=payload.recommendation_reasons,
                attraction_result=attraction_result,
                weather_result=weather_result,
                hotel_result=hotel_result,
                supervisor_warnings=warnings,
            )
        )

        combined_warnings = warnings + planning_result.status.warnings
        status = AgentExecutionStatus(
            success=planning_result.status.success,
            degraded=any(
                [
                    attraction_result.status.degraded,
                    weather_result.status.degraded,
                    hotel_result.status.degraded,
                    planning_result.status.degraded,
                ]
            ),
            warnings=combined_warnings,
            error=planning_result.status.error,
        )

        logger.info(
            "SupervisorAgent finished city=%s degraded=%s attractions=%s hotels=%s weather=%s",
            request.city,
            status.degraded,
            len(attraction_result.attractions),
            len(hotel_result.hotels),
            len(weather_result.weather_info),
        )
        return SupervisorAgentOutput(
            status=status,
            attraction_result=attraction_result,
            weather_result=weather_result,
            hotel_result=hotel_result,
            planning_result=planning_result,
        )
