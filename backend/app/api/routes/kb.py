"""知识库管理路由。"""

from __future__ import annotations

from statistics import mean
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...services.knowledge_base_service import get_knowledge_base_service
from ...services.reranker_service import get_reranker_service
from ...services.security_service import require_developer_user

router = APIRouter(prefix="/kb", tags=["知识库"], dependencies=[Depends(require_developer_user)])


class KBIngestRequest(BaseModel):
    city: str | None = Field(default=None, description="可选：只入库指定城市文档")
    clear_collection: bool = Field(default=False, description="入库前是否清空集合")


class KBEvaluateRequest(BaseModel):
    query: str = Field(..., description="评估查询词")
    city: str | None = Field(default=None, description="可选：城市过滤")
    top_k: int = Field(default=6, ge=1, le=20, description="返回数量")
    tags: str | None = Field(default=None, description="逗号分隔标签过滤")
    crowd_type: str | None = Field(default=None, description="逗号分隔人群过滤")
    budget_level: str | None = Field(default=None, description="预算过滤")
    expected_terms: List[str] = Field(default_factory=list, description="可选：期望命中关键词")
    rerank: bool = Field(default=True, description="是否执行重排")


@router.get("/status")
async def kb_status(city: str | None = None) -> dict:
    service = get_knowledge_base_service()
    docs = service.list_documents(city=city)
    return {
        "status": "正常",
        "message": "知识库状态正常",
        "city_filter": city,
        "document_count": len(docs),
        "sample_documents": [str(path) for path in docs[:5]],
    }


@router.post("/ingest")
async def kb_ingest(payload: KBIngestRequest) -> dict:
    try:
        result = get_knowledge_base_service().ingest_documents(
            city=payload.city,
            clear_collection=payload.clear_collection,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"知识库入库失败: {exc}") from exc


@router.get("/search")
async def kb_search(
    query: str,
    city: str | None = None,
    top_k: int = 6,
    tags: str | None = None,
    crowd_type: str | None = None,
    budget_level: str | None = None,
    rerank: bool = True,
) -> dict:
    if not query.strip():
        raise HTTPException(status_code=400, detail="query 不能为空")
    try:
        metadata_filters = _build_metadata_filters(tags=tags, crowd_type=crowd_type, budget_level=budget_level)

        results = get_knowledge_base_service().search(
            query=query,
            city=city,
            top_k=top_k * 2 if rerank else top_k,
            metadata_filters=metadata_filters or None,
        )
        if rerank:
            results = get_reranker_service().rerank(query=query, candidates=results, top_n=top_k)
        return {
            "status": "正常",
            "message": "检索成功",
            "query": query,
            "count": len(results),
            "metadata_filters": metadata_filters,
            "rerank_mode": get_reranker_service().mode if rerank else "关闭",
            "items": results,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"知识库检索失败: {exc}") from exc


@router.post("/evaluate")
async def kb_evaluate(payload: KBEvaluateRequest) -> dict:
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="query 不能为空")

    try:
        metadata_filters = _build_metadata_filters(
            tags=payload.tags,
            crowd_type=payload.crowd_type,
            budget_level=payload.budget_level,
        )
        top_k = max(1, min(20, int(payload.top_k)))
        recall_limit = top_k * 2 if payload.rerank else top_k

        kb_service = get_knowledge_base_service()
        recall_items = kb_service.search(
            query=payload.query,
            city=payload.city,
            top_k=recall_limit,
            metadata_filters=metadata_filters or None,
        )
        final_items = (
            get_reranker_service().rerank(query=payload.query, candidates=recall_items, top_n=top_k)
            if payload.rerank
            else recall_items[:top_k]
        )

        expected_terms = [item.strip().lower() for item in payload.expected_terms if item.strip()]
        expected_hit_count = sum(1 for item in final_items if _matches_expected_terms(item, expected_terms))
        scores = [_item_score(item) for item in final_items]
        recall_scores = [_item_score(item) for item in recall_items]

        return {
            "status": "正常",
            "message": "评估完成",
            "query": payload.query,
            "city_filter": payload.city,
            "metadata_filters": metadata_filters,
            "metrics": {
                "recall_count": len(recall_items),
                "final_count": len(final_items),
                "expected_term_count": len(expected_terms),
                "expected_hit_count": expected_hit_count,
                "expected_hit_rate": round(expected_hit_count / max(1, len(final_items)), 4),
                "score_avg": round(mean(scores), 4) if scores else 0.0,
                "score_max": round(max(scores), 4) if scores else 0.0,
                "score_min": round(min(scores), 4) if scores else 0.0,
                "top1_gain": round((scores[0] if scores else 0.0) - (recall_scores[0] if recall_scores else 0.0), 4),
                "rerank_mode": get_reranker_service().mode if payload.rerank else "关闭",
            },
            "items": [_to_preview_item(item, idx) for idx, item in enumerate(final_items, start=1)],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"知识库评估失败: {exc}") from exc


def _build_metadata_filters(tags: str | None, crowd_type: str | None, budget_level: str | None) -> Dict[str, Any]:
    metadata_filters: Dict[str, Any] = {}
    if tags:
        metadata_filters["tags"] = [item.strip() for item in tags.split(",") if item.strip()]
    if crowd_type:
        metadata_filters["crowd_type"] = [item.strip() for item in crowd_type.split(",") if item.strip()]
    if budget_level:
        metadata_filters["budget_level"] = budget_level.strip()
    return metadata_filters


def _item_score(item: Dict[str, Any]) -> float:
    return float(item.get("final_score", item.get("score", 0.0)))


def _matches_expected_terms(item: Dict[str, Any], expected_terms: List[str]) -> bool:
    if not expected_terms:
        return False

    metadata = dict(item.get("metadata", {}))
    text_parts = [
        str(item.get("content", "")),
        str(metadata.get("title", "")),
        str(metadata.get("city_hint", "")),
        str(metadata.get("crowd_type", "")),
        str(metadata.get("budget_level", "")),
    ]
    tags = metadata.get("tags", [])
    if isinstance(tags, list):
        text_parts.extend([str(tag) for tag in tags])
    else:
        text_parts.append(str(tags))

    full_text = " ".join(text_parts).lower()
    return any(term in full_text for term in expected_terms)


def _to_preview_item(item: Dict[str, Any], rank: int) -> Dict[str, Any]:
    metadata = dict(item.get("metadata", {}))
    content = str(item.get("content", "")).replace("\n", " ").strip()
    return {
        "rank": rank,
        "score": round(_item_score(item), 4),
        "base_score": round(float(item.get("base_score", item.get("score", 0.0))), 4),
        "rerank_score": round(float(item.get("rerank_score", 0.0)), 4),
        "rerank_mode": item.get("rerank_mode", "none"),
        "city_hint": metadata.get("city_hint"),
        "source_doc": metadata.get("doc_path"),
        "snippet": content[:180],
        "metadata": metadata,
    }
