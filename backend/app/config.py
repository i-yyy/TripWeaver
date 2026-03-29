"""Application configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings

APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
DEFAULT_DB_PATH = (BACKEND_DIR / "trip_planner.db").resolve()


def _load_env_files() -> None:
    env_candidates = [
        PROJECT_ROOT / ".env",
        BACKEND_DIR / ".env",
        PROJECT_ROOT / "HelloAgents" / ".env",
    ]
    for env_path in env_candidates:
        if env_path.exists():
            load_dotenv(env_path, override=False)


_load_env_files()


class Settings(BaseSettings):
    """Runtime settings."""

    app_name: str = "HelloAgents Travel Planner"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    cors_origins: str = (
        "http://localhost:5173,"
        "http://localhost:3000,"
        "http://127.0.0.1:5173,"
        "http://127.0.0.1:3000"
    )

    amap_api_key: str = ""
    amap_provider: str = "http"
    amap_http_timeout: float = 10.0
    unsplash_access_key: str = ""
    unsplash_secret_key: str = ""

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"
    jwt_secret_key: str = "dev-secret-key-change-me-before-production-1234567890"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7

    database_url: str = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"

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

    log_level: str = "INFO"

    class Config:
        case_sensitive = False
        extra = "ignore"

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_value(cls, value: object) -> object:
        """Accept common environment-style debug flags."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return value

    def get_cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()


def get_settings() -> Settings:
    return settings


def validate_config() -> bool:
    """Validate critical runtime settings."""
    errors: List[str] = []
    warnings: List[str] = []

    if not settings.amap_api_key:
        errors.append("AMAP_API_KEY is not configured.")

    llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not llm_api_key:
        warnings.append("LLM_API_KEY/OPENAI_API_KEY is not configured; LLM features may be unavailable.")

    if errors:
        error_msg = "Configuration errors:\n" + "\n".join(f"  - {msg}" for msg in errors)
        raise ValueError(error_msg)

    if warnings:
        print("\nConfiguration warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    return True


def print_config() -> None:
    """Print effective non-sensitive settings."""
    print(f"App: {settings.app_name}")
    print(f"Version: {settings.app_version}")
    print(f"Server: {settings.host}:{settings.port}")
    print(f"AMap key configured: {'yes' if settings.amap_api_key else 'no'}")
    print(f"AMap provider: {settings.amap_provider}")
    print(f"AMap HTTP timeout: {settings.amap_http_timeout}")

    llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    llm_base_url = os.getenv("LLM_BASE_URL") or settings.openai_base_url
    llm_model = os.getenv("LLM_MODEL_ID") or settings.openai_model

    print(f"LLM key configured: {'yes' if llm_api_key else 'no'}")
    print(f"LLM base URL: {llm_base_url}")
    print(f"LLM model: {llm_model}")
    print(f"Database: {settings.database_url}")
    print(f"Qdrant URL: {settings.qdrant_url}")
    print(f"Knowledge collection: {settings.qdrant_collection_kb}")
    print(f"Memory collection: {settings.qdrant_collection_memory}")
    print(f"Embedding model: {settings.embedding_model}")
    print(f"Log level: {settings.log_level}")
