"""LLM service helpers."""

from __future__ import annotations

from typing import Any, Optional

from hello_agents import HelloAgentsLLM

_llm_instance: Optional[HelloAgentsLLM] = None


def _safe_attr(obj: Any, attr_name: str, default: str = "unknown") -> str:
    try:
        value = getattr(obj, attr_name, default)
        return str(value)
    except Exception:
        return default


def get_llm() -> HelloAgentsLLM:
    """Return singleton LLM client."""
    global _llm_instance

    if _llm_instance is None:
        _llm_instance = HelloAgentsLLM()

        provider = _safe_attr(_llm_instance, "provider")
        model = _safe_attr(_llm_instance, "model")
        print("LLM service initialized")
        print(f"  provider: {provider}")
        print(f"  model: {model}")

    return _llm_instance


def reset_llm() -> None:
    """Reset LLM singleton (mainly for tests)."""
    global _llm_instance
    _llm_instance = None
