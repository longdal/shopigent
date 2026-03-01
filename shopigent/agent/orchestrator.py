"""
검색 파이프라인 총괄 오케스트레이터.

실행 순서:
1. QueryExpander (LLM) → 검색 키워드 확장
2. ScraperFactory → 병렬 크롤링
3. ProductDeduplicator → 중복 제거
4. ScoringEngine → 1000점 계산
5. RankingEngine → Top 5 선정
6. ReportGenerator → 리포트 생성
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime

from shopigent.scraper.base import RawProduct
from shopigent.scraper.shops.naver import NaverShoppingScraper
from shopigent.scoring.engine import ScoreBreakdown, ScoringEngine

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    query: str
    products: list[tuple[RawProduct, ScoreBreakdown]]  # Top 5 (상품, 점수)
    total_found: int
    executed_at: datetime


class SearchOrchestrator:
    def __init__(self):
        self.scoring_engine = ScoringEngine()
        self._scrapers = {
            "naver": NaverShoppingScraper(),
            # Phase 2에서 추가: coupang, eleven_street, gmarket, aliexpress
        }

    async def run(
        self,
        query: str,
        budget_max: int | None = None,
        target_shops: list[str] | None = None,
    ) -> SearchResult:
        """검색 파이프라인 실행"""
        logger.info(f"검색 시작: '{query}'")

        # 1. 사용할 스크래퍼 결정
        scrapers = self._select_scrapers(target_shops)

        # 2. 병렬 크롤링
        all_products = await self._parallel_scrape(scrapers, query)
        logger.info(f"총 {len(all_products)}개 상품 수집")

        # 3. 중복 제거
        unique_products = self._deduplicate(all_products)
        logger.info(f"중복 제거 후 {len(unique_products)}개")

        # 4. 점수 계산
        scored = [
            (p, self.scoring_engine.calculate(p, budget_max=budget_max))
            for p in unique_products
        ]

        # 5. Top 5 선정
        top5 = self.scoring_engine.rank_products(scored)

        return SearchResult(
            query=query,
            products=top5,
            total_found=len(unique_products),
            executed_at=datetime.now(),
        )

    def _select_scrapers(self, target_shops: list[str] | None):
        if not target_shops:
            return list(self._scrapers.values())
        return [
            scraper for name, scraper in self._scrapers.items()
            if name in target_shops
        ]

    async def _parallel_scrape(self, scrapers, query: str) -> list[RawProduct]:
        tasks = [scraper.search(query) for scraper in scrapers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        products = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"스크래퍼 {i} 실패: {result}")
            else:
                products.extend(result)
        return products

    def _deduplicate(self, products: list[RawProduct]) -> list[RawProduct]:
        """URL 기반 중복 제거"""
        seen_urls = set()
        unique = []
        for product in products:
            if product.url not in seen_urls:
                seen_urls.add(product.url)
                unique.append(product)
        return unique


# 싱글톤 인스턴스
orchestrator = SearchOrchestrator()
