"""RAG 检索编排服务。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..config import get_settings
from ..models.schemas import MemoryFact, RecommendationReason, TripRequest
from .knowledge_base_service import get_knowledge_base_service
from .reranker_service import get_reranker_service


class RetrieverService:
    """负责召回、重排和 RAG 上下文拼装。"""

    def __init__(self) -> None:
        self.settings = get_settings()

    def retrieve_trip_context(
        self,
        request: TripRequest,
        profile_context: str = "",
        memories: Optional[List[MemoryFact]] = None,
    ) -> str:
        bundle = self.retrieve_trip_bundle(
            request=request,
            profile_context=profile_context,
            memories=memories,
        )
        return str(bundle.get("context_text", ""))

    def retrieve_trip_bundle(
        self,
        request: TripRequest,
        profile_context: str = "",
        memories: Optional[List[MemoryFact]] = None,
    ) -> Dict[str, Any]:
        query = self._build_query(request)
        metadata_filters = self._build_metadata_filters(request)

        recall_results = get_knowledge_base_service().search(
            query=query,
            city=request.city,
            top_k=self.settings.rag_recall_top_k,
            metadata_filters=metadata_filters,
        )

        ranked_results = get_reranker_service().rerank(
            query=query,
            candidates=recall_results,
            top_n=self.settings.rag_rerank_top_k,
        )

        context_text = self._build_context_text(
            profile_context=profile_context,
            memories=memories or [],
            ranked_results=ranked_results,
        )
        recommendation_reasons = self._build_recommendation_reasons(
            profile_context=profile_context,
            memories=memories or [],
            ranked_results=ranked_results,
            limit=max(3, min(8, self.settings.rag_rerank_top_k)),
        )

        return {
            "query": query,
            "metadata_filters": metadata_filters,
            "recall_count": len(recall_results),
            "rerank_count": len(ranked_results),
            "recall_items": recall_results,
            "rerank_items": ranked_results,
            "context_text": context_text,
            "recommendation_reasons": recommendation_reasons,
        }

    @staticmethod
    def _build_query(request: TripRequest) -> str:
        sections = [
            f"城市:{request.city}",
            f"出行天数:{request.travel_days}",
            f"交通:{request.transportation}",
            f"住宿:{request.accommodation}",
            f"预算:{request.budget_level or '未知'}",
            f"偏好:{','.join(request.preferences) if request.preferences else '无'}",
            f"风格:{','.join(request.travel_style) if request.travel_style else '无'}",
            f"同行:{','.join(request.companions) if request.companions else '无'}",
            f"饮食限制:{','.join(request.dietary_restrictions) if request.dietary_restrictions else '无'}",
            f"行动需求:{','.join(request.mobility_needs) if request.mobility_needs else '无'}",
            f"额外要求:{request.free_text_input or '无'}",
        ]
        return "；".join(sections)

    @staticmethod
    def _build_metadata_filters(request: TripRequest) -> Dict[str, Any]:
        filters: Dict[str, Any] = {}
        tags = list(dict.fromkeys(request.preferences + request.travel_style))
        if tags:
            filters["tags"] = tags
        if request.companions:
            filters["crowd_type"] = request.companions
        if request.budget_level:
            filters["budget_level"] = request.budget_level
        return filters

    @staticmethod
    def _build_context_text(
        profile_context: str,
        memories: List[MemoryFact],
        ranked_results: List[Dict[str, Any]],
    ) -> str:
        memory_lines = []
        for memory in memories:
            summary = memory.summary or memory.content
            memory_lines.append(f"- [{memory.memory_type}] {summary}")

        kb_lines = []
        for item in ranked_results:
            content = RetrieverService._short_text(str(item.get("content", "")), 220)
            city_hint = str(item.get("metadata", {}).get("city_hint", "未知"))
            final_score = float(item.get("final_score", item.get("score", 0.0)))
            mode = str(item.get("rerank_mode", "none"))
            kb_lines.append(f"- (综合分 {final_score:.3f}, 模式 {mode}) {city_hint}: {content}")

        if not kb_lines and not memory_lines and not profile_context:
            return ""

        blocks = ["检索增强上下文（RAG）:"]
        if profile_context:
            blocks.append(profile_context)
        if memory_lines:
            blocks.append("相关用户记忆:\n" + "\n".join(memory_lines))
        if kb_lines:
            blocks.append("本地知识库命中片段（已重排）:\n" + "\n".join(kb_lines))
        else:
            blocks.append("本地知识库未命中高相关片段。")
        return "\n\n".join(blocks)

    @staticmethod
    def _build_recommendation_reasons(
        profile_context: str,
        memories: List[MemoryFact],
        ranked_results: List[Dict[str, Any]],
        limit: int = 6,
    ) -> List[Dict[str, Any]]:
        reasons: List[RecommendationReason] = []

        if profile_context.strip():
            first_line = profile_context.strip().splitlines()[0]
            reasons.append(
                RecommendationReason(
                    source_type="profile",
                    title="用户画像偏好",
                    reason=RetrieverService._short_text(first_line, 90),
                    snippet=RetrieverService._short_text(profile_context, 220),
                    score=1.0,
                    rerank_mode="profile-context",
                    metadata={},
                )
            )

        for memory in memories[:2]:
            summary = memory.summary or memory.content
            reasons.append(
                RecommendationReason(
                    source_type="memory",
                    title=f"历史偏好记忆（{memory.memory_type}）",
                    reason=RetrieverService._short_text(summary, 90),
                    snippet=RetrieverService._short_text(memory.content, 180),
                    score=float(memory.importance_score or 0.0),
                    rerank_mode="memory-recall",
                    metadata={
                        "city": memory.city,
                        "tags": memory.tags,
                    },
                )
            )

        for item in ranked_results:
            metadata = dict(item.get("metadata", {}))
            city_hint = str(metadata.get("city_hint", "未知城市"))
            source_doc = metadata.get("doc_path")
            tags = metadata.get("tags", [])
            if not isinstance(tags, list):
                tags = [tags] if tags else []

            reason_parts = []
            if tags:
                reason_parts.append(f"标签匹配: {','.join([str(tag) for tag in tags[:4]])}")
            crowd_type = metadata.get("crowd_type")
            if crowd_type:
                reason_parts.append(f"适配人群: {crowd_type}")
            budget_level = metadata.get("budget_level")
            if budget_level:
                reason_parts.append(f"预算层级: {budget_level}")
            if not reason_parts:
                reason_parts.append("与当前行程需求语义相近")

            reason = "；".join(reason_parts)
            content = RetrieverService._short_text(str(item.get("content", "")), 160)
            score = float(item.get("final_score", item.get("score", 0.0)))
            rerank_mode = str(item.get("rerank_mode", "none"))
            title = f"{city_hint} 本地知识命中"

            reasons.append(
                RecommendationReason(
                    source_type="knowledge_base",
                    title=title,
                    reason=reason,
                    snippet=content,
                    score=score,
                    rerank_mode=rerank_mode,
                    source_doc=str(source_doc) if source_doc else None,
                    metadata=metadata,
                )
            )

        compact = reasons[:limit]
        return [item.model_dump() for item in compact]

    @staticmethod
    def _short_text(text: str, limit: int) -> str:
        compact = str(text).replace("\n", " ").strip()
        if len(compact) <= limit:
            return compact
        return compact[: max(0, limit - 1)] + "…"


_retriever_service: Optional[RetrieverService] = None


def get_retriever_service() -> RetrieverService:
    global _retriever_service
    if _retriever_service is None:
        _retriever_service = RetrieverService()
    return _retriever_service
