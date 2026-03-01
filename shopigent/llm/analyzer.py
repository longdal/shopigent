import logging
from dataclasses import dataclass

from shopigent.llm.prompts.analyzer_prompts import (
    PRODUCT_ANALYZER_SYSTEM_PROMPT,
    format_product_analyzer_user_prompt,
)
from shopigent.llm.provider import LLMProvider
from shopigent.scraper.base import RawProduct

logger = logging.getLogger(__name__)

DEFAULT_SCORE = 100.0
DEFAULT_ASSESSMENT = "분석 실패"
SCORE_MIN = 0.0
SCORE_MAX = 200.0


@dataclass
class AnalysisResult:
    preference_fit_score: float
    assessment: str


class ProductAnalyzer:
    def __init__(self, llm_provider: LLMProvider):
        self._llm = llm_provider

    async def analyze(self, product: RawProduct, user_preference_text: str) -> AnalysisResult:
        messages = [
            {"role": "system", "content": PRODUCT_ANALYZER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": format_product_analyzer_user_prompt(product, user_preference_text),
            },
        ]
        try:
            data = await self._llm.complete_json(messages=messages)
            score = float(data.get("preference_fit_score", DEFAULT_SCORE))
            score = max(SCORE_MIN, min(SCORE_MAX, score))
            assessment = str(data.get("assessment", DEFAULT_ASSESSMENT))
            return AnalysisResult(preference_fit_score=score, assessment=assessment)
        except Exception:
            logger.warning("ProductAnalyzer JSON 파싱 실패 — 기본값 반환")
            return AnalysisResult(
                preference_fit_score=DEFAULT_SCORE,
                assessment=DEFAULT_ASSESSMENT,
            )
