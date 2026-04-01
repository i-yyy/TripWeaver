"""Skill selection service for the trip planning flow."""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from ..models.schemas import TripRequest
from ..models.skill_schemas import SelectedSkill, SkillDefinition
from ..skills.registry import get_skill_registry


class SkillService:
    """Rule-based skill selector for the MVP."""

    def __init__(self, registry: Optional[Sequence[SkillDefinition]] = None) -> None:
        self.registry = list(registry) if registry is not None else get_skill_registry()

    def select_skills(
        self,
        request: TripRequest,
        profile_context: str = "",
        memory_context: str = "",
        rag_context: str = "",
        limit: int = 3,
    ) -> List[SelectedSkill]:
        bag = self._build_signal_bag(
            request=request,
            profile_context=profile_context,
            memory_context=memory_context,
            rag_context=rag_context,
        )
        candidates: List[Tuple[SkillDefinition, float, List[str]]] = []

        for definition in self.registry:
            if not definition.enabled:
                continue

            score = 0.0
            reasons: List[str] = []

            for tag in definition.required_any_tags:
                if self._contains_token(bag["constraints"], tag):
                    score += 1.2
                    reasons.append(f"matched constraint: {tag}")
                elif self._contains_token(bag["tags"], tag):
                    score += 1.0
                    reasons.append(f"matched tag: {tag}")

            for keyword in definition.required_any_keywords:
                if self._contains_token(bag["keywords"], keyword):
                    weight = 1.2 if self._is_hard_constraint(keyword) else 0.6
                    score += weight
                    reasons.append(f"matched keyword: {keyword}")

            if score <= 0:
                continue

            candidates.append((definition, score, self._dedupe(reasons)))

        candidates.sort(key=lambda item: (item[1], -item[0].priority), reverse=True)

        selected: List[SelectedSkill] = []
        selected_keys: List[str] = []
        for definition, score, reasons in candidates:
            if any(key in definition.incompatible_with for key in selected_keys):
                continue
            selected.append(
                SelectedSkill(
                    key=definition.key,
                    name=definition.name,
                    description=definition.description,
                    score=round(score, 3),
                    reasons=reasons,
                    attraction_query_boosts=list(definition.attraction_query_boosts),
                    hotel_query_boosts=list(definition.hotel_query_boosts),
                    planning_rules=list(definition.planning_rules),
                    output_hints=list(definition.output_hints),
                )
            )
            selected_keys.append(definition.key)
            if len(selected) >= limit:
                break

        return selected

    @staticmethod
    def _build_signal_bag(
        request: TripRequest,
        profile_context: str,
        memory_context: str,
        rag_context: str,
    ) -> dict[str, str]:
        tags = " ".join(
            [
                *request.preferences,
                *request.travel_style,
                *request.companions,
                request.budget_level or "",
            ]
        ).lower()
        constraints = " ".join(
            [
                *request.dietary_restrictions,
                *request.mobility_needs,
            ]
        ).lower()
        keywords = " ".join(
            [
                request.free_text_input,
                profile_context,
                memory_context,
                rag_context,
            ]
        ).lower()
        return {"tags": tags, "constraints": constraints, "keywords": keywords}

    @staticmethod
    def _contains_token(haystack: str, needle: str) -> bool:
        return needle.strip().lower() in haystack

    @staticmethod
    def _is_hard_constraint(token: str) -> bool:
        normalized = token.strip().lower()
        return normalized in {"low walking load", "low walking", "wheelchair", "elderly", "行动不便", "老人"}

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


_skill_service: Optional[SkillService] = None


def get_skill_service() -> SkillService:
    global _skill_service
    if _skill_service is None:
        _skill_service = SkillService()
    return _skill_service
