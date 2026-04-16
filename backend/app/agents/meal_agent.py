"""Structured meal candidate retrieval agent."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List

from ..models.agent_schemas import AgentExecutionStatus, MealAgentInput, MealAgentOutput
from ..models.schemas import Attraction, Location, MealCandidate
from ..services.meal_candidate_service import MealCandidateService, get_meal_candidate_service

logger = logging.getLogger(__name__)


class MealAgent:
    def __init__(self, meal_candidate_service: MealCandidateService | None = None) -> None:
        self.meal_candidate_service = meal_candidate_service or get_meal_candidate_service()
        self.tools = ["meal_candidate_service.retrieve_day_candidates"]

    def list_tools(self) -> List[str]:
        return list(self.tools)

    async def execute(self, payload: MealAgentInput) -> MealAgentOutput:
        try:
            candidates_by_day, warnings = await asyncio.to_thread(self._retrieve_candidates, payload)
            degraded = bool(warnings)
            if not candidates_by_day:
                warnings = warnings + ["Meal candidate service returned no structured data"]
                degraded = True

            logger.info(
                "MealAgent city=%s days=%s degraded=%s",
                payload.request.city,
                len(candidates_by_day),
                degraded,
            )
            return MealAgentOutput(
                status=AgentExecutionStatus(
                    success=not degraded,
                    degraded=degraded,
                    warnings=warnings,
                    error=warnings[0] if warnings else None,
                ),
                meal_candidates_by_day=candidates_by_day,
            )
        except Exception as exc:  # pragma: no cover - external dependency
            warning = f"Meal candidate lookup failed: {exc}"
            logger.warning(warning)
            return MealAgentOutput(
                status=AgentExecutionStatus(
                    success=False,
                    degraded=True,
                    warnings=[warning],
                    error=warning,
                ),
                meal_candidates_by_day={},
            )

    def _retrieve_candidates(
        self,
        payload: MealAgentInput,
    ) -> tuple[Dict[int, Dict[str, List[MealCandidate]]], List[str]]:
        request = payload.request
        warnings: List[str] = []
        attraction_pool = payload.attractions or self._build_default_attractions(
            request.city,
            request.travel_days,
            request,
        )
        hotel_pool = payload.hotels
        candidates_by_day: Dict[int, Dict[str, List[MealCandidate]]] = {}

        for day_index in range(request.travel_days):
            day_attractions = self._pick_day_attractions(attraction_pool, day_index, request)
            day_hotel = hotel_pool[day_index % len(hotel_pool)] if hotel_pool else None
            try:
                candidates_by_day[day_index] = self.meal_candidate_service.retrieve_day_candidates(
                    request=request,
                    day_index=day_index,
                    attractions=day_attractions,
                    hotel=day_hotel,
                    skills=payload.skills,
                )
            except Exception as exc:  # pragma: no cover - external dependency
                warning = f"Meal candidate retrieval failed day={day_index + 1}: {exc}"
                logger.warning(
                    "Meal candidate retrieval failed city=%s day=%s error=%s",
                    request.city,
                    day_index,
                    exc,
                )
                warnings.append(warning)
                candidates_by_day[day_index] = {}
        return candidates_by_day, warnings

    def _daily_attraction_target_count(self, request) -> int:
        style_tokens = {str(item).strip().lower() for item in getattr(request, "travel_style", [])}
        companion_tokens = {str(item).strip().lower() for item in getattr(request, "companions", [])}
        mobility_tokens = {str(item).strip().lower() for item in getattr(request, "mobility_needs", [])}
        extra_text = str(getattr(request, "free_text_input", "") or "").strip().lower()

        low_intensity_mobility = {"less_walking", "low walking load", "low walking", "wheelchair", "rest_friendly"}
        low_intensity_keywords = (
            "\u8f7b\u677e",
            "\u4f4e\u5f3a\u5ea6",
            "\u5c11\u8d70\u8def",
            "\u5c11\u6b65\u884c",
            "\u4f11\u606f\u70b9",
            "low intensity",
            "slow pace",
        )

        if "slow" in style_tokens:
            return 2
        if mobility_tokens & low_intensity_mobility:
            return 2
        if "family" in companion_tokens and any(keyword in extra_text for keyword in low_intensity_keywords):
            return 2
        return 3

    def _pick_day_attractions(self, attractions: List[Attraction], day_index: int, request) -> List[Attraction]:
        if not attractions:
            return []
        target_count = self._daily_attraction_target_count(request)
        start = (day_index * target_count) % len(attractions)
        selection = attractions[start : start + target_count]
        if len(selection) < target_count:
            selection.extend(attractions[: target_count - len(selection)])
        return selection

    def _build_default_attractions(self, city: str, travel_days: int, request=None) -> List[Attraction]:
        target_count = self._daily_attraction_target_count(request) if request is not None else 3
        count = max(target_count, travel_days * target_count)
        return [
            Attraction(
                name=f"{city}\u7cbe\u9009\u666f\u70b9 {index + 1}",
                address=city,
                location=Location(longitude=116.40 + 0.01 * index, latitude=39.90 + 0.01 * index),
                visit_duration=120,
                description=(
                    f"\u8fd9\u662f {city} \u7684\u7cbe\u9009\u5019\u9009\u666f\u70b9\uff0c\u9002\u5408\u4f5c\u4e3a\u5f53\u5929\u6838\u5fc3\u6e38\u89c8\u5185\u5bb9\u3002"
                    f"\u5efa\u8bae\u91cd\u70b9\u5173\u6ce8\u5f53\u5730\u4ee3\u8868\u6027\u98ce\u8c8c\u3001\u9002\u5408\u62cd\u7167\u6216\u6162\u901b\u7684\u533a\u57df\uff0c\u5e76\u9884\u7559\u4e24\u5c0f\u65f6\u5de6\u53f3\u6e38\u89c8\u65f6\u95f4\u3002"
                ),
                category="\u666f\u70b9",
                ticket_price=50,
            )
            for index in range(count)
        ]
