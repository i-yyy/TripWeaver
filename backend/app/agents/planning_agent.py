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
from ..models.skill_schemas import SelectedSkill, ValidationResult
from ..services.amap_service import get_amap_service
from ..services.llm_service import get_llm
from ..services.plan_constraint_validator import PlanConstraintValidator, get_plan_constraint_validator

logger = logging.getLogger(__name__)

PLANNER_AGENT_PROMPT = """
你是一名专业旅行规划助手。
你会收到结构化的景点、酒店、天气、用户画像、记忆和 RAG 上下文。
你的任务是只返回最终 trip plan 的 JSON 对象。

规则：
1. 只能返回 JSON。不要返回 Markdown，不要在 JSON 前后添加任何解释。
2. 所有可读文本字段必须使用简体中文，包括城市说明、景点描述、餐饮描述、交通说明、住宿说明、整体建议。
3. 除非是官方专有名称，否则不要输出英文；如果输入上下文里有英文名称，优先转换为自然中文表达。
4. 严格兼容以下结构：
{
  "city": "中文城市名",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "中文详细日程概述",
      "transportation": "中文交通方式",
      "transportation_detail": "中文交通安排说明，需说明为什么这样安排",
      "transportation_cost": 0,
      "accommodation": "中文住宿说明",
      "route_summary": "中文路线摘要，说明先后顺序与衔接逻辑",
      "hotel": {
        "name": "中文酒店名称",
        "address": "中文地址",
        "price_range": "价格等级",
        "rating": "评分或口碑",
        "distance": "距离说明",
        "type": "酒店类型",
        "estimated_cost": 0
      },
      "attractions": [
        {
          "name": "中文景点名",
          "address": "中文地址",
          "visit_duration": 120,
          "description": "80-160字中文描述，至少包含核心看点、适合原因、建议时长、最佳游览时段或注意事项",
          "category": "景点分类",
          "ticket_price": 0
        }
      ],
      "meals": [
        {
          "type": "breakfast/lunch/dinner",
          "name": "中文餐饮建议",
          "description": "中文说明吃什么，以及为什么这样安排，需结合当天景点、时段、预算或当地特色",
          "estimated_cost": 0
        }
      ]
    }
  ],
  "weather_info": [],
  "overall_suggestions": "中文整体建议",
  "budget": {
    "total_attractions": 0,
    "total_hotels": 0,
    "total_meals": 0,
    "total_transportation": 0,
    "total": 0
  }
}
5. 只能使用提供的结构化上下文，不要编造新的城市、日期、酒店或景点。
6. 每天包含 2-3 个景点、3 餐、1 个酒店建议。
7. 景点、酒店、餐饮、交通都尽量给出价格或费用估算，不要留空。
8. 景点描述不能空泛，禁止使用“适合作为候选景点”“值得一去”等无信息量表达作为主体内容。
9. 餐饮描述必须回答两个问题：吃什么、为什么吃。
10. 必须结合天气建议、行动需求、预算等级和陪同人群。
"""


