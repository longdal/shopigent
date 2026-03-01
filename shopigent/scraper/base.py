"""
BaseScraper - 모든 쇼핑몰 스크래퍼의 추상 기반 클래스.

새 쇼핑몰 스크래퍼 추가 시 이 클래스를 상속하고
search(), get_product_detail() 메서드를 구현해야 합니다.
"""

import asyncio
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from shopigent.config import settings


@dataclass
class RawProduct:
    """스크래퍼가 반환하는 원시 상품 데이터"""
    url: str
    title: str
    shop_domain: str
    price: int | None = None
    delivery_fee: int = 0
    image_url: str | None = None
    category: str | None = None
    brand: str | None = None
    review_count: int = 0
    review_avg_rating: float | None = None
    description: str | None = None
    specs: dict = field(default_factory=dict)
    external_id: str | None = None
    raw_data: dict = field(default_factory=dict)

    @property
    def total_price(self) -> int | None:
        if self.price is None:
            return None
        return self.price + self.delivery_fee


@dataclass
class RawReview:
    """원시 리뷰 데이터"""
    rating: int | None = None
    content: str | None = None
    reviewed_at: str | None = None
    is_verified_purchase: bool | None = None
    helpful_count: int = 0


class BaseScraper(ABC):
    """쇼핑몰 스크래퍼 기반 클래스"""

    shop_domain: str = ""  # 서브클래스에서 반드시 지정

    async def search(self, query: str, max_results: int = 20) -> list[RawProduct]:
        """검색어로 상품 목록 검색. 서브클래스에서 구현."""
        raise NotImplementedError

    async def get_product_detail(self, url: str) -> RawProduct | None:
        """상품 상세 페이지에서 추가 정보 수집. 선택적 구현."""
        return None

    async def get_reviews(self, product: RawProduct, max_count: int = 20) -> list[RawReview]:
        """상품 리뷰 수집. 선택적 구현."""
        return []

    async def _delay(self) -> None:
        """봇 감지 방지를 위한 랜덤 딜레이"""
        delay = random.uniform(settings.scrape_delay_min, settings.scrape_delay_max)
        await asyncio.sleep(delay)
