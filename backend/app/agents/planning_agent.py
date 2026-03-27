"""LLM-backed planning agent that turns structured context into a TripPlan."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from hello_agents import SimpleAgent

from ..models.agent_schemas import AgentExecutionStatus, PlanningAgentInput, PlanningAgentOutput
from ..models.schemas import Attraction, Budget, DayPlan, Hotel, Location, Meal, TripPlan, WeatherInfo
from ..services.llm_service import get_llm

logger = logging.getLogger(__name__)

PLANNER_AGENT_PROMPT = """
You are a travel itinerary planner.
You receive structured attraction, hotel, weather, profile, memory and RAG context.
Your job is only to generate a JSON object for the final trip plan.

Rules:
1. Return JSON only. No markdown, no prose before or after JSON.
2. Keep the response compatible with this schema:
{
  "city": "string",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "string",
      "transportation": "string",
      "accommodation": "string",
      "hotel": {
        "name": "string",
        "address": "string",
        "price_range": "string",
        "rating": "string",
        "distance": "string",
        "type": "string",
        "estimated_cost": 0
      },
      "attractions": [],
      "meals": []
    }
  ],
  "weather_info": [],
  "overall_suggestions": "string",
  "budget": {
    "total_attractions": 0,
    "total_hotels": 0,
    "total_meals": 0,
    "total_transportation": 0,
    "total": 0
  }
}
3. Use only the provided structured context. Do not invent new cities or dates.
4. Each day should include 2-3 attractions, 3 meals, and one hotel recommendation when available.
5. Respect weather advice, mobility needs, and budget level.
"""


class PlanningAgent:
    def __init__(self, planner_runner: Any | None = None) -> None:
        self.tools = ["llm_service"]
        self.planner_runner = planner_runner or SimpleAgent(
            name="planning-agent",
            llm=get_llm(),
            system_prompt=PLANNER_AGENT_PROMPT,
        )

    def list_tools(self) -> List[str]:
        return list(self.tools)

    async def execute(self, payload: PlanningAgentInput) -> PlanningAgentOutput:
        prompt = self._build_prompt(payload)
        try:
            raw_response = await asyncio.to_thread(self.planner_runner.run, prompt)
            trip_plan = self._parse_response(raw_response, payload)
            return PlanningAgentOutput(
                status=AgentExecutionStatus(success=True, degraded=False, warnings=[]),
                trip_plan=trip_plan,
                raw_response=str(raw_response),
            )
        except Exception as exc:  # pragma: no cover - LLM external dependency
            warning = f"Planning agent fell back to deterministic plan: {exc}"
            logger.warning(warning)
            trip_plan = self.build_fallback_plan(payload)
            return PlanningAgentOutput(
                status=AgentExecutionStatus(success=False, degraded=True, warnings=[warning], error=str(exc)),
                trip_plan=trip_plan,
                raw_response=None,
            )

    def build_fallback_plan(self, payload: PlanningAgentInput) -> TripPlan:
        request = payload.request
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        hotel = payload.hotel_result.hotels[0] if payload.hotel_result.hotels else None
        weather_info = payload.weather_result.weather_info or []
        suggestions = list(payload.weather_result.suggestions)
        suggestions.extend(payload.supervisor_warnings[:2])
        suggestions = [item for item in suggestions if item]

        days: List[DayPlan] = []
        attractions_pool = payload.attraction_result.attractions or self._build_default_attractions(request.city, request.travel_days)

        for day_index in range(request.travel_days):
            date_text = (start_date + timedelta(days=day_index)).strftime("%Y-%m-%d")
            day_attractions = self._pick_day_attractions(attractions_pool, day_index)
            meals = self._build_default_meals(request)
            days.append(
                DayPlan(
                    date=date_text,
                    day_index=day_index,
                    description=f"Day {day_index + 1} focuses on accessible highlights in {request.city}.",
                    transportation=request.transportation,
                    accommodation=hotel.name if hotel else request.accommodation,
                    hotel=hotel,
                    attractions=day_attractions,
                    meals=meals,
                )
            )

        budget = self._build_budget(days)
        overall_suggestions = " ".join(
            suggestions
            or [
                f"This fallback itinerary covers {request.city} for {request.travel_days} day(s).",
                "Confirm opening hours and live weather before departure.",
            ]
        )
        return TripPlan(
            city=request.city,
            start_date=request.start_date,
            end_date=request.end_date,
            days=days,
            weather_info=weather_info,
            overall_suggestions=overall_suggestions,
            budget=budget,
            recommendation_reasons=payload.recommendation_reasons,
        )

    def _build_prompt(self, payload: PlanningAgentInput) -> str:
        structured_context = {
            "trip_request": payload.request.model_dump(),
            "profile_context": payload.profile_context,
            "memory_context": payload.memory_context,
            "rag_context": payload.rag_context,
            "recommendation_reasons": [reason.model_dump() for reason in payload.recommendation_reasons],
            "weather": {
                "summary": payload.weather_result.summary,
                "suggestions": payload.weather_result.suggestions,
                "weather_info": [item.model_dump() for item in payload.weather_result.weather_info],
            },
            "attractions": [item.model_dump() for item in payload.attraction_result.attractions],
            "hotels": [item.model_dump() for item in payload.hotel_result.hotels],
            "warnings": payload.supervisor_warnings,
        }
        context_json = json.dumps(structured_context, ensure_ascii=False, indent=2)
        return f"Generate a trip plan from this structured context:\n{context_json}"

    def _parse_response(self, response: Any, payload: PlanningAgentInput) -> TripPlan:
        json_str = self._extract_json(str(response))
        data = json.loads(json_str)
        if not isinstance(data, dict):
            raise ValueError("Planner response root must be an object")
        normalized = self._normalize_plan_data(data, payload)
        return TripPlan(**normalized)

    @staticmethod
    def _extract_json(response: str) -> str:
        if "```json" in response:
            start = response.find("```json") + len("```json")
            end = response.find("```", start)
            return response[start:end].strip()
        if "```" in response:
            start = response.find("```") + len("```")
            end = response.find("```", start)
            return response[start:end].strip()

        start = response.find("{")
        end = response.rfind("}")
        if start >= 0 and end > start:
            return response[start : end + 1]
        raise ValueError("No JSON object found in planning response")

    def _normalize_plan_data(self, data: Dict[str, Any], payload: PlanningAgentInput) -> Dict[str, Any]:
        request = payload.request
        raw_days = data.get("days")
        if not isinstance(raw_days, list):
            raw_days = data.get("itinerary") if isinstance(data.get("itinerary"), list) else []

        hotel_candidates = payload.hotel_result.hotels
        attraction_candidates = payload.attraction_result.attractions
        days = [
            self._normalize_day(
                raw_day=raw_day,
                day_index=index,
                payload=payload,
                default_hotel=hotel_candidates[index % len(hotel_candidates)] if hotel_candidates else None,
                default_attractions=self._pick_day_attractions(attraction_candidates, index),
            )
            for index, raw_day in enumerate(raw_days)
        ]

        if not days:
            fallback = self.build_fallback_plan(payload)
            return fallback.model_dump()

        while len(days) < request.travel_days:
            index = len(days)
            days.append(
                self._normalize_day(
                    raw_day={},
                    day_index=index,
                    payload=payload,
                    default_hotel=hotel_candidates[index % len(hotel_candidates)] if hotel_candidates else None,
                    default_attractions=self._pick_day_attractions(attraction_candidates, index),
                )
            )

        days = days[: request.travel_days]
        budget = self._normalize_budget(data.get("budget"), days)
        weather_info = data.get("weather_info") if isinstance(data.get("weather_info"), list) else None
        weather_models = [
            WeatherInfo.model_validate(item)
            for item in weather_info
            if isinstance(item, dict)
        ] if weather_info else payload.weather_result.weather_info

        overall_suggestions = str(
            data.get("overall_suggestions")
            or data.get("summary")
            or payload.weather_result.summary
            or f"{request.city} {request.travel_days}-day itinerary."
        )

        return {
            "city": str(data.get("city") or request.city),
            "start_date": str(data.get("start_date") or request.start_date),
            "end_date": str(data.get("end_date") or request.end_date),
            "days": days,
            "weather_info": weather_models,
            "overall_suggestions": overall_suggestions,
            "budget": budget,
            "recommendation_reasons": payload.recommendation_reasons,
        }

    def _normalize_day(
        self,
        raw_day: Any,
        day_index: int,
        payload: PlanningAgentInput,
        default_hotel: Optional[Hotel],
        default_attractions: List[Attraction],
    ) -> DayPlan:
        request = payload.request
        day = raw_day if isinstance(raw_day, dict) else {}
        date_text = day.get("date")
        if not isinstance(date_text, str) or not date_text.strip():
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
            date_text = (start_date + timedelta(days=day_index)).strftime("%Y-%m-%d")

        attractions_raw = day.get("attractions") if isinstance(day.get("attractions"), list) else []
        if attractions_raw:
            attractions = [self._normalize_attraction(item, request.city) for item in attractions_raw]
        else:
            attractions = default_attractions or self._build_default_attractions(request.city, 1)[:2]
        attractions = self._enrich_attractions(attractions, default_attractions, request.city)

        meals_raw = day.get("meals") if isinstance(day.get("meals"), list) else []
        meals = [self._normalize_meal(item, index) for index, item in enumerate(meals_raw)]
        if len(meals) < 3:
            meals = self._merge_meals(meals, self._build_default_meals(request))
        meals = self._enrich_meals(meals, request)

        hotel = self._normalize_hotel(day.get("hotel")) if isinstance(day.get("hotel"), dict) else default_hotel
        accommodation = str(day.get("accommodation") or (hotel.name if hotel else request.accommodation))

        return DayPlan(
            date=date_text,
            day_index=self._to_int(day.get("day_index"), day_index),
            description=str(day.get("description") or day.get("theme") or f"Day {day_index + 1} itinerary"),
            transportation=str(day.get("transportation") or request.transportation),
            accommodation=accommodation,
            hotel=hotel,
            attractions=attractions,
            meals=meals,
        )

    def _enrich_attractions(
        self,
        attractions: List[Attraction],
        defaults: List[Attraction],
        city: str,
    ) -> List[Attraction]:
        fallback_map = {item.name.strip().lower(): item for item in defaults if item.name.strip()}
        enriched: List[Attraction] = []

        for attraction in attractions:
            fallback = fallback_map.get(attraction.name.strip().lower())
            description = attraction.description.strip()
            if not description and fallback and fallback.description.strip():
                description = fallback.description.strip()
            if not description:
                description = (
                    f"{attraction.name} is a recommended stop in {city}, suitable for a "
                    f"{max(30, attraction.visit_duration)} minute visit."
                )

            enriched.append(
                attraction.model_copy(
                    update={
                        "description": description,
                        "address": attraction.address or (fallback.address if fallback else city),
                    }
                )
            )

        return enriched

    def _enrich_meals(self, meals: List[Meal], request) -> List[Meal]:
        defaults_by_type = {meal.type: meal for meal in self._build_default_meals(request)}
        enriched: List[Meal] = []

        for meal in meals[:3]:
            fallback = defaults_by_type.get(meal.type)
            name = meal.name.strip()
            if not name or name.endswith("recommendation"):
                name = fallback.name if fallback else f"{meal.type.title()} in {request.city}"

            description = (meal.description or "").strip()
            if not description:
                description = fallback.description if fallback else f"A {meal.type} option in {request.city}."

            estimated_cost = meal.estimated_cost or (fallback.estimated_cost if fallback else 0)
            enriched.append(
                meal.model_copy(
                    update={
                        "name": name,
                        "description": description,
                        "estimated_cost": estimated_cost,
                    }
                )
            )

        return enriched

    def _normalize_attraction(self, raw_item: Any, city: str) -> Attraction:
        item = raw_item if isinstance(raw_item, dict) else {}
        location = self._normalize_location(item.get("location"), city)
        return Attraction(
            name=str(item.get("name") or item.get("title") or "Recommended attraction"),
            address=str(item.get("address") or city),
            location=location,
            visit_duration=self._parse_visit_duration(item.get("visit_duration")),
            description=str(item.get("description") or item.get("reason") or ""),
            category=str(item.get("category") or "attraction"),
            ticket_price=self._to_int(item.get("ticket_price") or item.get("price"), 0),
            poi_id=str(item.get("poi_id") or item.get("id") or ""),
        )

    def _normalize_meal(self, raw_item: Any, index: int) -> Meal:
        item = raw_item if isinstance(raw_item, dict) else {}
        default_types = ["breakfast", "lunch", "dinner"]
        meal_type = str(item.get("type") or default_types[min(index, 2)])
        return Meal(
            type=meal_type,
            name=str(item.get("name") or item.get("suggestion") or f"{meal_type} recommendation"),
            address=str(item.get("address")) if item.get("address") else None,
            location=self._maybe_location(item.get("location")),
            description=str(item.get("description") or item.get("suggestion") or ""),
            estimated_cost=self._to_int(item.get("estimated_cost"), 0),
        )

    def _normalize_hotel(self, raw_item: Any) -> Optional[Hotel]:
        item = raw_item if isinstance(raw_item, dict) else {}
        name = str(item.get("name") or "").strip()
        if not name:
            return None
        return Hotel(
            name=name,
            address=str(item.get("address") or ""),
            location=self._maybe_location(item.get("location")),
            price_range=str(item.get("price_range") or ""),
            rating=str(item.get("rating") or ""),
            distance=str(item.get("distance") or ""),
            type=str(item.get("type") or ""),
            estimated_cost=self._to_int(item.get("estimated_cost"), 0),
        )

    def _normalize_budget(self, raw_budget: Any, days: List[DayPlan]) -> Budget:
        if isinstance(raw_budget, dict):
            total_attractions = self._to_int(raw_budget.get("total_attractions"), 0)
            total_hotels = self._to_int(raw_budget.get("total_hotels"), 0)
            total_meals = self._to_int(raw_budget.get("total_meals"), 0)
            total_transportation = self._to_int(raw_budget.get("total_transportation"), 0)
            total = self._to_int(
                raw_budget.get("total"),
                total_attractions + total_hotels + total_meals + total_transportation,
            )
            return Budget(
                total_attractions=total_attractions,
                total_hotels=total_hotels,
                total_meals=total_meals,
                total_transportation=total_transportation,
                total=total,
            )
        return self._build_budget(days)

    def _build_budget(self, days: List[DayPlan]) -> Budget:
        total_attractions = sum(attraction.ticket_price for day in days for attraction in day.attractions)
        total_hotels = sum((day.hotel.estimated_cost if day.hotel else 0) for day in days)
        total_meals = sum(meal.estimated_cost for day in days for meal in day.meals)
        total_transportation = max(0, len(days) * 40)
        total = total_attractions + total_hotels + total_meals + total_transportation
        return Budget(
            total_attractions=total_attractions,
            total_hotels=total_hotels,
            total_meals=total_meals,
            total_transportation=total_transportation,
            total=total,
        )

    def _pick_day_attractions(self, attractions: List[Attraction], day_index: int) -> List[Attraction]:
        if not attractions:
            return []
        start = (day_index * 2) % len(attractions)
        selection = attractions[start : start + 2]
        if len(selection) < 2:
            selection.extend(attractions[: 2 - len(selection)])
        return selection

    def _build_default_attractions(self, city: str, travel_days: int) -> List[Attraction]:
        count = max(2, travel_days * 2)
        return [
            Attraction(
                name=f"{city} highlight {index + 1}",
                address=city,
                location=Location(longitude=116.40 + 0.01 * index, latitude=39.90 + 0.01 * index),
                visit_duration=120,
                description=f"Fallback attraction candidate in {city}.",
                category="attraction",
                ticket_price=50,
            )
            for index in range(count)
        ]

    def _build_default_meals(self, request) -> List[Meal]:
        budget = request.budget_level or "medium"
        base_cost = {"low": 30, "medium": 60, "high": 120}.get(budget, 60)
        return [
            Meal(type="breakfast", name="Local breakfast", description="Simple breakfast near the first stop.", estimated_cost=base_cost // 2),
            Meal(type="lunch", name="Regional lunch", description="Lunch close to the midday attraction.", estimated_cost=base_cost),
            Meal(type="dinner", name="Relaxed dinner", description="Dinner near the hotel area.", estimated_cost=base_cost + 20),
        ]

    def _merge_meals(self, current: List[Meal], defaults: List[Meal]) -> List[Meal]:
        existing_types = {meal.type for meal in current}
        merged = list(current)
        for meal in defaults:
            if meal.type not in existing_types:
                merged.append(meal)
        return merged[:3]

    def _normalize_location(self, raw_location: Any, city: str) -> Location:
        if isinstance(raw_location, dict):
            lng = raw_location.get("longitude", raw_location.get("lng", raw_location.get("lon", 116.40)))
            lat = raw_location.get("latitude", raw_location.get("lat", 39.90))
            return Location(longitude=self._to_float(lng, 116.40), latitude=self._to_float(lat, 39.90))

        if isinstance(raw_location, str) and "," in raw_location:
            lng_text, lat_text = [item.strip() for item in raw_location.split(",", 1)]
            return Location(longitude=self._to_float(lng_text, 116.40), latitude=self._to_float(lat_text, 39.90))

        city_defaults = {
            "beijing": (116.40, 39.90),
            "shanghai": (121.47, 31.23),
        }
        longitude, latitude = city_defaults.get(city.lower(), (116.40, 39.90))
        return Location(longitude=longitude, latitude=latitude)

    def _maybe_location(self, raw_location: Any) -> Optional[Location]:
        if raw_location is None:
            return None
        if isinstance(raw_location, dict):
            longitude = raw_location.get("longitude", raw_location.get("lng", raw_location.get("lon")))
            latitude = raw_location.get("latitude", raw_location.get("lat"))
            if longitude is None or latitude is None:
                return None
            return Location(longitude=self._to_float(longitude, 0.0), latitude=self._to_float(latitude, 0.0))
        if isinstance(raw_location, str) and "," in raw_location:
            longitude, latitude = [item.strip() for item in raw_location.split(",", 1)]
            return Location(longitude=self._to_float(longitude, 0.0), latitude=self._to_float(latitude, 0.0))
        return None

    def _parse_visit_duration(self, value: Any) -> int:
        if isinstance(value, (int, float)):
            return max(30, int(value))
        if isinstance(value, str):
            numbers = re.findall(r"\d+(?:\.\d+)?", value)
            if numbers:
                amount = float(numbers[0])
                if "hour" in value.lower() or "小时" in value or value.lower().endswith("h"):
                    return max(30, int(amount * 60))
                return max(30, int(amount))
        return 120

    @staticmethod
    def _to_int(value: Any, default: int) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            numbers = re.findall(r"-?\d+", value)
            if numbers:
                return int(numbers[0])
        return default

    @staticmethod
    def _to_float(value: Any, default: float) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            numbers = re.findall(r"-?\d+(?:\.\d+)?", value)
            if numbers:
                return float(numbers[0])
        return default
