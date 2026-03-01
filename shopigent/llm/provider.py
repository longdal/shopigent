"""
LLM 추상화 레이어.

LiteLLM을 통해 Claude, GPT-4, Gemini, Ollama 등 다양한 모델을
단일 인터페이스로 사용합니다.

모델 전환: .env의 LLM_PRIMARY_MODEL 값만 변경하면 됩니다.
"""

import logging
from typing import Any

import litellm

from shopigent.config import settings

logger = logging.getLogger(__name__)

# LiteLLM 로그 레벨 조정
litellm.set_verbose = False


class LLMProvider:
    def __init__(self):
        self.primary_model = settings.llm_primary_model
        self.fallback_model = settings.llm_fallback_model

        # API 키 설정
        if settings.anthropic_api_key:
            litellm.anthropic_key = settings.anthropic_api_key
        if settings.openai_api_key:
            litellm.openai_key = settings.openai_api_key

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2048,
        use_fallback: bool = True,
    ) -> str:
        """LLM 텍스트 완성. 실패 시 fallback 모델 사용."""
        try:
            response = await litellm.acompletion(
                model=self.primary_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"Primary LLM 실패 ({self.primary_model}): {e}")
            if use_fallback and self.fallback_model:
                return await self._complete_with_fallback(messages, temperature, max_tokens)
            raise

    async def _complete_with_fallback(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        logger.info(f"Fallback LLM 사용: {self.fallback_model}")
        response = await litellm.acompletion(
            model=self.fallback_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def complete_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> Any:
        """JSON 형식 응답을 요청하고 파싱하여 반환."""
        import json

        text = await self.complete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # ```json ... ``` 블록 제거
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        return json.loads(text)


# 싱글톤 인스턴스
llm_provider = LLMProvider()
