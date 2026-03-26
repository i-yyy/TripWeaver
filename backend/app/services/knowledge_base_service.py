"""本地旅游知识库服务（支持 Qdrant 入库与检索）。"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models

from ..config import get_settings
from .embedding_service import get_embedding_service


@dataclass
class DocumentChunk:
    """知识库切片。"""

    chunk_id: str
    doc_path: str
    city_hint: str
    content: str
    metadata: Dict[str, Any]


class KnowledgeBaseService:
    """本地知识库 + Qdrant 检索服务。"""

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self.settings = get_settings()
        self.root_dir = root_dir or (Path(__file__).resolve().parents[2] / "data" / "knowledge_base")
        self.embedding = get_embedding_service()
        self.client = QdrantClient(
            url=self.settings.qdrant_url,
            api_key=self.settings.qdrant_api_key or None,
            timeout=15,
        )

    # -----------------------
    # 文档加载与切片
    # -----------------------
    def list_documents(self, city: Optional[str] = None) -> List[Path]:
        if not self.root_dir.exists():
            return []
        docs = [
            path
            for path in self.root_dir.rglob("*.md")
            if path.is_file()
            and path.name.lower() != "readme.md"
            and not path.name.startswith("_")
        ]
        if city:
            city_token = city.lower().strip()
            docs = [path for path in docs if city_token in str(path).lower()]
        return sorted(docs)

    def load_documents(self, city: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        docs = self.list_documents(city=city)[:limit]
        data: List[Dict[str, Any]] = []
        for path in docs:
            text = self._safe_read(path)
            metadata, content = self._parse_frontmatter(text)
            data.append(
                {
                    "path": str(path),
                    "city_hint": path.parent.name,
                    "metadata": metadata,
                    "content": content.strip(),
                }
            )
        return data

    def split_to_chunks(self, city: Optional[str] = None, limit: int = 200) -> List[DocumentChunk]:
        docs = self.load_documents(city=city, limit=limit)
        chunks: List[DocumentChunk] = []

        for doc in docs:
            pieces = self._chunk_text(
                text=doc["content"],
                chunk_size=self.settings.rag_chunk_size,
                overlap=self.settings.rag_chunk_overlap,
            )
            for idx, piece in enumerate(pieces):
                seed = f"{doc['path']}::{idx}::{piece[:80]}"
                chunk_id = str(uuid.uuid5(uuid.NAMESPACE_URL, seed))
                metadata = dict(doc["metadata"])
                metadata.update(
                    {
                        "doc_path": doc["path"],
                        "city_hint": doc["city_hint"],
                        "chunk_index": idx,
                    }
                )
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        doc_path=doc["path"],
                        city_hint=doc["city_hint"],
                        content=piece,
                        metadata=metadata,
                    )
                )
        return chunks

    # -----------------------
    # Qdrant 入库与检索
    # -----------------------
    def ensure_collection(self) -> None:
        collection = self.settings.qdrant_collection_kb
        try:
            self.client.get_collection(collection)
            return
        except Exception:
            pass

        self.client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(
                size=self.embedding.vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def ingest_documents(self, city: Optional[str] = None, clear_collection: bool = False) -> Dict[str, Any]:
        collection = self.settings.qdrant_collection_kb
        try:
            if clear_collection:
                try:
                    self.client.delete_collection(collection)
                except Exception:
                    pass
            self.ensure_collection()
        except Exception as exc:
            return {
                "success": False,
                "message": f"Qdrant 不可用，未执行入库: {exc}",
                "document_count": 0,
                "chunk_count": 0,
                "embedding_mode": self.embedding.mode,
            }
        chunks = self.split_to_chunks(city=city)
        if not chunks:
            return {
                "success": True,
                "message": "未发现可入库文档",
                "document_count": 0,
                "chunk_count": 0,
                "embedding_mode": self.embedding.mode,
            }

        vectors = self.embedding.embed_texts([chunk.content for chunk in chunks])
        points: List[models.PointStruct] = []
        for chunk, vector in zip(chunks, vectors):
            points.append(
                models.PointStruct(
                    id=chunk.chunk_id,
                    vector=vector,
                    payload={
                        "content": chunk.content,
                        **chunk.metadata,
                    },
                )
            )

        batch_size = 64
        try:
            for i in range(0, len(points), batch_size):
                self.client.upsert(
                    collection_name=collection,
                    points=points[i : i + batch_size],
                    wait=True,
                )
        except Exception as exc:
            return {
                "success": False,
                "message": f"向量入库失败: {exc}",
                "document_count": len({chunk.doc_path for chunk in chunks}),
                "chunk_count": 0,
                "embedding_mode": self.embedding.mode,
            }

        return {
            "success": True,
            "message": "知识库入库完成",
            "document_count": len({chunk.doc_path for chunk in chunks}),
            "chunk_count": len(chunks),
            "embedding_mode": self.embedding.mode,
            "collection": collection,
        }

    def search(
        self,
        query: str,
        city: Optional[str] = None,
        top_k: Optional[int] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            return []
        limit = top_k or self.settings.rag_top_k

        try:
            self.ensure_collection()

            query_vector = self.embedding.embed_text(query)
            must_conditions: List[models.FieldCondition] = self._build_must_conditions(
                city=city,
                metadata_filters=metadata_filters,
            )

            query_filter = models.Filter(must=must_conditions) if must_conditions else None
            search_result = self.client.search(
                collection_name=self.settings.qdrant_collection_kb,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )

            results: List[Dict[str, Any]] = []
            for item in search_result:
                payload = dict(item.payload or {})
                score = float(item.score or 0.0)
                if score < self.settings.rag_min_score:
                    continue
                results.append(
                    {
                        "score": score,
                        "content": payload.get("content", ""),
                        "metadata": payload,
                    }
                )
            if results:
                return results
        except Exception as exc:
            print(f"Qdrant 检索失败，自动切换本地回退检索: {exc}")

        return self._fallback_search(
            query=query,
            city=city,
            top_k=limit,
            metadata_filters=metadata_filters,
        )

    # -----------------------
    # 工具方法
    # -----------------------
    @staticmethod
    def _safe_read(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="gbk", errors="ignore")

    @staticmethod
    def _parse_frontmatter(text: str) -> tuple[Dict[str, Any], str]:
        # 兼容无 frontmatter 文档
        if not text.startswith("---"):
            return {}, text

        # 优先使用 python-frontmatter 解析完整 YAML
        try:
            import frontmatter  # type: ignore

            post = frontmatter.loads(text)
            metadata = {
                str(key): KnowledgeBaseService._normalize_metadata_value(value)
                for key, value in dict(post.metadata or {}).items()
            }
            return metadata, str(post.content or "")
        except Exception:
            pass

        parts = re.split(r"^---\s*$", text, maxsplit=2, flags=re.MULTILINE)
        if len(parts) < 3:
            return {}, text

        header = parts[1]
        content = parts[2]

        # 次优先使用 PyYAML，支持多行 list/dict
        try:
            import yaml  # type: ignore

            loaded = yaml.safe_load(header) or {}
            if isinstance(loaded, dict):
                metadata = {
                    str(key): KnowledgeBaseService._normalize_metadata_value(value)
                    for key, value in loaded.items()
                }
                return metadata, content
        except Exception:
            pass

        metadata: Dict[str, Any] = {}
        for line in header.splitlines():
            raw = line.strip()
            if not raw or ":" not in raw:
                continue
            key, value = raw.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                metadata[key] = [
                    item.strip().strip("'\"")
                    for item in inner.split(",")
                    if item.strip()
                ]
            else:
                metadata[key] = value.strip("'\"")
        return metadata, content

    @staticmethod
    def _normalize_metadata_value(value: Any) -> Any:
        if value is None:
            return ""
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            return [KnowledgeBaseService._normalize_metadata_value(item) for item in value]
        if isinstance(value, dict):
            return {
                str(key): KnowledgeBaseService._normalize_metadata_value(item)
                for key, item in value.items()
            }
        return str(value)

    @staticmethod
    def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
        clean = re.sub(r"\s+", " ", text).strip()
        if not clean:
            return []
        if len(clean) <= chunk_size:
            return [clean]

        chunks: List[str] = []
        start = 0
        while start < len(clean):
            end = min(len(clean), start + chunk_size)
            chunk = clean[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(clean):
                break
            start = max(0, end - overlap)
        return chunks

    def _fallback_search(
        self,
        query: str,
        city: Optional[str],
        top_k: int,
        metadata_filters: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        docs = self.load_documents(city=city, limit=80)
        keywords = [token for token in re.split(r"[\s,，。；;:：]+", query.lower()) if token]
        scored: List[Dict[str, Any]] = []
        for doc in docs:
            if not self._metadata_match(doc["metadata"], metadata_filters):
                continue
            text = str(doc["content"])
            low = text.lower()
            hit = 0
            for keyword in keywords:
                if keyword and keyword in low:
                    hit += 1
            if hit <= 0:
                continue
            preview = text.replace("\n", " ").strip()[:260]
            scored.append(
                {
                    "score": float(hit) / max(1.0, len(keywords)),
                    "content": preview,
                    "metadata": {
                        **doc["metadata"],
                        "doc_path": doc["path"],
                        "city_hint": doc["city_hint"],
                        "retrieval_mode": "fallback",
                    },
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _build_must_conditions(
        city: Optional[str],
        metadata_filters: Optional[Dict[str, Any]],
    ) -> List[models.FieldCondition]:
        conditions: List[models.FieldCondition] = []
        if city:
            conditions.append(
                models.FieldCondition(
                    key="city_hint",
                    match=models.MatchValue(value=city),
                )
            )
        if not metadata_filters:
            return conditions

        for key, value in metadata_filters.items():
            if value is None:
                continue
            if isinstance(value, list):
                clean = [str(item).strip() for item in value if str(item).strip()]
                if not clean:
                    continue
                conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchAny(any=clean),
                    )
                )
            else:
                text = str(value).strip()
                if not text:
                    continue
                conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=text),
                    )
                )
        return conditions

    @staticmethod
    def _metadata_match(metadata: Dict[str, Any], metadata_filters: Optional[Dict[str, Any]]) -> bool:
        if not metadata_filters:
            return True

        for key, value in metadata_filters.items():
            if value is None:
                continue
            actual = metadata.get(key)
            if isinstance(value, list):
                expected = [str(item).lower().strip() for item in value if str(item).strip()]
                if not expected:
                    continue
                if isinstance(actual, list):
                    actual_values = [str(item).lower().strip() for item in actual]
                elif actual is None:
                    actual_values = []
                else:
                    actual_values = [str(actual).lower().strip()]
                if not any(token in actual_values for token in expected):
                    return False
            else:
                expected_one = str(value).lower().strip()
                if not expected_one:
                    continue
                if isinstance(actual, list):
                    actual_values = [str(item).lower().strip() for item in actual]
                    if expected_one not in actual_values:
                        return False
                else:
                    if str(actual or "").lower().strip() != expected_one:
                        return False
        return True


_kb_service: Optional[KnowledgeBaseService] = None


def get_knowledge_base_service() -> KnowledgeBaseService:
    global _kb_service
    if _kb_service is None:
        _kb_service = KnowledgeBaseService()
    return _kb_service
