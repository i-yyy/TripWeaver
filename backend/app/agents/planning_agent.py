"""LLM-backed planning agent that turns structured context into a TripPlan."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from time import perf_counter
from typing import Any, Dict, List, Optional

from hello_agents import SimpleAgent

from ..models.agent_schemas import AgentExecutionStatus, PlanningAgentInput, PlanningAgentOutput
from ..models.schemas import Attraction, Budget, DayPlan, Hotel, Location, Meal, MealCandidate, TripPlan, WeatherInfo
from ..models.skill_schemas import SelectedSkill, ValidationResult
from ..services.amap_service import get_amap_service
from ..services.llm_service import get_llm
from ..services.meal_candidate_service import MealCandidateService, get_meal_candidate_service
from ..services.plan_constraint_validator import PlanConstraintValidator, get_plan_constraint_validator

logger = logging.getLogger(__name__)

PLANNER_AGENT_PROMPT = """
你是一名专业旅行规划助手。
你会收到结构化的景点、酒店、天气、用户画像、记忆与 RAG 上下文。
你的任务是只返回最终 trip plan 的 JSON 对象。

规则：
1. 只能返回 JSON，不要返回 Markdown，也不要在 JSON 前后添加任何解释。
2. 所有可读文本字段必须使用简体中文，包括城市说明、景点描述、餐饮描述、交通说明、住宿说明和整体建议。
3. 除非是官方专有名词，否则不要输出英文；如果输入上下文里有英文名称，优先转换为自然中文表达。
4. 严格兼容既有 TripPlan 结构，尤其是 city、start_date、end_date、days、weather_info、overall_suggestions、budget 这些字段。
5. 只能使用提供的结构化上下文，不要编造新的城市、日期、酒店或景点。
6. 默认每天包含 3 个景点、3 餐、1 个酒店建议；如果用户明确偏好轻松节奏、少步行，或属于亲子低强度出行，再将当天景点控制为 2 个。
7. 景点、酒店、餐饮、交通都尽量给出价格或费用估算，不要留空。
8. 景点描述不能空泛，禁止使用“适合作为候选景点”“值得一去”等低信息量表达作为主体内容。
9. 餐饮描述必须回答两个问题：吃什么、为什么吃。
10. 必须结合天气建议、行动需求、预算等级和同行人群。
"""


class PlanningAgent:
    def __init__(
        self,
        planner_runner: Any | None = None,
        constraint_validator: PlanConstraintValidator | None = None,
        meal_candidate_service: MealCandidateService | None = None,
    ) -> None:
        self.tools = ["llm_service"]
        self.planner_runner = planner_runner or SimpleAgent(
            name="planning-agent",
            llm=get_llm(),
            system_prompt=PLANNER_AGENT_PROMPT,
        )
        self.constraint_validator = constraint_validator or get_plan_constraint_validator()
        self.meal_candidate_service = meal_candidate_service or get_meal_candidate_service()

    def list_tools(self) -> List[str]:
        return list(self.tools)

    async def execute(self, payload: PlanningAgentInput) -> PlanningAgentOutput:
        started_at = perf_counter()
        meal_started_at = perf_counter()
        meal_candidates_by_day, meal_source = self._resolve_meal_candidates(payload)
        logger.info(
            "[timing] PlanningAgent meal candidates prepared city=%s elapsed=%.2fs days=%s source=%s",
            payload.request.city,
            perf_counter() - meal_started_at,
            len(meal_candidates_by_day),
            meal_source,
        )

        prompt_started_at = perf_counter()
        prompt = self._build_prompt(payload, meal_candidates_by_day)
        logger.info(
            "[timing] PlanningAgent prompt built city=%s elapsed=%.2fs prompt_chars=%s",
            payload.request.city,
            perf_counter() - prompt_started_at,
            len(prompt),
        )
        try:
            llm_started_at = perf_counter()
            raw_response = await asyncio.to_thread(self.planner_runner.run, prompt)
            logger.info(
                "[timing] PlanningAgent llm completed city=%s elapsed=%.2fs response_chars=%s",
                payload.request.city,
                perf_counter() - llm_started_at,
                len(str(raw_response or "")),
            )

            parse_started_at = perf_counter()
            trip_plan = self._parse_response(raw_response, payload, meal_candidates_by_day)
            logger.info(
                "[timing] PlanningAgent parse completed city=%s elapsed=%.2fs days=%s",
                payload.request.city,
                perf_counter() - parse_started_at,
                len(trip_plan.days),
            )

            enrich_started_at = perf_counter()
            trip_plan = await self._safe_enrich_plan(trip_plan, payload)
            logger.info(
                "[timing] PlanningAgent enrich completed city=%s elapsed=%.2fs days=%s",
                payload.request.city,
                perf_counter() - enrich_started_at,
                len(trip_plan.days),
            )

            validate_started_at = perf_counter()
            trip_plan, validation = await self._validate_plan(trip_plan, payload)
            logger.info(
                "[timing] PlanningAgent validate completed city=%s elapsed=%.2fs warnings=%s errors=%s",
                payload.request.city,
                perf_counter() - validate_started_at,
                len(validation.warnings),
                len(validation.errors),
            )
            warnings = self._validation_messages(validation)
            logger.info(
                "[timing] PlanningAgent finished city=%s total_elapsed=%.2fs degraded=%s",
                payload.request.city,
                perf_counter() - started_at,
                bool(warnings),
            )
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
            fallback_started_at = perf_counter()
            trip_plan = self.build_fallback_plan(payload, meal_candidates_by_day)
            logger.info(
                "[timing] PlanningAgent fallback built city=%s elapsed=%.2fs days=%s",
                payload.request.city,
                perf_counter() - fallback_started_at,
                len(trip_plan.days),
            )
            enrich_started_at = perf_counter()
            trip_plan = await self._safe_enrich_plan(trip_plan, payload)
            logger.info(
                "[timing] PlanningAgent fallback enrich completed city=%s elapsed=%.2fs",
                payload.request.city,
                perf_counter() - enrich_started_at,
            )
            validate_started_at = perf_counter()
            trip_plan, validation = await self._validate_plan(trip_plan, payload)
            logger.info(
                "[timing] PlanningAgent fallback validate completed city=%s elapsed=%.2fs warnings=%s errors=%s",
                payload.request.city,
                perf_counter() - validate_started_at,
                len(validation.warnings),
                len(validation.errors),
            )
            validation_messages = self._validation_messages(validation)
            logger.info(
                "[timing] PlanningAgent finished city=%s total_elapsed=%.2fs degraded=%s fallback=true",
                payload.request.city,
                perf_counter() - started_at,
                True,
            )
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

    def build_fallback_plan(
        self,
        payload: PlanningAgentInput,
        meal_candidates_by_day: Optional[Dict[int, Dict[str, List[MealCandidate]]]] = None,
    ) -> TripPlan:
        request = payload.request
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        hotel = payload.hotel_result.hotels[0] if payload.hotel_result.hotels else None
        weather_info = payload.weather_result.weather_info or []
        suggestions = list(payload.weather_result.suggestions)
        suggestions.extend(payload.supervisor_warnings[:2])
        suggestions = [item for item in suggestions if item]

        days: List[DayPlan] = []
        attractions_pool = payload.attraction_result.attractions or self._build_default_attractions(
            request.city,
            request.travel_days,
            request,
        )

        for day_index in range(request.travel_days):
            date_text = (start_date + timedelta(days=day_index)).strftime("%Y-%m-%d")
            day_attractions = self._pick_day_attractions(attractions_pool, day_index, request)
            day_meal_candidates = (meal_candidates_by_day or {}).get(day_index, {})
            meals = self._build_seed_meals(request, day_meal_candidates)
            days.append(
                DayPlan(
                    date=date_text,
                    day_index=day_index,
                    description=f"第 {day_index + 1} 天围绕 {request.city} 的核心点位展开，整体安排以顺路、舒适、便于衔接为主。",
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
                f"这份备选行程覆盖了 {request.city} {request.travel_days} 天的核心安排。",
                "出发前请再确认开放时间、实时天气和交通情况。",
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

    def _build_prompt(
        self,
        payload: PlanningAgentInput,
        meal_candidates_by_day: Optional[Dict[int, Dict[str, List[MealCandidate]]]] = None,
    ) -> str:
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
            "meal_candidates": self._meal_candidates_prompt_payload(meal_candidates_by_day or {}),
            "warnings": payload.supervisor_warnings,
        }
        context_json = json.dumps(structured_context, ensure_ascii=False, indent=2)
        return (
            "请基于以下结构化上下文生成中文旅行计划 JSON。\n"
            "再次强调：只能输出 JSON，所有说明必须使用简体中文。\n"
            "Keep the existing poi_id for attractions from context whenever available. Do not invent or drop poi_id, image_url, photos, image_source, image_status, or map_image_url when reusing a provided attraction.\n"
            "When meal_candidates are provided, prefer them over invented meal names and keep meals specific.\n"
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

    def _retrieve_meal_candidates(
        self,
        payload: PlanningAgentInput,
    ) -> Dict[int, Dict[str, List[MealCandidate]]]:
        request = payload.request
        attraction_pool = payload.attraction_result.attractions or self._build_default_attractions(
            request.city,
            request.travel_days,
            request,
        )
        hotel_pool = payload.hotel_result.hotels
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
                logger.warning(
                    "Meal candidate retrieval failed city=%s day=%s error=%s",
                    request.city,
                    day_index,
                    exc,
                )
                candidates_by_day[day_index] = {}
        return candidates_by_day

    def _resolve_meal_candidates(
        self,
        payload: PlanningAgentInput,
    ) -> tuple[Dict[int, Dict[str, List[MealCandidate]]], str]:
        candidates_from_agent = payload.meal_result.meal_candidates_by_day
        if candidates_from_agent:
            return candidates_from_agent, "meal-agent"
        return self._retrieve_meal_candidates(payload), "planning-fallback"

    @staticmethod
    def _meal_candidates_prompt_payload(
        meal_candidates_by_day: Dict[int, Dict[str, List[MealCandidate]]],
    ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        payload: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        for day_index, per_type in meal_candidates_by_day.items():
            payload[str(day_index)] = {
                meal_type: [candidate.model_dump() for candidate in candidates]
                for meal_type, candidates in per_type.items()
            }
        return payload

    def _build_seed_meals(
        self,
        request,
        meal_candidates_by_type: Optional[Dict[str, List[MealCandidate]]] = None,
        meals: Optional[List[Meal]] = None,
    ) -> List[Meal]:
        merged = list(meals or [])
        existing_types = {str(meal.type or "").lower() for meal in merged}
        defaults_by_type = {meal.type: meal for meal in self._build_default_meals(request)}
        used_names = {self._normalize_meal_name_for_dedupe(item.name) for item in merged if item.name}

        for meal_type in ("breakfast", "lunch", "dinner"):
            if meal_type in existing_types:
                continue
            candidate = self._pick_meal_candidate(
                meal_type,
                None,
                (meal_candidates_by_type or {}).get(meal_type, []),
                excluded_names=used_names,
            )
            if candidate is not None:
                merged.append(self._candidate_to_meal(candidate, meal_type, request))
                used_names.add(self._normalize_meal_name_for_dedupe(candidate.name))
            else:
                fallback_meal = defaults_by_type[meal_type]
                merged.append(fallback_meal)
                used_names.add(self._normalize_meal_name_for_dedupe(fallback_meal.name))

        return self._sort_meals_by_type(merged[:3])

    @staticmethod
    def _sort_meals_by_type(meals: List[Meal]) -> List[Meal]:
        order = {"breakfast": 0, "lunch": 1, "dinner": 2, "snack": 3}
        return sorted(meals, key=lambda item: order.get(str(item.type).lower(), 99))

    def _pick_meal_candidate(
        self,
        meal_type: str,
        meal: Optional[Meal],
        candidates: List[MealCandidate],
        excluded_names: Optional[set[str]] = None,
    ) -> Optional[MealCandidate]:
        if not candidates:
            return None
        excluded = excluded_names or set()
        if meal is not None:
            matched = self._match_candidate_by_name(meal.name, candidates)
            if matched is not None and self._normalize_meal_name_for_dedupe(matched.name) not in excluded:
                return matched
        for candidate in candidates:
            if self._normalize_meal_name_for_dedupe(candidate.name) not in excluded:
                return candidate
        return None

    @staticmethod
    def _normalize_meal_name_for_dedupe(name: str) -> str:
        return re.sub(r"[\s()（）,，、:：;；·\-_/]+", "", str(name or "")).lower()

    @staticmethod
    def _match_candidate_by_name(name: str, candidates: List[MealCandidate]) -> Optional[MealCandidate]:
        compact_name = re.sub(r"\s+", "", str(name or "")).lower()
        if not compact_name:
            return None
        for candidate in candidates:
            candidate_name = re.sub(r"\s+", "", candidate.name).lower()
            if compact_name == candidate_name:
                return candidate
        for candidate in candidates:
            candidate_name = re.sub(r"\s+", "", candidate.name).lower()
            if compact_name in candidate_name or candidate_name in compact_name:
                return candidate
        return None

    def _candidate_to_meal(self, candidate: MealCandidate, meal_type: str, request) -> Meal:
        return Meal(
            type=meal_type,
            name=candidate.name,
            address=candidate.address or None,
            location=candidate.location,
            description=self._build_candidate_meal_description(candidate, meal_type, request),
            estimated_cost=candidate.estimated_cost or self._build_meal_template(request, meal_type).estimated_cost,
        )

    def _build_candidate_meal_description(self, candidate: MealCandidate, meal_type: str, request) -> str:
        label = self._meal_type_label(meal_type)
        address = candidate.address or request.city
        dietary_suffix = self._meal_dietary_suffix(request)
        category = self._clean_meal_category(candidate.category)
        eat_what = self._build_meal_food_hint(candidate, meal_type)
        reason = self._build_meal_reason_hint(meal_type)
        category_hint = f"店型偏{category}，" if category else ""
        return (
            f"{label}建议在 {candidate.name} 用餐，可考虑点 {eat_what}。"
            f"地点在 {address}，{category_hint}{reason}。{dietary_suffix}"
        ).strip()

    @staticmethod
    def _clean_meal_category(category: str) -> str:
        raw = str(category or "").strip()
        if not raw:
            return ""
        tokens = [item.strip() for item in re.split(r"[;；:：>|/\\,，\s]+", raw) if item and str(item).strip()]
        if not tokens:
            return ""

        ignored = {"餐饮服务", "生活服务", "餐饮", "美食"}
        normalized: List[str] = []
        seen: set[str] = set()
        for token in tokens:
            if token in ignored:
                continue
            if token not in seen:
                normalized.append(token)
                seen.add(token)
        if not normalized:
            return ""
        if len(normalized) >= 2 and normalized[-1] != normalized[-2]:
            return f"{normalized[-2]}、{normalized[-1]}"
        return normalized[-1]

    def _build_meal_food_hint(self, candidate: MealCandidate, meal_type: str) -> str:
        text = " ".join(
            [
                str(candidate.name or ""),
                str(candidate.category or ""),
                str(candidate.source_query or ""),
            ]
        ).lower()
        if any(token in text for token in ("米粉", "粉")):
            return "一份现煮米粉配小菜"
        if any(token in text for token in ("面", "拉面")):
            return "一份热汤面配时蔬或小菜"
        if any(token in text for token in ("粥", "包子", "早餐")):
            return "粥点、包点和一份热饮"
        if any(token in text for token in ("烧烤", "烤")):
            return "招牌烤物配主食和蔬菜"
        if any(token in text for token in ("火锅",)):
            return "小份锅底配主菜和蔬菜拼盘"
        if meal_type == "breakfast":
            return "主食搭配蛋白和热饮"
        if meal_type == "lunch":
            return "一份主食配热菜，控制油盐和分量"
        if meal_type == "dinner":
            return "店内招牌主菜配时蔬和主食"
        return "店内招牌组合餐"

    @staticmethod
    def _build_meal_reason_hint(meal_type: str) -> str:
        if meal_type == "breakfast":
            return "出餐通常更快，方便上午准时开始行程"
        if meal_type == "lunch":
            return "补能效率更高，也便于衔接下午活动"
        if meal_type == "dinner":
            return "收尾节奏更从容，适合一天结束后放松休息"
        return "更方便衔接当天路线安排"

    @staticmethod
    def _meal_dietary_suffix(request) -> str:
        mapping = {
            "vegetarian": "已优先考虑素食限制。",
            "halal": "已优先考虑清真限制。",
            "no_spicy": "已优先考虑少辣或不辣需求。",
        }
        messages = [mapping[item.lower()] for item in getattr(request, "dietary_restrictions", []) if item.lower() in mapping]
        return "" if not messages else " " + "".join(messages)

    def _parse_response(
        self,
        response: Any,
        payload: PlanningAgentInput,
        meal_candidates_by_day: Optional[Dict[int, Dict[str, List[MealCandidate]]]] = None,
    ) -> TripPlan:
        json_str = self._extract_json(str(response))
        data = json.loads(json_str)
        if not isinstance(data, dict):
            raise ValueError("Planner response root must be an object")
        normalized = self._normalize_plan_data(data, payload, meal_candidates_by_day)
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

    def _normalize_plan_data(
        self,
        data: Dict[str, Any],
        payload: PlanningAgentInput,
        meal_candidates_by_day: Optional[Dict[int, Dict[str, List[MealCandidate]]]] = None,
    ) -> Dict[str, Any]:
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
                meal_candidates_by_type=(meal_candidates_by_day or {}).get(index, {}),
                default_hotel=hotel_candidates[index % len(hotel_candidates)] if hotel_candidates else None,
                default_attractions=self._pick_day_attractions(attraction_candidates, index, request),
            )
            for index, raw_day in enumerate(raw_days)
        ]

        if not days:
            fallback = self.build_fallback_plan(payload, meal_candidates_by_day)
            return fallback.model_dump()

        while len(days) < request.travel_days:
            index = len(days)
            days.append(
                self._normalize_day(
                    raw_day={},
                    day_index=index,
                    payload=payload,
                    meal_candidates_by_type=(meal_candidates_by_day or {}).get(index, {}),
                    default_hotel=hotel_candidates[index % len(hotel_candidates)] if hotel_candidates else None,
                    default_attractions=self._pick_day_attractions(attraction_candidates, index, request),
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
        meal_candidates_by_type: Optional[Dict[str, List[MealCandidate]]],
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
            target_count = self._daily_attraction_target_count(request)
            attractions = default_attractions or self._build_default_attractions(request.city, 1, request)[:target_count]
        attractions = self._enrich_attractions(attractions, default_attractions, request.city)

        meals_raw = day.get("meals") if isinstance(day.get("meals"), list) else []
        meals = [self._normalize_meal(item, index) for index, item in enumerate(meals_raw)]
        meals = self._build_seed_meals(request, meal_candidates_by_type, meals)
        meals = self._enrich_meals(meals, request, meal_candidates_by_type)

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
            description=str(day.get("description") or day.get("theme") or f"第 {day_index + 1} 天行程安排"),
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
                    f"{attraction.name}位于 {attraction.address or city}，适合作为当天行程中的重点停留点。"
                    f"核心看点包括当地代表性的景观与适合拍照或慢逛的区域，建议停留 {max(30, attraction.visit_duration)} 分钟，"
                    "并尽量避开最拥挤的时段前往。"
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

    def _enrich_meals(
        self,
        meals: List[Meal],
        request,
        meal_candidates_by_type: Optional[Dict[str, List[MealCandidate]]] = None,
    ) -> List[Meal]:
        defaults_by_type = {meal.type: meal for meal in self._build_default_meals(request)}
        enriched: List[Meal] = []
        used_names: set[str] = set()

        for meal in meals[:3]:
            fallback = defaults_by_type.get(meal.type) or self._build_meal_template(request, meal.type)
            candidate = self._pick_meal_candidate(
                meal.type,
                meal,
                (meal_candidates_by_type or {}).get(str(meal.type).lower(), []),
                excluded_names=used_names,
            )
            name = meal.name.strip()
            if self._is_generic_meal_name(name, meal.type):
                if candidate is not None:
                    name = candidate.name
                else:
                    name = fallback.name

            normalized_name = self._normalize_meal_name_for_dedupe(name)
            if normalized_name in used_names:
                replacement = self._pick_meal_candidate(
                    meal.type,
                    None,
                    (meal_candidates_by_type or {}).get(str(meal.type).lower(), []),
                    excluded_names=used_names,
                )
                if replacement is not None:
                    candidate = replacement
                    name = replacement.name
                else:
                    name = fallback.name
                    candidate = None
                    meal = meal.model_copy(update={"address": None, "location": None})

            description = (meal.description or "").strip()
            if not description or self._is_generic_meal_description(description):
                if candidate is not None:
                    description = self._build_candidate_meal_description(candidate, meal.type, request)
                else:
                    description = fallback.description

            address = meal.address
            location = meal.location
            if candidate is not None:
                address = address or candidate.address or None
                location = location or candidate.location

            estimated_cost = meal.estimated_cost
            if not estimated_cost and candidate is not None:
                estimated_cost = candidate.estimated_cost
            if not estimated_cost:
                estimated_cost = fallback.estimated_cost

            enriched.append(
                meal.model_copy(
                    update={
                        "name": name,
                        "address": address,
                        "location": location,
                        "description": description,
                        "estimated_cost": estimated_cost,
                    }
                )
            )
            used_names.add(self._normalize_meal_name_for_dedupe(name))

        return self._sort_meals_by_type(enriched)

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
        name = str(item.get("name") or item.get("title") or "鎺ㄨ崘鏅偣")
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
            category=str(item.get("category") or "鏅偣"),
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
        normalized_name = re.sub(r"[\s()（）,，、\/_-]+", "", name).lower()
        normalized_address = re.sub(r"[\s()（）,，、\/_-]+", "", address).lower()
        for candidate in candidates:
            candidate_name = re.sub(r"[\s()（）,，、\/_-]+", "", candidate.name).lower()
            candidate_address = re.sub(r"[\s()（）,，、\/_-]+", "", candidate.address).lower()
            if normalized_name and normalized_name == candidate_name:
                return candidate
            if normalized_address and normalized_address == candidate_address:
                return candidate
        for candidate in candidates:
            candidate_name = re.sub(r"[\s()（）,，、\/_-]+", "", candidate.name).lower()
            candidate_address = re.sub(r"[\s()（）,，、\/_-]+", "", candidate.address).lower()
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
            name=str(item.get("name") or item.get("title") or "鎺ㄨ崘鏅偣"),
            address=str(item.get("address") or city),
            location=location,
            visit_duration=self._parse_visit_duration(item.get("visit_duration")),
            description=str(item.get("description") or item.get("reason") or ""),
            category=str(item.get("category") or "鏅偣"),
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

    def _daily_attraction_target_count(self, request) -> int:
        style_tokens = {str(item).strip().lower() for item in getattr(request, "travel_style", [])}
        companion_tokens = {str(item).strip().lower() for item in getattr(request, "companions", [])}
        mobility_tokens = {str(item).strip().lower() for item in getattr(request, "mobility_needs", [])}
        extra_text = str(getattr(request, "free_text_input", "") or "").strip().lower()

        low_intensity_mobility = {"less_walking", "low walking load", "low walking", "wheelchair", "rest_friendly"}
        low_intensity_keywords = ("轻松", "低强度", "少走路", "少步行", "休息点", "low intensity", "slow pace")

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
                name=f"{city}精选景点 {index + 1}",
                address=city,
                location=Location(longitude=116.40 + 0.01 * index, latitude=39.90 + 0.01 * index),
                visit_duration=120,
                description=(
                    f"这是 {city} 的精选候选景点，适合作为当天核心游览内容。"
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
            "breakfast": "早餐建议吃包子、鸡蛋和豆浆，出餐快、饱腹感稳定，方便上午景点前快速出发。",
            "lunch": "午餐建议点热汤面、小炒和米饭，吃什么明确，也方便继续下午行程。",
            "dinner": "晚餐建议吃一份招牌主菜、时蔬和米饭，正餐完整，适合一天结束后好好休息。",
        }

        if "vegetarian" in dietary:
            name_map = {
                "breakfast": "豆浆、素包子和白粥",
                "lunch": "菌菇面配清炒时蔬和豆腐",
                "dinner": "素食套餐配杂粮饭和时令蔬菜",
            }
            description_map = {
                "breakfast": "早餐建议吃豆浆、素包子和白粥，口味清爽、出发快，也能兼顾素食限制和上午行程节奏。",
                "lunch": "午餐建议点菌菇面、清炒时蔬和豆腐，既能吃得具体饱腹，也方便继续下午游览，并符合素食要求。",
                "dinner": "晚餐建议吃素食套餐、杂粮饭和时令蔬菜，收尾更轻松，也能继续保持素食约束。",
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
                "breakfast": "早餐建议吃白粥、鸡蛋和鲜肉包，口味温和、不刺激，适合早点出发前先稳定补充能量。",
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
            f"当天以 {request.transportation} 为主，优先按景点顺路原则串联 {stop_names}，"
            f"减少往返折返时间，结束后回到 {hotel_name} 附近休息。"
        )

    def _build_route_summary(self, attractions: List[Attraction], transportation: str) -> str:
        if not attractions:
            return ""
        names = [item.name for item in attractions[:3]]
        if len(names) == 1:
            return f"当天主要前往 {names[0]}，交通方式以 {transportation} 为主。"
        return f"建议按 {' → '.join(names)} 的顺序游览，全程以 {transportation} 衔接，路线会更顺畅。"

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
        media_elapsed = 0.0
        route_elapsed = 0.0
        media_attempts = 0
        route_attempts = 0
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
                media_started_at = perf_counter()
                image_url, photos, image_source, image_status = self._resolve_attraction_media(
                    amap_service, attraction, trip_plan.city
                )
                media_elapsed += perf_counter() - media_started_at
                media_attempts += 1
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
            route_started_at = perf_counter()
            route_details = self._build_route_details(amap_service, attractions, trip_plan.city, route_type)
            route_elapsed += perf_counter() - route_started_at
            route_attempts += max(0, len(attractions) - 1)
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
        logger.info(
            "[timing] PlanningAgent enrich stats city=%s days=%s media_attempts=%s media_elapsed=%.2fs route_attempts=%s route_elapsed=%.2fs",
            trip_plan.city,
            len(trip_plan.days),
            media_attempts,
            media_elapsed,
            route_attempts,
            route_elapsed,
        )
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
                    f"{origin.name} 到 {destination.name} 约 {distance_km} 公里，预计 {duration_min} 分钟"
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
            f"当天行程围绕 {attraction_names} 展开，整体节奏以舒适游览为主，"
            f"通过 {transportation} 串联主要停留点，兼顾观光体验、休息节奏与预算控制。"
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
            f"{name}位于 {address}，适合作为当天重点游览内容。这里通常能看到城市代表性的景观、"
            f"历史文化或休闲体验内容，适合安排约 {visit_duration} 分钟停留。建议优先关注最有代表性的区域，"
            "并结合当天客流和天气情况安排拍照、步行和休息节奏。"
        )

    def _ensure_meal_reason(self, description: str | None, name: str, city: str, request=None, meal_type: str = "") -> str:
        compact = (description or "").strip()
        if compact and self._looks_like_chinese(compact) and len(compact) >= 18:
            return compact
        if request is not None:
            return self._build_meal_template(request, meal_type or "lunch").description
        return f"推荐选择 {name}，既能体验 {city} 当地风味，也方便衔接当天景点安排。"

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
