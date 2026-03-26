"""文本向量化服务。"""

from __future__ import annotations

import hashlib
import math
from typing import List, Optional

from ..config import get_settings


class EmbeddingService:
    """统一的向量化服务。

    优先使用 `sentence-transformers` 模型；
    如果模型不可用，自动退化到哈希向量，保证系统可运行。
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.embedding_model
        self.default_dim = settings.embedding_vector_size
        self._model = None
        self._model_dim: Optional[int] = None
        self._mode = "hash"
        self._init_model()

    def _init_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer(self.model_name)
            self._mode = "model"
            sample = self._model.encode(["向量维度探测"], normalize_embeddings=True)
            if sample is not None and len(sample) > 0:
                self._model_dim = int(len(sample[0]))
            print(f"向量服务已加载模型: {self.model_name}，维度: {self.vector_size}")
        except Exception as exc:
            self._model = None
            self._mode = "hash"
            self._model_dim = None
            print(f"向量模型加载失败，使用哈希向量兜底: {exc}")

    @property
    def vector_size(self) -> int:
        return self._model_dim or self.default_dim

    @property
    def mode(self) -> str:
        return self._mode

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self._model is not None:
            vectors = self._model.encode(texts, normalize_embeddings=True).tolist()
            return [[float(v) for v in vec] for vec in vectors]
        return [self._hash_embedding(text, self.vector_size) for text in texts]

    def embed_text(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]

    @staticmethod
    def _hash_embedding(text: str, dim: int) -> List[float]:
        if dim <= 0:
            dim = 256
        values = [0.0 for _ in range(dim)]
        tokens = [token for token in text.replace("\n", " ").split(" ") if token]
        if not tokens:
            return values

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8", errors="ignore")).hexdigest()
            idx = int(digest[:8], 16) % dim
            sign = 1.0 if int(digest[8:10], 16) % 2 == 0 else -1.0
            weight = (int(digest[10:14], 16) % 1000) / 1000.0
            values[idx] += sign * weight

        # L2 归一化，保持可比较性
        norm = math.sqrt(sum(v * v for v in values))
        if norm > 1e-8:
            values = [v / norm for v in values]
        return values


_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
