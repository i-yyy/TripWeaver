"""Structured hotel retrieval and filtering agent."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Dict, List, Sequence, Set, Tuple

from ..models.agent_schemas import AgentExecutionStatus, HotelAgentInput, HotelAgentOutput
from ..models.schemas import Hotel, Location, POIInfo
from ..models.skill_schemas import SelectedSkill
from ..services.amap_service import AmapService, get_amap_service

logger = logging.getLogger(__name__)

HOTEL_QUERY_MAP: Dict[str, List[str]] = {
    "budget hotel": ["经济型酒店", "连锁酒店", "酒店"],
    "comfort hotel": ["舒适型酒店", "酒店"],
    "luxury hotel": ["高档酒店", "五星级酒店", "酒店"],
    "homestay": ["民宿", "酒店"],
}

HOTEL_HINTS = ("酒店", "宾馆", "民宿", "客栈", "酒店式公寓", "旅舍", "住宿")


class HotelAgent:
    def __init__(self, amap_service: AmapService | None = None) -> None:
        self.amap_service = amap_service or get_amap_service()
        self.tools = ["amap_service.search_poi"]

    def list_tools(self) -> List[str]:
        return list(self.tools)

    async def execute(self, payload: HotelAgentInput) -> HotelAgentOutput:
        search_queries = self._build_queries(payload)
        warnings: List[str] = []
        collected: List[POIInfo] = []

        query_results = await asyncio.gather(
            *[self._search_query(query, payload.request.city) for query in search_queries]
        )
        for pois, warning in query_results:
            if pois:
                collected.extend(pois)
            if warning:
                warnings.append(warning)

        hotels = self._rank_and_convert(payload, collected)
        status = AgentExecutionStatus(
            success=bool(hotels) or not warnings,
            degraded=bool(warnings) or not hotels,
            warnings=warnings if hotels else warnings + ["No structured hotel candidates were returned"],
            error=None if hotels or not warnings else warnings[-1],
        )

        logger.info(
            "HotelAgent city=%s queries=%s raw=%s final=%s",
            payload.request.city,
            len(search_queries),
            len(collected),
            len(hotels),
        )
        return HotelAgentOutput(status=status, search_queries=search_queries, hotels=hotels)

    async def _search_query(self, query: str, city: str) -> Tuple[List[POIInfo], str | None]:
        try:
            pois = await asyncio.to_thread(self.amap_service.search_poi, query, city)
            return pois, None
        except Exception as exc:  # pragma: no cover - external dependency
            warning = f"Hotel search failed for query '{query}': {exc}"
            logger.warning(warning)
            return [], warning

    def _build_queries(self, payload: HotelAgentInput) -> List[str]:
        accommodation = payload.request.accommodation.strip().lower()
        queries = HOTEL_QUERY_MAP.get(accommodation, [])
        ordered: List[str] = []
        seen: Set[str] = set()

        raw_accommodation = payload.request.accommodation.strip()
        extra_queries = ["酒店", "宾馆"]
        if self._contains_cjk(raw_accommodation):
            extra_queries.insert(0, raw_accommodation)

        for query in self._skill_query_boosts(payload.skills) + queries + extra_queries:
            compact = query.strip()
            if compact and compact not in seen:
                seen.add(compact)
                ordered.append(compact)

        return ordered[:5]

    def _rank_and_convert(self, payload: HotelAgentInput, pois: Sequence[POIInfo]) -> List[Hotel]:
        seen: Set[str] = set()
        scored: List[tuple[float, Hotel]] = []

        for poi in pois:
            if self._should_exclude(poi):
                continue

            dedupe_key = self._dedupe_key(poi)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            hotel = self._poi_to_hotel(payload, poi)
            score = self._score_poi(payload, poi)
            scored.append((score, hotel))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in scored[: payload.limit]]

    def _should_exclude(self, poi: POIInfo) -> bool:
        text = f"{poi.name} {poi.type}"
        return not any(hint in text for hint in HOTEL_HINTS)

    def _score_poi(self, payload: HotelAgentInput, poi: POIInfo) -> float:
        request = payload.request
        text = f"{poi.name} {poi.type}".lower()
        accommodation = request.accommodation.lower()
        score = 1.0
        skill_keys = {skill.key for skill in payload.skills}

        if "luxury" in accommodation and any(token in text for token in ("豪华", "五星", "高档", "国际")):
            score += 2.5
        if "budget" in accommodation and any(token in text for token in ("经济", "快捷", "连锁", "青年旅舍")):
            score += 2.5
        if "comfort" in accommodation and any(token in text for token in ("舒适", "精选", "商务", "酒店")):
            score += 2.0
        if "homestay" in accommodation and any(token in text for token in ("民宿", "客栈")):
            score += 2.5

        if request.budget_level == "low":
            score += 1.0 if any(token in text for token in ("经济", "快捷", "连锁", "旅舍")) else -0.5
        elif request.budget_level == "high":
            score += 1.0 if any(token in text for token in ("豪华", "五星", "高档")) else -0.5

        if "low_mobility" in skill_keys and any(token in text for token in ("地铁", "交通", "商圈", "中心", "站")):
            score += 1.5
        if "family_friendly" in skill_keys and any(token in text for token in ("酒店", "连锁", "商务")):
            score += 0.6

        return score

    def _poi_to_hotel(self, payload: HotelAgentInput, poi: POIInfo) -> Hotel:
        request = payload.request
        return Hotel(
            name=poi.name,
            address=poi.address,
            location=Location(
                longitude=poi.location.longitude,
                latitude=poi.location.latitude,
            ),
            price_range=self._estimate_price_range(request),
            rating="",
            distance="",
            type=poi.type,
            estimated_cost=self._estimate_cost(request),
        )

    def _estimate_cost(self, request) -> int:
        accommodation = request.accommodation.lower()
        if "luxury" in accommodation:
            return 1200
        if "comfort" in accommodation:
            return 600
        if "budget" in accommodation:
            return 280
        if "homestay" in accommodation:
            return 420
        if request.budget_level == "high":
            return 900
        if request.budget_level == "low":
            return 250
        return 500

    def _estimate_price_range(self, request) -> str:
        if request.budget_level == "high":
            return "high"
        if request.budget_level == "low":
            return "low"
        return "medium"

    @staticmethod
    def _skill_query_boosts(skills: List[SelectedSkill]) -> List[str]:
        ordered: List[str] = []
        seen: Set[str] = set()
        for skill in skills:
            for query in skill.hotel_query_boosts:
                compact = query.strip()
                if compact and compact not in seen:
                    seen.add(compact)
                    ordered.append(compact)
        return ordered

    @staticmethod
    def _dedupe_key(poi: POIInfo) -> str:
        compact_name = re.sub(r"[()（）\s]+", "", poi.name.lower())
        compact_address = re.sub(r"\s+", "", poi.address.lower())
        return f"{compact_name}:{compact_address}"

    @staticmethod
    def _contains_cjk(text: str) -> bool:
        return any("\u4e00" <= char <= "\u9fff" for char in text)
