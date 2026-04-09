"""Meal candidate retrieval backed by AMap POI search."""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional, Sequence

from ..models.schemas import Attraction, Hotel, MealCandidate, POIInfo, TripRequest
from ..models.skill_schemas import SelectedSkill
from .amap_service import AmapService, get_amap_service

logger = logging.getLogger(__name__)

MEAL_TYPES = ("breakfast", "lunch", "dinner")

MEAL_QUERY_TERMS: Dict[str, List[str]] = {
    "breakfast": ["早餐", "早点", "早饭"],
    "lunch": ["午餐", "中餐", "简餐"],
    "dinner": ["晚餐", "本地菜", "餐馆"],
}

FOOD_STYLE_TERMS = ["本地特色", "美食", "小吃"]

DIETARY_QUERY_TERMS: Dict[str, List[str]] = {
    "vegetarian": ["素食", "素餐"],
    "halal": ["清真"],
    "no_spicy": ["清淡", "少辣", "不辣"],
}


class MealCandidateService:
    """Retrieve meal POI candidates with lightweight rule-based queries."""

    def __init__(self, amap_service: AmapService | None = None) -> None:
        self.amap_service = amap_service or get_amap_service()

    def retrieve_day_candidates(
        self,
        request: TripRequest,
        day_index: int,
        attractions: Sequence[Attraction],
        hotel: Hotel | None = None,
        skills: Sequence[SelectedSkill] = (),
        per_type_limit: int = 5,
    ) -> Dict[str, List[MealCandidate]]:
        skill_keys = {item.key for item in skills}
        anchors = self._build_anchor_texts(request.city, attractions, hotel)
        results: Dict[str, List[MealCandidate]] = {}

        for meal_type in MEAL_TYPES:
            queries = self._build_queries(
                request=request,
                meal_type=meal_type,
                anchors=anchors,
                skill_keys=skill_keys,
            )
            candidates = self._run_queries(
                request=request,
                meal_type=meal_type,
                queries=queries,
                limit=per_type_limit,
            )
            results[meal_type] = candidates

        counts = {meal_type: len(items) for meal_type, items in results.items()}
        logger.info("MealCandidateService day=%s city=%s counts=%s", day_index, request.city, counts)
        return results

    @staticmethod
    def _build_anchor_texts(city: str, attractions: Sequence[Attraction], hotel: Hotel | None) -> List[str]:
        anchors: List[str] = []
        seen: set[str] = set()
        for attraction in attractions[:2]:
            name = str(attraction.name or "").strip()
            if name and name not in seen:
                seen.add(name)
                anchors.append(name)
        if hotel is not None:
            hotel_name = str(hotel.name or "").strip()
            if hotel_name and hotel_name not in seen:
                seen.add(hotel_name)
                anchors.append(hotel_name)
        city_name = str(city or "").strip()
        if city_name and city_name not in seen:
            anchors.append(city_name)
        return anchors

    def _build_queries(
        self,
        request: TripRequest,
        meal_type: str,
        anchors: Sequence[str],
        skill_keys: set[str],
    ) -> List[str]:
        terms = list(MEAL_QUERY_TERMS.get(meal_type, [meal_type]))
        if "food_explorer" in skill_keys or "local_immersion" in skill_keys:
            terms.extend(FOOD_STYLE_TERMS)

        dietary_terms = self._dietary_terms(request.dietary_restrictions)
        queries: List[str] = []
        seen: set[str] = set()

        for anchor in anchors:
            for term in terms:
                self._append_query(queries, seen, f"{anchor} 附近 {term}")
                self._append_query(queries, seen, f"{anchor} {term}")
            for dietary_term in dietary_terms:
                for term in terms[:2]:
                    self._append_query(queries, seen, f"{anchor} 附近 {dietary_term}{term}")

        city_name = str(request.city or "").strip()
        for term in terms:
            self._append_query(queries, seen, f"{city_name} {term}")
        if "food_explorer" in skill_keys:
            self._append_query(queries, seen, f"{city_name} 必吃 {terms[0]}")

        return queries[:8]

    def _run_queries(
        self,
        request: TripRequest,
        meal_type: str,
        queries: Sequence[str],
        limit: int,
    ) -> List[MealCandidate]:
        collected: List[MealCandidate] = []
        seen_keys: set[str] = set()

        for query in queries:
            try:
                pois = self.amap_service.search_poi(query, request.city)
            except Exception as exc:  # pragma: no cover - external dependency
                logger.warning("Meal candidate query failed city=%s meal_type=%s query=%s error=%s", request.city, meal_type, query, exc)
                continue

            for poi in pois:
                candidate = self._build_candidate(request, meal_type, poi, query)
                if candidate is None:
                    continue
                dedupe_key = self._candidate_key(candidate)
                if dedupe_key in seen_keys:
                    continue
                seen_keys.add(dedupe_key)
                collected.append(candidate)

        collected.sort(key=lambda item: self._score_candidate(item, request, meal_type), reverse=True)
        return collected[:limit]

    def _build_candidate(
        self,
        request: TripRequest,
        meal_type: str,
        poi: POIInfo,
        source_query: str,
    ) -> Optional[MealCandidate]:
        name = str(poi.name or "").strip()
        if not name:
            return None
        return MealCandidate(
            meal_type=meal_type,
            name=name,
            poi_id=str(poi.id or "").strip(),
            address=str(poi.address or "").strip(),
            location=poi.location,
            category=str(poi.type or "").strip(),
            tags=self._extract_tags(request, name, str(poi.type or "")),
            estimated_cost=self._estimate_cost(request, meal_type),
            source_query=source_query,
        )

    @staticmethod
    def _candidate_key(candidate: MealCandidate) -> str:
        if candidate.poi_id:
            return candidate.poi_id
        compact_name = "".join(str(candidate.name).lower().split())
        compact_address = "".join(str(candidate.address).lower().split())
        return f"{compact_name}|{compact_address}"

    def _score_candidate(self, candidate: MealCandidate, request: TripRequest, meal_type: str) -> float:
        score = 0.0
        text = " ".join(
            [
                candidate.name,
                candidate.category,
                candidate.address,
                candidate.source_query,
                " ".join(candidate.tags),
            ]
        ).lower()

        for token in MEAL_QUERY_TERMS.get(meal_type, []):
            if token.lower() in text:
                score += 2.0
        for token in self._dietary_terms(request.dietary_restrictions):
            if token.lower() in text:
                score += 2.5
        for token in FOOD_STYLE_TERMS:
            if token.lower() in text:
                score += 0.8
        if candidate.poi_id:
            score += 0.3
        if candidate.address:
            score += 0.2
        return score

    @staticmethod
    def _append_query(queries: List[str], seen: set[str], query: str) -> None:
        text = str(query or "").strip()
        if not text or text in seen:
            return
        seen.add(text)
        queries.append(text)

    @staticmethod
    def _dietary_terms(restrictions: Iterable[str]) -> List[str]:
        terms: List[str] = []
        for token in restrictions:
            for item in DIETARY_QUERY_TERMS.get(str(token).lower(), []):
                if item not in terms:
                    terms.append(item)
        return terms

    @staticmethod
    def _extract_tags(request: TripRequest, name: str, category: str) -> List[str]:
        tags: List[str] = []
        text = f"{name} {category}".lower()
        if "food" in [item.lower() for item in request.preferences]:
            tags.append("food")
        if any(token in text for token in ("清真",)):
            tags.append("halal")
        if any(token in text for token in ("素",)):
            tags.append("vegetarian")
        if any(token in text for token in ("辣", "川")):
            tags.append("spicy")
        return tags

    @staticmethod
    def _estimate_cost(request: TripRequest, meal_type: str) -> int:
        budget = str(request.budget_level or "medium").lower()
        base_cost = {"low": 30, "medium": 60, "high": 120}.get(budget, 60)
        if meal_type == "breakfast":
            return max(12, base_cost // 2)
        if meal_type == "dinner":
            return base_cost + 20
        return base_cost


_meal_candidate_service: Optional[MealCandidateService] = None


def get_meal_candidate_service() -> MealCandidateService:
    global _meal_candidate_service
    if _meal_candidate_service is None:
        _meal_candidate_service = MealCandidateService()
    return _meal_candidate_service
