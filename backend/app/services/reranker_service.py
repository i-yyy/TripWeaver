"""重排服务：对召回结果进行二次排序。"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional

from ..config import get_settings


class RerankerService:
    """召回结果重排。

    优先尝试使用 CrossEncoder 进行重排；
    如果不可用，自动降级为关键词重叠打分 + 原始召回分融合。
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_name = self.settings.reranker_model
        self._model = None
        self._mode = "fallback"
        self._init_model()

    def _init_model(self) -> None:
        try:
            from sentence_transformers import CrossEncoder  # type: ignore

            self._model = CrossEncoder(self.model_name)
            self._mode = "cross-encoder"
            print(f"重排模型加载成功: {self.model_name}")
        except Exception as exc:
            self._model = None
            self._mode = "fallback"
            print(f"重排模型加载失败，使用回退重排: {exc}")

    @property
    def mode(self) -> str:
        return self._mode

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_n: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        limit = top_n or self.settings.rag_rerank_top_k

        if self._model is not None:
            try:
                pairs = [(query, str(item.get("content", ""))) for item in candidates]
                scores = self._model.predict(pairs)
                merged = []
                for item, score in zip(candidates, scores):
                    base_score = float(item.get("score", 0.0))
                    rerank_score = float(score)
                    final_score = 0.65 * self._sigmoid(rerank_score) + 0.35 * base_score
                    merged.append(
                        {
                            **item,
                            "base_score": base_score,
                            "rerank_score": float(rerank_score),
                            "final_score": float(final_score),
                            "rerank_mode": self._mode,
                        }
                    )
                merged.sort(key=lambda row: row["final_score"], reverse=True)
                return merged[:limit]
            except Exception as exc:
                print(f"模型重排失败，切换回退重排: {exc}")

        fallback = []
        for item in candidates:
            base_score = float(item.get("score", 0.0))
            overlap = self._keyword_overlap_score(query, str(item.get("content", "")))
            final_score = 0.5 * base_score + 0.5 * overlap
            fallback.append(
                {
                    **item,
                    "base_score": base_score,
                    "rerank_score": overlap,
                    "final_score": float(final_score),
                    "rerank_mode": "fallback",
                }
            )
        fallback.sort(key=lambda row: row["final_score"], reverse=True)
        return fallback[:limit]

    @staticmethod
    def _sigmoid(value: float) -> float:
        try:
            return 1.0 / (1.0 + math.exp(-value))
        except OverflowError:
            return 0.0 if value < 0 else 1.0

    @staticmethod
    def _keyword_overlap_score(query: str, content: str) -> float:
        q_tokens = [token for token in re.split(r"[\s,，。；;:：]+", query.lower()) if token]
        c_text = content.lower()
        if not q_tokens:
            return 0.0
        hit = sum(1 for token in q_tokens if token in c_text)
        return float(hit) / float(len(q_tokens))


_reranker_service: Optional[RerankerService] = None


def get_reranker_service() -> RerankerService:
    global _reranker_service
    if _reranker_service is None:
        _reranker_service = RerankerService()
    return _reranker_service
