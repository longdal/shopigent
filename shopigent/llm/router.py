from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

import httpx

from shopigent.config import settings

logger = logging.getLogger(__name__)


class LLMTaskType(Enum):
    QUERY_EXPAND = "query_expand"
    PRODUCT_ANALYZE = "product_analyze"
    REPORT_GENERATE = "report_generate"
    DOM_PARSE = "dom_parse"


@dataclass(frozen=True)
class ModelConfig:
    primary_model: str
    fallback_model: str
    timeout_sec: int = 30


_DEFAULT_ROUTING: dict[LLMTaskType, ModelConfig] = {
    LLMTaskType.QUERY_EXPAND: ModelConfig(
        primary_model="ollama/qwen2.5:7b",
        fallback_model="gemini/gemini-2.0-flash",
        timeout_sec=15,
    ),
    LLMTaskType.PRODUCT_ANALYZE: ModelConfig(
        primary_model="ollama/qwen2.5:7b",
        fallback_model="gemini/gemini-2.0-flash",
        timeout_sec=30,
    ),
    LLMTaskType.REPORT_GENERATE: ModelConfig(
        primary_model="gemini/gemini-2.0-flash",
        fallback_model="gpt-4o-mini",
        timeout_sec=60,
    ),
    LLMTaskType.DOM_PARSE: ModelConfig(
        primary_model="gemini/gemini-2.0-flash",
        fallback_model="gpt-4o-mini",
        timeout_sec=30,
    ),
}


class LLMRouter:
    def __init__(
        self,
        routing_table: dict[LLMTaskType, ModelConfig] | None = None,
    ):
        self._routing = routing_table or _DEFAULT_ROUTING
        self._ollama_base_url = settings.ollama_base_url

    def get_model(self, task_type: LLMTaskType) -> str:
        config = self._routing[task_type]
        if config.primary_model.startswith("ollama/"):
            if self._is_ollama_available():
                return config.primary_model
            logger.info(
                "Ollama unavailable for %s, falling back to %s",
                task_type.value,
                config.fallback_model,
            )
            return config.fallback_model
        return config.primary_model

    def get_config(self, task_type: LLMTaskType) -> ModelConfig:
        return self._routing[task_type]

    def _is_ollama_available(self) -> bool:
        try:
            resp = httpx.get(self._ollama_base_url, timeout=2)
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
