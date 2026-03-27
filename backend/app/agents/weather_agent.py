"""Structured weather retrieval agent."""

from __future__ import annotations

import asyncio
import logging
from typing import List

from ..models.agent_schemas import AgentExecutionStatus, WeatherAgentInput, WeatherAgentOutput
from ..models.schemas import WeatherInfo
from ..services.amap_service import AmapService, get_amap_service

logger = logging.getLogger(__name__)


class WeatherAgent:
    def __init__(self, amap_service: AmapService | None = None) -> None:
        self.amap_service = amap_service or get_amap_service()
        self.tools = ["amap_service.get_weather"]

    def list_tools(self) -> List[str]:
        return list(self.tools)

    async def execute(self, payload: WeatherAgentInput) -> WeatherAgentOutput:
        try:
            weather_info = await asyncio.to_thread(self.amap_service.get_weather, payload.request.city)
            suggestions = self._build_suggestions(weather_info)
            summary = self._build_summary(payload.request.city, weather_info, suggestions)
            degraded = not weather_info
            warnings = [] if weather_info else ["Weather service returned no structured data"]
            return WeatherAgentOutput(
                status=AgentExecutionStatus(
                    success=bool(weather_info),
                    degraded=degraded,
                    warnings=warnings,
                    error=warnings[0] if warnings else None,
                ),
                weather_info=weather_info,
                summary=summary,
                suggestions=suggestions,
            )
        except Exception as exc:  # pragma: no cover - external dependency
            warning = f"Weather lookup failed: {exc}"
            logger.warning(warning)
            return WeatherAgentOutput(
                status=AgentExecutionStatus(success=False, degraded=True, warnings=[warning], error=warning),
                weather_info=[],
                summary="Weather information is unavailable. Use a flexible schedule.",
                suggestions=["Keep an indoor backup option and confirm conditions before departure."],
            )

    def _build_summary(self, city: str, weather_info: List[WeatherInfo], suggestions: List[str]) -> str:
        if not weather_info:
            return f"{city} weather is unavailable."

        first = weather_info[0]
        return (
            f"{city} weather starts with {first.day_weather or 'unknown'} "
            f"{first.day_temp}°C/{first.night_temp}°C. "
            + " ".join(suggestions[:2])
        ).strip()

    def _build_suggestions(self, weather_info: List[WeatherInfo]) -> List[str]:
        suggestions: List[str] = []
        if not weather_info:
            return suggestions

        first = weather_info[0]
        condition_text = f"{first.day_weather} {first.night_weather}"

        if any(token in condition_text for token in ("雨", "snow", "storm", "雷", "雨夹雪")):
            suggestions.append("Prefer indoor attractions and leave extra transit buffer for wet weather.")
        if any(token in condition_text for token in ("晴", "sun", "多云")):
            suggestions.append("Outdoor stops are feasible, but avoid midday heat if the schedule is dense.")
        if first.day_temp >= 30:
            suggestions.append("Schedule intensive walking in the morning or evening and keep hydration breaks.")
        if first.day_temp <= 5:
            suggestions.append("Prioritize indoor breaks and shorter outdoor stays in cold conditions.")
        if first.wind_power and any(token in str(first.wind_power) for token in ("5", "6", "7", "8")):
            suggestions.append("Strong wind may affect riverside or open-area visits.")

        if not suggestions:
            suggestions.append("Weather impact is limited. Keep the itinerary flexible for day-of adjustments.")
        return suggestions
