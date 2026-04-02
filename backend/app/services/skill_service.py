"""Skill selection, dynamic augmentation, and final resolution for V2."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, List, Optional, Sequence

from ..models.agent_schemas import WeatherAgentOutput
from ..models.schemas import TripRequest
from ..models.skill_schemas import SelectedSkill, SkillDefinition
from ..skills.registry import get_skill_registry


class SkillService:
    """Rule-based selector with static/dynamic phases and capped resolution."""

    MAX_TOTAL_SKILLS = 4
    MAX_HARD_SKILLS = 3
    MAX_DYNAMIC_SKILLS = 2
    MAX_STYLE_SKILLS = 2

    def __init__(self, registry: Optional[Sequence[SkillDefinition]] = None) -> None:
        self.registry = list(registry) if registry is not None else get_skill_registry()

    def select_static_skills(
        self,
        request: TripRequest,
        profile_context: str = "",
        memory_context: str = "",
        rag_context: str = "",
    ) -> List[SelectedSkill]:
        bag = self._build_signal_bag(
            request=request,
            profile_context=profile_context,
            memory_context=memory_context,
            rag_context=rag_context,
        )
        return self._select_candidates(
            definitions=[item for item in self.registry if item.enabled and item.layer == "static"],
            request=request,
            bag=bag,
            source="static",
            weather_result=None,
        )

    def augment_dynamic_skills(
        self,
        request: TripRequest,
        weather_result: WeatherAgentOutput,
        profile_context: str = "",
        memory_context: str = "",
        rag_context: str = "",
    ) -> List[SelectedSkill]:
        bag = self._build_signal_bag(
            request=request,
            profile_context=profile_context,
            memory_context=memory_context,
            rag_context=rag_context,
        )
        return self._select_candidates(
            definitions=[item for item in self.registry if item.enabled and item.layer == "dynamic"],
            request=request,
            bag=bag,
            source="dynamic",
            weather_result=weather_result,
        )

    def finalize_skills(
        self,
        static_skills: Sequence[SelectedSkill],
        dynamic_skills: Sequence[SelectedSkill],
    ) -> List[SelectedSkill]:
        combined = self._dedupe_selected(list(static_skills) + list(dynamic_skills))
        if not combined:
            return []

        ordered = sorted(
            combined,
            key=lambda item: (self._category_weight(item.category), item.score, -item.priority),
            reverse=True,
        )

        selected: List[SelectedSkill] = []
        suppressed: set[str] = set()
        hard_count = 0
        dynamic_count = 0
        style_count = 0

        for skill in ordered:
            if skill.key in suppressed:
                continue
            if any(existing.key in skill.incompatible_with for existing in selected):
                continue
            if any(skill.key in existing.suppresses for existing in selected):
                continue

            is_hard = self._is_hard_category(skill.category)
            is_dynamic = skill.layer == "dynamic"
            is_style = skill.category == "style"

            if is_hard and hard_count >= self.MAX_HARD_SKILLS:
                continue
            if is_dynamic and dynamic_count >= self.MAX_DYNAMIC_SKILLS:
                continue
            if is_style and style_count >= self.MAX_STYLE_SKILLS:
                continue
            if len(selected) >= self.MAX_TOTAL_SKILLS:
                continue

            if skill.suppresses:
                selected = [item for item in selected if item.key not in set(skill.suppresses)]
                hard_count = sum(1 for item in selected if self._is_hard_category(item.category))
                dynamic_count = sum(1 for item in selected if item.layer == "dynamic")
                style_count = sum(1 for item in selected if item.category == "style")
                suppressed.update(skill.suppresses)

            selected.append(skill)
            if is_hard:
                hard_count += 1
            if is_dynamic:
                dynamic_count += 1
            if is_style:
                style_count += 1

        return selected

    def select_skills(
        self,
        request: TripRequest,
        profile_context: str = "",
        memory_context: str = "",
        rag_context: str = "",
        weather_result: WeatherAgentOutput | None = None,
    ) -> List[SelectedSkill]:
        static_skills = self.select_static_skills(
            request=request,
            profile_context=profile_context,
            memory_context=memory_context,
            rag_context=rag_context,
        )
        if weather_result is not None:
            dynamic_skills = self.augment_dynamic_skills(
                request=request,
                weather_result=weather_result,
                profile_context=profile_context,
                memory_context=memory_context,
                rag_context=rag_context,
            )
        else:
            bag = self._build_signal_bag(
                request=request,
                profile_context=profile_context,
                memory_context=memory_context,
                rag_context=rag_context,
            )
            dynamic_skills = self.finalize_skills(
                [],
                self._select_candidates(
                    definitions=[
                        item
                        for item in self.registry
                        if item.enabled
                        and item.layer == "dynamic"
                        and not item.weekend_only
                        and item.min_temperature is None
                        and item.max_temperature is None
                    ],
                    request=request,
                    bag=bag,
                    source="dynamic",
                    weather_result=None,
                ),
            )
        return self.finalize_skills(static_skills, dynamic_skills)[:3]

    def _select_candidates(
        self,
        definitions: Sequence[SkillDefinition],
        request: TripRequest,
        bag: dict[str, str],
        source: str,
        weather_result: WeatherAgentOutput | None,
    ) -> List[SelectedSkill]:
        selected: List[SelectedSkill] = []
        for definition in definitions:
            score = 0.0
            matched_fields: List[str] = []
            matched_terms: List[str] = []
            reasons: List[str] = []

            score = self._match_terms(
                haystack=bag["tags"],
                needles=definition.required_any_tags,
                base_score=1.0,
                field_name="tags",
                score=score,
                matched_fields=matched_fields,
                matched_terms=matched_terms,
                reasons=reasons,
            )
            score = self._match_terms(
                haystack=bag["keywords"],
                needles=definition.required_any_keywords,
                base_score=0.6,
                field_name="keywords",
                score=score,
                matched_fields=matched_fields,
                matched_terms=matched_terms,
                reasons=reasons,
            )
            score = self._match_terms(
                haystack=bag["dietary"],
                needles=definition.required_dietary_restrictions,
                base_score=1.2,
                field_name="dietary_restrictions",
                score=score,
                matched_fields=matched_fields,
                matched_terms=matched_terms,
                reasons=reasons,
            )
            score = self._match_terms(
                haystack=bag["mobility"],
                needles=definition.required_mobility_needs,
                base_score=1.2,
                field_name="mobility_needs",
                score=score,
                matched_fields=matched_fields,
                matched_terms=matched_terms,
                reasons=reasons,
            )
            score = self._match_terms(
                haystack=bag["companions"],
                needles=definition.required_companions,
                base_score=1.0,
                field_name="companions",
                score=score,
                matched_fields=matched_fields,
                matched_terms=matched_terms,
                reasons=reasons,
            )
            score = self._match_terms(
                haystack=bag["transportation"],
                needles=[item.lower() for item in definition.required_transport_modes],
                base_score=1.0,
                field_name="transportation",
                score=score,
                matched_fields=matched_fields,
                matched_terms=matched_terms,
                reasons=reasons,
            )
            score = self._match_terms(
                haystack=bag["budget_level"],
                needles=[item.lower() for item in definition.required_budget_levels],
                base_score=1.0,
                field_name="budget_level",
                score=score,
                matched_fields=matched_fields,
                matched_terms=matched_terms,
                reasons=reasons,
            )

            if definition.weekend_only and self._is_weekend_trip(request):
                score += 1.1
                matched_fields.append("date")
                matched_terms.append("weekend")
                reasons.append("matched weekend date")

            if weather_result is not None:
                score = self._match_weather(
                    definition=definition,
                    weather_result=weather_result,
                    score=score,
                    matched_fields=matched_fields,
                    matched_terms=matched_terms,
                    reasons=reasons,
                )

            if score <= 0:
                continue

            selected.append(
                SelectedSkill(
                    key=definition.key,
                    name=definition.name,
                    description=definition.description,
                    score=round(score, 3),
                    priority=definition.priority,
                    layer=definition.layer,
                    category=definition.category,
                    source=source,
                    matched_fields=self._dedupe(matched_fields),
                    matched_terms=self._dedupe(matched_terms),
                    reasons=self._dedupe(reasons),
                    incompatible_with=list(definition.incompatible_with),
                    suppresses=list(definition.suppresses),
                    hard_rules=list(definition.hard_rules),
                    soft_rules=list(definition.soft_rules),
                    meal_rules=list(definition.meal_rules),
                    routing_rules=list(definition.routing_rules),
                    planning_rules=[
                        *definition.planning_rules,
                        *definition.hard_rules,
                        *definition.soft_rules,
                        *definition.meal_rules,
                        *definition.routing_rules,
                    ],
                    attraction_query_boosts=list(definition.attraction_query_boosts),
                    hotel_query_boosts=list(definition.hotel_query_boosts),
                    output_hints=list(definition.output_hints),
                )
            )

        return selected

    @staticmethod
    def _build_signal_bag(
        request: TripRequest,
        profile_context: str,
        memory_context: str,
        rag_context: str,
    ) -> dict[str, str]:
        tags = " ".join([*request.preferences, *request.travel_style]).lower()
        keywords = " ".join([request.free_text_input, profile_context, memory_context, rag_context]).lower()
        return {
            "tags": tags,
            "keywords": keywords,
            "budget_level": str(request.budget_level or "").lower(),
            "transportation": str(request.transportation or "").lower(),
            "companions": " ".join(request.companions).lower(),
            "dietary": " ".join(request.dietary_restrictions).lower(),
            "mobility": " ".join(request.mobility_needs).lower(),
        }

    def _match_weather(
        self,
        definition: SkillDefinition,
        weather_result: WeatherAgentOutput,
        score: float,
        matched_fields: List[str],
        matched_terms: List[str],
        reasons: List[str],
    ) -> float:
        weather_text = " ".join(
            [
                weather_result.summary,
                *weather_result.suggestions,
                *[
                    f"{item.day_weather} {item.night_weather} {item.day_temp} {item.night_temp}"
                    for item in weather_result.weather_info
                ],
            ]
        ).lower()

        if definition.weather_keywords:
            for token in definition.weather_keywords:
                if token.lower() in weather_text:
                    score += 1.1
                    matched_fields.append("weather")
                    matched_terms.append(token)
                    reasons.append(f"matched weather keyword: {token}")

        if definition.min_temperature is not None:
            hottest = max([int(item.day_temp) for item in weather_result.weather_info], default=-999)
            if hottest >= definition.min_temperature:
                score += 1.4
                matched_fields.append("weather")
                matched_terms.append(f"temp>={definition.min_temperature}")
                reasons.append(f"matched min temperature: {definition.min_temperature}")

        if definition.max_temperature is not None:
            coldest = min([int(item.day_temp) for item in weather_result.weather_info], default=999)
            if coldest <= definition.max_temperature:
                score += 1.0
                matched_fields.append("weather")
                matched_terms.append(f"temp<={definition.max_temperature}")
                reasons.append(f"matched max temperature: {definition.max_temperature}")

        return score

    @staticmethod
    def _match_terms(
        haystack: str,
        needles: Sequence[str],
        base_score: float,
        field_name: str,
        score: float,
        matched_fields: List[str],
        matched_terms: List[str],
        reasons: List[str],
    ) -> float:
        for needle in needles:
            token = needle.strip().lower()
            if token and token in haystack:
                score += base_score
                matched_fields.append(field_name)
                matched_terms.append(token)
                reasons.append(f"matched {field_name}: {token}")
        return score

    @staticmethod
    def _is_weekend_trip(request: TripRequest) -> bool:
        try:
            start = datetime.strptime(request.start_date, "%Y-%m-%d")
            end = datetime.strptime(request.end_date, "%Y-%m-%d")
        except ValueError:
            return False
        cursor = start
        while cursor <= end:
            if cursor.weekday() >= 5:
                return True
            cursor += timedelta(days=1)
        return False

    @staticmethod
    def _dedupe(items: Sequence[str]) -> List[str]:
        ordered: List[str] = []
        seen = set()
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            ordered.append(item)
        return ordered

    @staticmethod
    def _dedupe_selected(skills: Iterable[SelectedSkill]) -> List[SelectedSkill]:
        by_key: dict[str, SelectedSkill] = {}
        for skill in skills:
            existing = by_key.get(skill.key)
            if existing is None or (skill.score, -skill.priority) > (existing.score, -existing.priority):
                by_key[skill.key] = skill
        return list(by_key.values())

    @staticmethod
    def _is_hard_category(category: str) -> bool:
        return category in {"hard", "dynamic-hard"}

    @staticmethod
    def _category_weight(category: str) -> int:
        if category == "hard":
            return 3
        if category == "dynamic-hard":
            return 2
        return 1


_skill_service: Optional[SkillService] = None


def get_skill_service() -> SkillService:
    global _skill_service
    if _skill_service is None:
        _skill_service = SkillService()
    return _skill_service
