"""
네이버 쇼핑 스크래퍼.

네이버 쇼핑 검색 API를 우선 사용하고,
API 미설정 시 공개 검색 결과 파싱으로 폴백합니다.
"""

import logging
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from shopigent.config import settings
from shopigent.scraper.base import BaseScraper, RawProduct

logger = logging.getLogger(__name__)

NAVER_SHOP_API_URL = "https://openapi.naver.com/v1/search/shop.json"


class NaverShoppingScraper(BaseScraper):
    shop_domain = "shopping.naver.com"

    async def search(self, query: str, max_results: int = 20) -> list[RawProduct]:
        if settings.naver_client_id and settings.naver_client_secret:
            return await self._search_via_api(query, max_results)
        return await self._search_via_web(query, max_results)

    async def _search_via_api(self, query: str, max_results: int) -> list[RawProduct]:
        """네이버 쇼핑 검색 API 사용"""
        headers = {
            "X-Naver-Client-Id": settings.naver_client_id,
            "X-Naver-Client-Secret": settings.naver_client_secret,
        }
        params = {
            "query": query,
            "display": min(max_results, 100),
            "sort": "sim",  # 정확도순
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(NAVER_SHOP_API_URL, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.error(f"네이버 쇼핑 API 오류: {e}")
                return []

        products = []
        for item in data.get("items", []):
            # HTML 태그 제거
            title = BeautifulSoup(item.get("title", ""), "html.parser").get_text()
            price_str = item.get("lprice", "0").replace(",", "")
            delivery_fee = int(item.get("mallName", "0") == "쿠팡") * 0  # 예시

            try:
                price = int(price_str)
            except ValueError:
                price = None

            products.append(
                RawProduct(
                    url=item.get("link", ""),
                    title=title,
                    shop_domain=self.shop_domain,
                    price=price,
                    delivery_fee=0,  # API에서 배송비 미제공, 상세 페이지에서 획득
                    image_url=item.get("image"),
                    brand=item.get("brand"),
                    category=item.get("category1"),
                    external_id=item.get("productId"),
                    raw_data=item,
                )
            )

        logger.info(f"네이버 API 검색 결과: {len(products)}개 (쿼리: {query})")
        return products

    async def _search_via_web(self, query: str, max_results: int) -> list[RawProduct]:
        """API 미설정 시 공개 검색 결과 파싱 (fallback)"""
        logger.warning("네이버 쇼핑 API 미설정. 웹 검색으로 폴백합니다.")
        url = f"https://search.shopping.naver.com/search/all?query={quote(query)}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }

        await self._delay()
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url, headers=headers, follow_redirects=True)
                resp.raise_for_status()
            except Exception as e:
                logger.error(f"네이버 쇼핑 웹 파싱 오류: {e}")
                return []

        # 실제 파싱은 Phase 2에서 구현 (현재는 빈 목록 반환)
        logger.info("네이버 쇼핑 웹 파싱은 Phase 2에서 구현됩니다.")
        return []
