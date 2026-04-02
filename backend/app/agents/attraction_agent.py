"""Structured attraction retrieval and ranking agent."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Dict, List, Sequence, Set, Tuple

from ..models.agent_schemas import AgentExecutionStatus, AttractionAgentInput, AttractionAgentOutput
from ..models.schemas import Attraction, Location, POIInfo
from ..models.skill_schemas import SelectedSkill
from ..services.amap_service import AmapService, get_amap_service

logger = logging.getLogger(__name__)

TAG_QUERY_MAP: Dict[str, List[str]] = {
    "history": ["博物馆", "名胜古迹"],
    "nature": ["公园", "自然风景区"],
    "museum": ["博物馆"],
    "citywalk": ["景点", "步行街"],
    "shopping": ["购物中心", "商圈"],
    "family": ["亲子景点", "公园"],
}

EXCLUDED_NAME_KEYWORDS = {
    "售票",
    "游客中心",
    "讲解",
    "停车场",
    "卫生间",
    "文创店",
    "餐饮",
    "便利店",
    "服务点",
    "出入口",
    "入口",
    "出口",
}

INDOOR_HINTS = {"博物馆", "美术馆", "科技馆", "展览馆", "图书馆", "艺术馆"}
LOW_WALKING_PENALTIES = {"山", "长城", "徒步", "森林公园", "湿地"}
FAMILY_FRIENDLY_HINTS = {"科技馆", "动物园", "博物馆", "公园", "海洋馆", "亲子"}


class AttractionAgent:
    def __init__(self, amap_service: AmapService | None = None) -> None:
        self.amap_service = amap_service or get_amap_service()
        self.tools = ["amap_service.search_poi"]

    def list_tools(self) -> List[str]:
        return list(self.tools)

    async def execute(self, payload: AttractionAgentInput) -> AttractionAgentOutput:
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

        attractions = self._rank_and_convert(payload, collected)
        status = AgentExecutionStatus(
            success=bool(attractions) or not warnings,
            degraded=bool(warnings) or not attractions,
            warnings=warnings if attractions else warnings + ["No structured attractions were returned"],
            error=None if attractions or not warnings else warnings[-1],
        )

        logger.info(
            "AttractionAgent city=%s queries=%s raw=%s final=%s",
            payload.request.city,
            len(search_queries),
            len(collected),
            len(attractions),
        )
        return AttractionAgentOutput(status=status, search_queries=search_queries, attractions=attractions)

    async def _search_query(self, query: str, city: str) -> Tuple[List[POIInfo], str | None]:
        try:
            pois = await asyncio.to_thread(self.amap_service.search_poi, query, city)
            return pois, None
        except Exception as exc:  # pragma: no cover - external dependency
            warning = f"Attraction search failed for query '{query}': {exc}"
            logger.warning(warning)
            return [], warning

    def _build_queries(self, payload: AttractionAgentInput) -> List[str]:
        request = payload.request
        ordered: List[str] = []
        seen: Set[str] = set()

        def add(query: str) -> None:
            compact = query.strip()
            if compact and compact not in seen:
                seen.add(compact)
                ordered.append(compact)

        for query in self._skill_query_boosts(payload.skills):
            add(query)

        tags = request.preferences + request.travel_style + request.companions
        for tag in tags:
            for mapped in TAG_QUERY_MAP.get(tag.strip().lower(), []):
                add(mapped)

        free_text = f"{request.free_text_input} {payload.rag_context}".lower()
        if any(token in free_text for token in ("rain", "下雨", "雨天", "indoor", "室内")):
            add("室内景点")
            add("博物馆")

        if request.preferences:
            first_preference = request.preferences[0].strip()
            if self._contains_cjk(first_preference):
                add(first_preference)

        add("景点")
        add("热门景点")
        return ordered[:6]

    def _rank_and_convert(self, payload: AttractionAgentInput, pois: Sequence[POIInfo]) -> List[Attraction]:
        request = payload.request
        seen: Set[str] = set()
        scored: List[tuple[float, Attraction]] = []

        for poi in pois:
            if self._should_exclude(poi):
                continue

            dedupe_key = self._dedupe_key(poi)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            attraction = self._poi_to_attraction(poi, request.city)
            score = self._score_poi(request, payload.rag_context, payload.skills, poi)
            scored.append((score, attraction))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in scored[: payload.limit]]

    def _should_exclude(self, poi: POIInfo) -> bool:
        name = poi.name.strip()
        if not name:
            return True
        return any(keyword in name for keyword in EXCLUDED_NAME_KEYWORDS)

    def _score_poi(self, request, rag_context: str, skills: List[SelectedSkill], poi: POIInfo) -> float:
        text = f"{poi.name} {poi.type} {poi.address}".lower()
        score = 1.0
        skill_keys = {skill.key for skill in skills}

        for tag in request.preferences + request.travel_style:
            mapped_queries = TAG_QUERY_MAP.get(tag.lower(), [])
            if any(mapped.lower().replace("景点", "") in text for mapped in mapped_queries):
                score += 2.5
            if tag.lower() in text:
                score += 1.5

        if any(token in text for token in ("博物馆", "美术馆", "科技馆", "纪念馆")):
            score += 1.2

        if any(token in f"{request.free_text_input} {rag_context}".lower() for token in ("rain", "下雨", "雨天", "indoor", "室内")):
            if any(token in poi.name or token in poi.type for token in INDOOR_HINTS):
                score += 2.0

        companions = [companion.lower() for companion in request.companions]
        if any(group in companions for group in ("family", "儿童", "亲子")):
            if any(token in text for token in FAMILY_FRIENDLY_HINTS):
                score += 1.5

        if any(need.lower() in {"low walking load", "low walking", "wheelchair", "elderly"} for need in request.mobility_needs):
            if any(token.lower() in text for token in [item.lower() for item in LOW_WALKING_PENALTIES]):
                score -= 2.0

        if "rainy_day" in skill_keys and any(token in poi.name or token in poi.type for token in INDOOR_HINTS):
            score += 1.5
        if "family_friendly" in skill_keys and any(token in text for token in FAMILY_FRIENDLY_HINTS):
            score += 1.2
        if "low_mobility" in skill_keys:
            if any(token.lower() in text for token in [item.lower() for item in LOW_WALKING_PENALTIES]):
                score -= 1.5
            if any(token in poi.name or token in poi.type for token in INDOOR_HINTS):
                score += 0.8

        return score

    @staticmethod
    def _skill_query_boosts(skills: List[SelectedSkill]) -> List[str]:
        ordered: List[str] = []
        seen: Set[str] = set()
        for skill in skills:
            for query in skill.attraction_query_boosts:
                compact = query.strip()
                if compact and compact not in seen:
                    seen.add(compact)
                    ordered.append(compact)
        return ordered

    def _poi_to_attraction(self, poi: POIInfo, city: str) -> Attraction:
        category = poi.type.split(";")[0] if poi.type else "attraction"
        visit_duration = self._estimate_visit_duration(poi)
        ticket_price = self._estimate_ticket_price(poi)
        description = f"{poi.name}，位于{poi.address or city}，适合作为{category}类行程候选。"

        return Attraction(
            name=poi.name,
            address=poi.address or city,
            location=Location(
                longitude=poi.location.longitude,
                latitude=poi.location.latitude,
            ),
            visit_duration=visit_duration,
            description=description,
            category=category,
            poi_id=poi.id,
            ticket_price=ticket_price,
        )

    def _estimate_visit_duration(self, poi: POIInfo) -> int:
        text = f"{poi.name} {poi.type}"
        if any(token in text for token in ("博物馆", "美术馆", "科技馆", "纪念馆")):
            return 180
        if any(token in text for token in ("公园", "古镇", "步行街")):
            return 120
        return 150

    def _estimate_ticket_price(self, poi: POIInfo) -> int:
        text = f"{poi.name} {poi.type}"
        if any(token in text for token in ("博物馆", "纪念馆", "公园")):
            return 40
        if any(token in text for token in ("故宫", "长城", "景区", "乐园")):
            return 80
        return 50

    @staticmethod
    def _dedupe_key(poi: POIInfo) -> str:
        compact_name = re.sub(r"[()（）\s]+", "", poi.name.lower())
        compact_address = re.sub(r"\s+", "", poi.address.lower())
        return f"{compact_name}:{compact_address}"

    @staticmethod
    def _contains_cjk(text: str) -> bool:
        return any("\u4e00" <= char <= "\u9fff" for char in text)