class PlanningAgent:
    def __init__(
        self,
        planner_runner: Any | None = None,
        constraint_validator: PlanConstraintValidator | None = None,
    ) -> None:
        self.tools = ["llm_service"]
        self.planner_runner = planner_runner or SimpleAgent(
            name="planning-agent",
            llm=get_llm(),
            system_prompt=PLANNER_AGENT_PROMPT,
        )
        self.constraint_validator = constraint_validator or get_plan_constraint_validator()

    def list_tools(self) -> List[str]:
        return list(self.tools)

    async def execute(self, payload: PlanningAgentInput) -> PlanningAgentOutput:
        prompt = self._build_prompt(payload)
        try:
            raw_response = await asyncio.to_thread(self.planner_runner.run, prompt)
            trip_plan = self._parse_response(raw_response, payload)
            trip_plan = await self._safe_enrich_plan(trip_plan, payload)
            trip_plan, validation = await self._validate_plan(trip_plan, payload)
            warnings = self._validation_messages(validation)
            return PlanningAgentOutput(
                status=AgentExecutionStatus(
                    success=not bool(validation.errors),
                    degraded=bool(warnings),
                    warnings=warnings,
                    error=validation.errors[0].message if validation.errors else None,
                ),
                trip_plan=trip_plan,
                raw_response=str(raw_response),
            )
        except Exception as exc:  # pragma: no cover - LLM external dependency
            warning = f"Planning agent fell back to deterministic plan: {exc}"
            logger.warning(warning)
            trip_plan = self.build_fallback_plan(payload)
            trip_plan = await self._safe_enrich_plan(trip_plan, payload)
            trip_plan, validation = await self._validate_plan(trip_plan, payload)
            validation_messages = self._validation_messages(validation)
            return PlanningAgentOutput(
                status=AgentExecutionStatus(
                    success=False,
                    degraded=True,
                    warnings=[warning] + validation_messages,
                    error=str(exc) if not validation.errors else validation.errors[0].message,
                ),
                trip_plan=trip_plan,
                raw_response=None,
            )

    async def _safe_enrich_plan(self, trip_plan: TripPlan, payload: PlanningAgentInput) -> TripPlan:
        try:
            return await asyncio.to_thread(self._enrich_trip_plan, trip_plan, payload)
        except Exception as exc:  # pragma: no cover - external dependency
            logger.warning("Trip plan enrichment failed: %s", exc)
            return trip_plan

    async def _validate_plan(
        self,
        trip_plan: TripPlan,
        payload: PlanningAgentInput,
    ) -> tuple[TripPlan, ValidationResult]:
        return await asyncio.to_thread(
            self.constraint_validator.validate_and_repair,
            payload.request,
            payload.skills,
            trip_plan,
            payload.weather_result,
        )

    @staticmethod
    def _validation_messages(validation: ValidationResult) -> List[str]:
        return [issue.message for issue in [*validation.warnings, *validation.errors]]

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
                    description=f"第{day_index + 1}天以{request.city}的核心看点为主，安排舒适且便于衔接的游览节奏。",
                    transportation=request.transportation,
                    transportation_detail=self._default_transportation_detail(request, day_attractions, hotel),
                    transportation_cost=self._estimate_transportation_cost(request.transportation, day_attractions),
                    accommodation=hotel.name if hotel else request.accommodation,
                    hotel=hotel,
                    attractions=day_attractions,
                    meals=meals,
                    route_summary=self._build_route_summary(day_attractions, request.transportation),
                )
            )

        budget = self._build_budget(days)
        overall_suggestions = " ".join(
            suggestions
            or [
                f"这份备选行程覆盖{request.city}{request.travel_days}天的核心安排。",
                "出发前请确认开放时间、实时天气以及交通情况。",
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
            applied_skills=payload.skills,
        )

    def _build_prompt(self, payload: PlanningAgentInput) -> str:
        skill_block = self._build_skill_prompt_block(payload.skills)
        structured_context = {
            "trip_request": payload.request.model_dump(),
            "profile_context": payload.profile_context,
            "memory_context": payload.memory_context,
            "rag_context": payload.rag_context,
            "recommendation_reasons": [reason.model_dump() for reason in payload.recommendation_reasons],
            "skills": [self._skill_prompt_item(skill) for skill in payload.skills],
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
        return (
            "请基于以下结构化上下文生成中文旅行计划 JSON。"
            "再次强调：只能输出 JSON，所有说明必须使用简体中文。\n"
            "Keep the existing poi_id for attractions from context whenever available. Do not invent or drop poi_id, image_url, photos, image_source, image_status, or map_image_url when reusing a provided attraction.\n"
            f"{skill_block}{context_json}"
        )

    @staticmethod
    def _skill_prompt_item(skill: SelectedSkill) -> Dict[str, Any]:
        return {
            "key": skill.key,
            "name": skill.name,
            "layer": skill.layer,
            "category": skill.category,
            "source": skill.source,
            "matched_fields": list(skill.matched_fields),
            "matched_terms": list(skill.matched_terms),
            "reasons": list(skill.reasons),
            "hard_rules": list(skill.hard_rules),
            "soft_rules": list(skill.soft_rules),
            "meal_rules": list(skill.meal_rules),
            "routing_rules": list(skill.routing_rules),
            "planning_rules": list(skill.planning_rules),
            "output_hints": list(skill.output_hints),
        }

    def _build_skill_prompt_block(self, skills: List[SelectedSkill]) -> str:
        if not skills:
            return ""

        lines = ["Enabled skills. Follow hard constraints first, then style preferences:"]
        for skill in skills:
            lines.append(f"- {skill.name} ({skill.key}, {skill.layer}, {skill.category})")
            for rule in skill.hard_rules:
                lines.append(f"  * hard: {rule}")
            for rule in skill.soft_rules:
                lines.append(f"  * soft: {rule}")
            for rule in skill.meal_rules:
                lines.append(f"  * meal: {rule}")
            for rule in skill.routing_rules:
                lines.append(f"  * routing: {rule}")
            if not any([skill.hard_rules, skill.soft_rules, skill.meal_rules, skill.routing_rules]):
                for rule in skill.planning_rules:
                    lines.append(f"  * rule: {rule}")
        lines.append("")
        return "\n".join(lines)

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
            or f"{request.city}{request.travel_days}天行程建议。"
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
            "applied_skills": payload.skills,
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
            attractions = [
                self._normalize_attraction_with_fallback(item, request.city, default_attractions)
                for item in attractions_raw
            ]
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
        transportation = str(day.get("transportation") or request.transportation)
        transportation_detail = str(
            day.get("transportation_detail")
            or day.get("transportation_reason")
            or self._default_transportation_detail(request, attractions, hotel)
        )
        transportation_cost = self._to_int(
            day.get("transportation_cost"),
            self._estimate_transportation_cost(transportation, attractions),
        )
        route_summary = str(day.get("route_summary") or self._build_route_summary(attractions, transportation))

        return DayPlan(
            date=date_text,
            day_index=self._to_int(day.get("day_index"), day_index),
            description=str(day.get("description") or day.get("theme") or f"第{day_index + 1}天行程安排"),
            transportation=transportation,
            transportation_detail=transportation_detail,
            transportation_cost=transportation_cost,
            accommodation=accommodation,
            hotel=hotel,
            attractions=attractions,
            meals=meals,
            route_summary=route_summary,
            route_map_url=str(day.get("route_map_url") or "") or None,
        )

    def _enrich_attractions(
        self,
        attractions: List[Attraction],
        defaults: List[Attraction],
        city: str,
    ) -> List[Attraction]:
        enriched: List[Attraction] = []

        for attraction in attractions:
            fallback = self._match_attraction_fallback(attraction.name, attraction.address, defaults)
            description = attraction.description.strip()
            if not description and fallback and fallback.description.strip():
                description = fallback.description.strip()
            if not description:
                description = (
                    f"{attraction.name}位于{attraction.address or city}，适合作为当天行程的重要一站。"
                    f"核心看点包括当地代表性景观与适合拍照或慢逛的区域，建议停留"
                    f"{max(30, attraction.visit_duration)}分钟，并尽量避开最拥挤的时段前往。"
                )

            enriched.append(
                attraction.model_copy(
                    update={
                        "description": description,
                        "address": attraction.address or (fallback.address if fallback else city),
                        "poi_id": attraction.poi_id or (fallback.poi_id if fallback else ""),
                        "photos": list(attraction.photos or (fallback.photos if fallback else []) or []),
                        "image_url": attraction.image_url or (fallback.image_url if fallback else None),
                        "image_source": attraction.image_source or (fallback.image_source if fallback else None),
                        "image_status": attraction.image_status or (fallback.image_status if fallback else None),
                        "map_image_url": attraction.map_image_url or (fallback.map_image_url if fallback else None),
                    }
                )
            )

        return enriched

    def _enrich_meals(self, meals: List[Meal], request) -> List[Meal]:
        defaults_by_type = {meal.type: meal for meal in self._build_default_meals(request)}
        enriched: List[Meal] = []

        for meal in meals[:3]:
            fallback = defaults_by_type.get(meal.type) or self._build_meal_template(request, meal.type)
            name = meal.name.strip()
            if self._is_generic_meal_name(name, meal.type):
                name = fallback.name

            description = (meal.description or "").strip()
            if not description or self._is_generic_meal_description(description):
                description = fallback.description

            estimated_cost = meal.estimated_cost or fallback.estimated_cost
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

    @staticmethod
    def _normalize_photo_urls(raw_photos: Any) -> List[str]:
        if not isinstance(raw_photos, list):
            return []

        normalized: List[str] = []
        seen: set[str] = set()
        for item in raw_photos:
            if isinstance(item, dict):
                url = item.get("url") or item.get("image") or item.get("src")
            else:
                url = item
            text = str(url or "").strip()
            if not text or text in seen or PlanningAgent._is_map_like_image_url(text):
                continue
            seen.add(text)
            normalized.append(text)
        return normalized

    @staticmethod
    def _is_map_like_image_url(url: Any) -> bool:
        text = str(url or "").strip().lower()
        if not text:
            return False
        return (
            text.startswith("map:")
            or "/v3/staticmap" in text
            or "restapi.amap.com/v3/staticmap" in text
            or "webapi.amap.com/maps/staticmap" in text
        )

    @classmethod
    def _dedupe_real_image_urls(cls, raw_urls: List[Any]) -> List[str]:
        normalized: List[str] = []
        seen: set[str] = set()
        for item in raw_urls:
            text = str(item or "").strip()
            if not text or text in seen or cls._is_map_like_image_url(text):
                continue
            seen.add(text)
            normalized.append(text)
        return normalized

    def _resolve_attraction_media(
        self,
        amap_service,
        attraction: Attraction,
        city: str,
    ) -> tuple[Optional[str], List[str], Optional[str], str]:
        photos = self._dedupe_real_image_urls(list(attraction.photos or []))
        amap_photos: List[str] = []

        if attraction.poi_id:
            try:
                amap_photos = self._dedupe_real_image_urls(list(amap_service.get_poi_photo_urls(attraction.poi_id)))
                photos = self._dedupe_real_image_urls([*amap_photos, *photos])
            except Exception as exc:
                logger.debug("AMap POI photo lookup failed poi_id=%s error=%s", attraction.poi_id, exc)

        image_candidates = [*amap_photos]
        if attraction.image_url:
            image_candidates.append(attraction.image_url)
        image_candidates.extend(photos)
        image_candidates = self._dedupe_real_image_urls(image_candidates)
        image_url = next((item for item in image_candidates if item), None)

        if image_url:
            photos = self._dedupe_real_image_urls([image_url, *photos])
            image_source = "amap" if image_url in amap_photos else attraction.image_source or "provided"
            return image_url, photos, image_source, "ok"

        return None, photos, None, "missing"

    def _normalize_attraction_with_fallback(
        self,
        raw_item: Any,
        city: str,
        fallback_attractions: Optional[List[Attraction]] = None,
    ) -> Attraction:
        item = raw_item if isinstance(raw_item, dict) else {}
        name = str(item.get("name") or item.get("title") or "推荐景点")
        address = str(item.get("address") or city)
        fallback = self._match_attraction_fallback(name, address, fallback_attractions or [])
        location = self._resolve_attraction_location(
            raw_location=item.get("location"),
            name=name,
            address=address,
            city=city,
            fallback=fallback,
        )
        return Attraction(
            name=name,
            address=address,
            location=location,
            visit_duration=self._parse_visit_duration(item.get("visit_duration")),
            description=str(item.get("description") or item.get("reason") or ""),
            category=str(item.get("category") or "景点"),
            photos=self._normalize_photo_urls(item.get("photos")),
            image_url=next(
                iter(
                    self._dedupe_real_image_urls(
                        [item.get("image_url"), fallback.image_url if fallback else None]
                    )
                ),
                None,
            ),
            image_source=str(item.get("image_source") or "") or (fallback.image_source if fallback else None),
            image_status=str(item.get("image_status") or "") or (fallback.image_status if fallback else None),
            map_image_url=str(item.get("map_image_url") or "") or None,
            ticket_price=self._to_int(item.get("ticket_price") or item.get("price"), 0),
            poi_id=str(item.get("poi_id") or item.get("id") or (fallback.poi_id if fallback else "") or ""),
        )

    def _resolve_attraction_location(
        self,
        raw_location: Any,
        name: str,
        address: str,
        city: str,
        fallback: Optional[Attraction],
    ) -> Location:
        location = self._maybe_location(raw_location)
        if location is not None:
            return location

        if fallback and fallback.location:
            return fallback.location

        amap_service = get_amap_service()
        for candidate in [address, f"{city}{name}" if city and name else "", name]:
            compact = str(candidate or "").strip()
            if not compact:
                continue
            try:
                location = amap_service.geocode(compact, city or None)
            except Exception as exc:
                logger.debug("Attraction geocode failed name=%s city=%s candidate=%s error=%s", name, city, compact, exc)
                location = None
            if location is not None:
                return location

        try:
            city_location = amap_service.geocode_city_http(city)
        except Exception as exc:
            logger.debug("City geocode fallback failed city=%s error=%s", city, exc)
            city_location = None
        if city_location is not None:
            return city_location

        return self._fallback_city_location(city)

    @staticmethod
    def _match_attraction_fallback(name: str, address: str, candidates: List[Attraction]) -> Optional[Attraction]:
        normalized_name = re.sub(r"[\s()（）,，、\\/_-]+", "", name).lower()
        normalized_address = re.sub(r"[\s()（）,，、\\/_-]+", "", address).lower()
        for candidate in candidates:
            candidate_name = re.sub(r"[\s()（）,，、\\/_-]+", "", candidate.name).lower()
            candidate_address = re.sub(r"[\s()（）,，、\\/_-]+", "", candidate.address).lower()
            if normalized_name and normalized_name == candidate_name:
                return candidate
            if normalized_address and normalized_address == candidate_address:
                return candidate
        for candidate in candidates:
            candidate_name = re.sub(r"[\s()（）,，、\\/_-]+", "", candidate.name).lower()
            candidate_address = re.sub(r"[\s()（）,，、\\/_-]+", "", candidate.address).lower()
            if normalized_name and candidate_name and min(len(normalized_name), len(candidate_name)) >= 4:
                if normalized_name in candidate_name or candidate_name in normalized_name:
                    return candidate
            if normalized_address and candidate_address and min(len(normalized_address), len(candidate_address)) >= 6:
                if normalized_address in candidate_address or candidate_address in normalized_address:
                    return candidate
        return None

    @staticmethod
    def _fallback_city_location(city: str) -> Location:
        city_defaults = {
            "beijing": (116.40, 39.90),
            "shanghai": (121.47, 31.23),
        }
        longitude, latitude = city_defaults.get(city.lower(), (104.195397, 35.86166))
        return Location(longitude=longitude, latitude=latitude)

    def _normalize_attraction(self, raw_item: Any, city: str) -> Attraction:
        item = raw_item if isinstance(raw_item, dict) else {}
        location = self._normalize_location(item.get("location"), city)
        return Attraction(
            name=str(item.get("name") or item.get("title") or "推荐景点"),
            address=str(item.get("address") or city),
            location=location,
            visit_duration=self._parse_visit_duration(item.get("visit_duration")),
            description=str(item.get("description") or item.get("reason") or ""),
            category=str(item.get("category") or "景点"),
            photos=self._normalize_photo_urls(item.get("photos")),
            image_url=next(iter(self._dedupe_real_image_urls([item.get("image_url")])), None),
            image_source=str(item.get("image_source") or "") or None,
            image_status=str(item.get("image_status") or "") or None,
            map_image_url=str(item.get("map_image_url") or "") or None,
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
            map_image_url=str(item.get("map_image_url") or "") or None,
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
        total_transportation = sum(day.transportation_cost for day in days)
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
                name=f"{city}精选景点{index + 1}",
                address=city,
                location=Location(longitude=116.40 + 0.01 * index, latitude=39.90 + 0.01 * index),
                visit_duration=120,
                description=(
                    f"这是{city}的精选候选景点，适合作为当日核心游览内容。"
                    f"建议重点关注当地代表性风貌、适合拍照或慢逛的区域，并预留两小时左右游览时间。"
                ),
                category="景点",
                ticket_price=50,
            )
            for index in range(count)
        ]

    def _build_default_meals(self, request) -> List[Meal]:
        budget = request.budget_level or "medium"
        base_cost = {"low": 30, "medium": 60, "high": 120}.get(budget, 60)
        return [
            self._build_meal_template(request, "breakfast", base_cost),
            self._build_meal_template(request, "lunch", base_cost),
            self._build_meal_template(request, "dinner", base_cost),
        ]

    def _merge_meals(self, current: List[Meal], defaults: List[Meal]) -> List[Meal]:
        existing_types = {meal.type for meal in current}
        merged = list(current)
        for meal in defaults:
            if meal.type not in existing_types:
                merged.append(meal)
        return merged[:3]

    def _build_meal_template(self, request, meal_type: str, base_cost: Optional[int] = None) -> Meal:
        if base_cost is None:
            budget = request.budget_level or "medium"
            base_cost = {"low": 30, "medium": 60, "high": 120}.get(budget, 60)

        dietary = {item.lower() for item in getattr(request, "dietary_restrictions", [])}
        default_name_map = {
            "breakfast": "包子、鸡蛋和豆浆",
            "lunch": "热汤面配小炒和米饭",
            "dinner": "招牌主菜配时蔬和米饭",
        }
        default_description_map = {
            "breakfast": "早餐建议吃包子、鸡蛋和豆浆，出餐快、饱腹稳定，方便上午景点前快速出发。",
            "lunch": "午餐建议点热汤面、小炒和米饭，吃什么明确，也方便继续下午行程。",
            "dinner": "晚餐建议吃一份招牌主菜、时蔬和米饭，正餐完整，适合一天结束后好好休息。",
        }

        if "vegetarian" in dietary:
            name_map = {
                "breakfast": "豆浆、素包子和白粥",
                "lunch": "菌菇面配清炒时蔬和豆腐",
                "dinner": "素馄饨配杂粮饭和时令蔬菜",
            }
            description_map = {
                "breakfast": "早餐建议吃豆浆、素包子和白粥，口味清爽、出发快，也能兼顾素食限制和上午行程节奏。",
                "lunch": "午餐建议点菌菇面、清炒时蔬和豆腐，既能吃得具体饱腹，也方便继续下午的游览安排，并符合素食要求。",
                "dinner": "晚餐建议吃素馄饨、杂粮饭和时令蔬菜，收尾更轻松，也能继续保持素食约束。",
            }
        elif "halal" in dietary:
            name_map = {
                "breakfast": "牛肉包、鸡蛋和豆浆",
                "lunch": "清真牛肉面配凉菜",
                "dinner": "手抓饭配烤羊肉和酸奶",
            }
            description_map = {
                "breakfast": "早餐建议吃牛肉包、鸡蛋和豆浆，出餐快、饱腹感强，也便于满足清真饮食要求。",
                "lunch": "午餐建议点清真牛肉面和凉菜，吃什么明确，补充体力也快，适合放在上午和下午景点之间。",
                "dinner": "晚餐建议吃手抓饭、烤羊肉和酸奶，既有完整正餐感，也更容易在收尾时兼顾清真要求和休息节奏。",
            }
        elif "no_spicy" in dietary:
            name_map = {
                "breakfast": "白粥、鸡蛋和鲜肉包",
                "lunch": "清汤面配白切鸡和时蔬",
                "dinner": "清蒸鱼配青菜和米饭",
            }
            description_map = {
                "breakfast": "早餐建议吃白粥、鸡蛋和鲜肉包，口味温和，不刺激，适合早点出发前先稳定补充能量。",
                "lunch": "午餐建议点清汤面、白切鸡和时蔬，吃得具体又不过辣，便于下午继续活动。",
                "dinner": "晚餐建议吃清蒸鱼、青菜和米饭，口味清淡、恢复感更强，也符合少辣或不辣的需求。",
            }
        else:
            name_map = default_name_map
            description_map = default_description_map

        cost_map = {
            "breakfast": max(12, base_cost // 2),
            "lunch": base_cost,
            "dinner": base_cost + 20,
            "snack": max(10, base_cost // 2),
        }
        return Meal(
            type=meal_type,
            name=name_map.get(meal_type, default_name_map["lunch"]),
            description=description_map.get(meal_type, default_description_map["lunch"]),
            estimated_cost=cost_map.get(meal_type, base_cost),
        )

    def _is_generic_meal_name(self, name: str, meal_type: str) -> bool:
        compact = str(name or "").strip().lower()
        if not compact or compact.endswith("recommendation"):
            return True
        generic_tokens = {
            "早餐",
            "午餐",
            "晚餐",
            "简餐",
            "素食餐",
            "轻食",
            "餐饮建议",
            "本地特色早餐",
            "当地主打午餐",
            "轻松晚餐",
            "breakfast",
            "lunch",
            "dinner",
        }
        if compact in generic_tokens:
            return True
        return any(token in compact for token in ("简餐", "素食餐", "轻食", "recommendation"))

    @staticmethod
    def _is_generic_meal_description(description: str) -> bool:
        compact = str(description or "").strip()
        if not compact:
            return True
        generic_phrases = (
            "补充体力",
            "衔接当天行程",
            "控制用餐时间",
            "控制预算",
            "方便出发",
            "方便衔接",
            "本地常见",
        )
        has_food_separator = any(token in compact for token in ("、", "配", "和"))
        return any(token in compact for token in generic_phrases) and not has_food_separator

    def _meal_type_label(self, meal_type: str) -> str:
        mapping = {
            "breakfast": "早餐",
            "lunch": "午餐",
            "dinner": "晚餐",
            "snack": "小吃",
        }
        return mapping.get(str(meal_type).lower(), "餐饮")

    def _estimate_transportation_cost(self, transportation: str, attractions: List[Attraction]) -> int:
        transport_text = transportation.lower()
        segments = max(1, len(attractions))
        if any(token in transport_text for token in ("walk", "步行", "citywalk")):
            return 0
        if any(token in transport_text for token in ("metro", "subway", "bus", "transit", "地铁", "公交")):
            return max(6, segments * 6)
        if any(token in transport_text for token in ("taxi", "car", "drive", "打车", "驾车", "网约车")):
            return max(30, segments * 25)
        return max(10, segments * 8)

    def _default_transportation_detail(
        self,
        request,
        attractions: List[Attraction],
        hotel: Optional[Hotel],
    ) -> str:
        stop_names = "、".join(item.name for item in attractions[:3]) or "当日景点"
        hotel_name = hotel.name if hotel else request.accommodation
        return (
            f"当天以{request.transportation}为主，优先按照景点顺路原则串联{stop_names}，"
            f"减少往返折返时间，结束后回到{hotel_name}附近休息。"
        )

    def _build_route_summary(self, attractions: List[Attraction], transportation: str) -> str:
        if not attractions:
            return ""
        names = [item.name for item in attractions[:3]]
        if len(names) == 1:
            return f"当天主要前往{name}，交通方式以{transportation}为主。".replace("{name}", names[0])
        return f"建议按{' → '.join(names)}的顺序游览，全程以{transportation}衔接，路线更顺畅。"

    def _resolve_route_type(self, transportation: str) -> str:
        transport_text = transportation.lower()
        if any(token in transport_text for token in ("metro", "subway", "bus", "transit", "地铁", "公交")):
            return "transit"
        if any(token in transport_text for token in ("taxi", "car", "drive", "打车", "驾车", "网约车")):
            return "driving"
        return "walking"

    def _enrich_trip_plan(self, trip_plan: TripPlan, payload: PlanningAgentInput) -> TripPlan:
        amap_service = get_amap_service()

        enriched_days: List[DayPlan] = []
        for day in trip_plan.days:
            hotel = day.hotel
            if hotel and hotel.location:
                hotel = hotel.model_copy(
                    update={
                        "map_image_url": amap_service.build_static_map_url(
                            [hotel.location],
                            labels=["H"],
                        )
                    }
                )

            attractions: List[Attraction] = []
            used_image_urls: set[str] = set()
            for index, attraction in enumerate(day.attractions, start=1):
                map_image_url = attraction.map_image_url or amap_service.build_static_map_url(
                    [attraction.location],
                    labels=[str(index)],
                )
                image_url, photos, image_source, image_status = self._resolve_attraction_media(
                    amap_service, attraction, trip_plan.city
                )
                photos = [item for item in photos if item and item not in used_image_urls]
                if image_url in used_image_urls:
                    image_url = next((item for item in photos if item not in used_image_urls), None)
                    if not image_url:
                        image_source = None
                        image_status = "missing"
                if image_url:
                    used_image_urls.add(image_url)
                    photos = self._dedupe_real_image_urls([image_url, *photos])
                description = self._ensure_chinese_attraction_description(
                    attraction.description,
                    attraction.name,
                    attraction.address,
                    attraction.visit_duration,
                )
                attractions.append(
                    attraction.model_copy(
                        update={
                            "image_url": image_url,
                            "photos": photos,
                            "image_source": image_source,
                            "image_status": image_status,
                            "map_image_url": map_image_url,
                            "description": description,
                        }
                    )
                )

            meals = [
                meal.model_copy(update={"description": self._ensure_meal_reason(meal.description, meal.name, trip_plan.city, payload.request, meal.type)})
                for meal in day.meals
            ]

            route_type = self._resolve_route_type(day.transportation)
            route_summary = day.route_summary or self._build_route_summary(attractions, day.transportation)
            route_details = self._build_route_details(amap_service, attractions, trip_plan.city, route_type)
            if route_details:
                route_summary = route_details

            transportation_cost = day.transportation_cost or self._estimate_transportation_cost(
                day.transportation, attractions
            )
            route_map_url = day.route_map_url or amap_service.build_static_map_url(
                [item.location for item in attractions if item.location],
                labels=[str(index + 1) for index in range(len(attractions))],
            )

            enriched_days.append(
                day.model_copy(
                    update={
                        "hotel": hotel,
                        "attractions": attractions,
                        "meals": meals,
                        "transportation_cost": transportation_cost,
                        "transportation_detail": day.transportation_detail
                        or self._default_transportation_detail(payload.request, attractions, hotel),
                        "route_summary": route_summary,
                        "route_map_url": route_map_url,
                        "description": self._ensure_day_description(day.description, attractions, day.transportation),
                    }
                )
            )

        budget = self._build_budget(enriched_days)
        return trip_plan.model_copy(update={"days": enriched_days, "budget": budget})

    def _build_route_details(
        self,
        amap_service,
        attractions: List[Attraction],
        city: str,
        route_type: str,
    ) -> str:
        if len(attractions) < 2:
            return ""

        segments: List[str] = []
        for origin, destination in zip(attractions, attractions[1:]):
            try:
                route = amap_service.plan_route(
                    origin_address=origin.address,
                    destination_address=destination.address,
                    origin_city=city,
                    destination_city=city,
                    route_type=route_type,
                )
                distance_km = round(float(route.get("distance", 0.0)) / 1000, 1)
                duration_min = max(1, int(route.get("duration", 0)) // 60)
                segments.append(
                    f"{origin.name}到{destination.name}约{distance_km}公里，预计{duration_min}分钟"
                )
            except Exception as exc:  # pragma: no cover - external dependency
                logger.debug("Route enrichment failed from %s to %s: %s", origin.name, destination.name, exc)

        return "；".join(segments)

    def _ensure_day_description(self, description: str, attractions: List[Attraction], transportation: str) -> str:
        compact = (description or "").strip()
        if compact and len(compact) >= 24:
            return compact
        attraction_names = "、".join(item.name for item in attractions[:3]) or "城市精华景点"
        return (
            f"当天行程围绕{attraction_names}展开，整体节奏以舒适游览为主，"
            f"通过{transportation}串联主要停留点，兼顾观光体验、休息节奏与预算控制。"
        )

    def _ensure_chinese_attraction_description(
        self,
        description: str,
        name: str,
        address: str,
        visit_duration: int,
    ) -> str:
        compact = (description or "").strip()
        if compact and self._looks_like_chinese(compact) and len(compact) >= 40:
            return compact
        return (
            f"{name}位于{address}，适合作为当天重点游览内容。这里通常能看到城市代表性景观、"
            f"历史文化或休闲体验内容，适合安排约{visit_duration}分钟停留。建议优先关注最有代表性的区域，"
            "并结合当天客流和天气情况安排拍照、步行和休息节奏。"
        )

    def _ensure_meal_reason(self, description: str | None, name: str, city: str, request=None, meal_type: str = "") -> str:
        compact = (description or "").strip()
        if compact and self._looks_like_chinese(compact) and len(compact) >= 18:
            return compact
        if request is not None:
            return self._build_meal_template(request, meal_type or "lunch").description
        return f"推荐选择{name}，既能体验{city}本地风味，也方便衔接当天景点安排。"

    def _looks_like_chinese(self, text: str) -> bool:
        if not text:
            return False
        cjk = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
        return cjk >= max(6, len(text) // 4)

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
