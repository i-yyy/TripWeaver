"""应用配置。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# 优先加载项目根目录 .env
load_dotenv()

# 可选加载 HelloAgents 的 .env 作为兜底配置
helloagents_env = Path(__file__).parent.parent.parent.parent / "HelloAgents" / ".env"
if helloagents_env.exists():
    load_dotenv(helloagents_env, override=False)


class Settings(BaseSettings):
    """运行时配置。"""

    # 应用信息
    app_name: str = "HelloAgents 智能旅行助手"
    app_version: str = "1.0.0"
    debug: bool = False

    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS 配置
    cors_origins: str = (
        "http://localhost:5173,"
        "http://localhost:3000,"
        "http://127.0.0.1:5173,"
        "http://127.0.0.1:3000"
    )

    # 外部 API
    amap_api_key: str = ""
    unsplash_access_key: str = ""
    unsplash_secret_key: str = ""

    # LLM
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"

    # 持久化
    database_url: str = "sqlite:///./trip_planner.db"

    # 向量检索 / RAG
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection_kb: str = "trip_kb"
    qdrant_collection_memory: str = "trip_memory"
    embedding_model: str = "BAAI/bge-m3"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    embedding_vector_size: int = 1024
    rag_chunk_size: int = 700
    rag_chunk_overlap: int = 120
    rag_top_k: int = 6
    rag_recall_top_k: int = 12
    rag_rerank_top_k: int = 6
    rag_min_score: float = 0.0

    # 日志
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    def get_cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()


def get_settings() -> Settings:
    return settings


def validate_config() -> bool:
    """校验关键配置。"""
    errors = []
    warnings = []

    if not settings.amap_api_key:
        errors.append("AMAP_API_KEY 未配置。")

    llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not llm_api_key:
        warnings.append("LLM_API_KEY/OPENAI_API_KEY 未配置，LLM 功能可能不可用。")

    if errors:
        error_msg = "配置错误:\n" + "\n".join(f"  - {msg}" for msg in errors)
        raise ValueError(error_msg)

    if warnings:
        print("\n配置告警:")
        for warning in warnings:
            print(f"  - {warning}")

    return True


def print_config() -> None:
    """打印生效配置（不输出敏感值）。"""
    print(f"应用: {settings.app_name}")
    print(f"版本: {settings.app_version}")
    print(f"服务地址: {settings.host}:{settings.port}")
    print(f"已配置高德 Key: {'是' if settings.amap_api_key else '否'}")

    llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    llm_base_url = os.getenv("LLM_BASE_URL") or settings.openai_base_url
    llm_model = os.getenv("LLM_MODEL_ID") or settings.openai_model

    print(f"已配置 LLM Key: {'是' if llm_api_key else '否'}")
    print(f"LLM 地址: {llm_base_url}")
    print(f"LLM 模型: {llm_model}")
    print(f"数据库: {settings.database_url}")
    print(f"Qdrant 地址: {settings.qdrant_url}")
    print(f"知识库集合: {settings.qdrant_collection_kb}")
    print(f"记忆库集合: {settings.qdrant_collection_memory}")
    print(f"向量模型: {settings.embedding_model}")
    print(f"日志级别: {settings.log_level}")
