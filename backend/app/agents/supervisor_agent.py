"""Supervisor agent that orchestrates structured sub-agents."""

from __future__ import annotations

import asyncio
import logging
from time import perf_counter
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
from ..services.skill_service import SkillService, get_skill_service
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
        skill_service: SkillService | None = None,
    ) -> None:
        self.attraction_agent = attraction_agent or AttractionAgent()
        self.weather_agent = weather_agent or WeatherAgent()
        self.hotel_agent = hotel_agent or HotelAgent()
        self.planning_agent = planning_agent or PlanningAgent()
        self.skill_service = skill_service or get_skill_service()
        self.tools: List[str] = []

    async def execute(self, payload: SupervisorAgentInput) -> SupervisorAgentOutput:
        request = payload.request
        started_at = perf_counter()
        logger.info("SupervisorAgent start city=%s days=%s", request.city, request.travel_days)

        attraction_task = asyncio.create_task(
            self.attraction_agent.execute(
                AttractionAgentInput(
                    request=request,
                    profile_context=payload.profile_context,
                    rag_context=payload.rag_context,
                    skills=payload.skills,
                )
            )
        )
        weather_task = asyncio.create_task(self.weather_agent.execute(WeatherAgentInput(request=request)))
        hotel_task = asyncio.create_task(
            self.hotel_agent.execute(
                HotelAgentInput(
                    request=request,
                    profile_context=payload.profile_context,
                    skills=payload.skills,
                )
            )
        )
        fetch_started_at = perf_counter()
        attraction_result, weather_result, hotel_result = await asyncio.gather(
            attraction_task,
            weather_task,
            hotel_task,
        )
        fetch_elapsed = perf_counter() - fetch_started_at
        logger.info(
            "⏱️ SupervisorAgent fetch completed city=%s elapsed=%.2fs attractions=%s hotels=%s weather=%s",
            request.city,
            fetch_elapsed,
            len(attraction_result.attractions),
            len(hotel_result.hotels),
            len(weather_result.weather_info),
        )

        warnings: List[str] = []
        for result in (attraction_result, weather_result, hotel_result):
            warnings.extend(result.status.warnings)

        skills_started_at = perf_counter()
        dynamic_skills = self.skill_service.augment_dynamic_skills(
            request=request,
            weather_result=weather_result,
            profile_context=payload.profile_context,
            memory_context=payload.memory_context,
            rag_context=payload.rag_context,
        )
        final_skills = self.skill_service.finalize_skills(payload.skills, dynamic_skills)
        logger.info(
            "⏱️ SupervisorAgent skills completed city=%s elapsed=%.2fs static=%s dynamic=%s final=%s",
            request.city,
            perf_counter() - skills_started_at,
            len(payload.skills),
            len(dynamic_skills),
            len(final_skills),
        )

        planning_started_at = perf_counter()
        planning_result = await self.planning_agent.execute(
            PlanningAgentInput(
                request=request,
                profile_context=payload.profile_context,
                memory_context=payload.memory_context,
                rag_context=payload.rag_context,
                recommendation_reasons=payload.recommendation_reasons,
                skills=final_skills,
                attraction_result=attraction_result,
                weather_result=weather_result,
                hotel_result=hotel_result,
                supervisor_warnings=warnings,
            )
        )
        logger.info(
            "⏱️ SupervisorAgent planning completed city=%s elapsed=%.2fs days=%s warnings=%s",
            request.city,
            perf_counter() - planning_started_at,
            len(planning_result.trip_plan.days),
            len(planning_result.status.warnings),
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
            "⏱️ SupervisorAgent finished city=%s degraded=%s attractions=%s hotels=%s weather=%s total_elapsed=%.2fs",
            request.city,
            status.degraded,
            len(attraction_result.attractions),
            len(hotel_result.hotels),
            len(weather_result.weather_info),
            perf_counter() - started_at,
        )
        return SupervisorAgentOutput(
            status=status,
            attraction_result=attraction_result,
            weather_result=weather_result,
            hotel_result=hotel_result,
            planning_result=planning_result,
        )
