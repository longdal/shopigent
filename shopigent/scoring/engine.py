"""
1000점 만점 점수 산정 엔진.

점수 구성:
- 가격 점수:      최대 250점 (예산 대비 가격 + 배송비 경쟁력)
- 품질 점수:      최대 250점 (재질/브랜드/스펙 적합도)
- 리뷰 점수:      최대 200점 (수/평점/신뢰도/최근 트렌드)
- 취향 적합도:    최대 200점 (LLM 취향 일치도)
- 신뢰도 점수:    최대 100점 (쇼핑몰+판매자)
"""

from dataclasses import dataclass

from shopigent.scraper.base import RawProduct


@dataclass
class ScoreBreakdown:
    price_score: float = 0.0        # 0~250
    quality_score: float = 0.0      # 0~250
    review_score: float = 0.0       # 0~200
    preference_fit_score: float = 0.0  # 0~200
    reliability_score: float = 0.0  # 0~100

    @property
    def total(self) -> float:
        return (
            self.price_score
            + self.quality_score
            + self.review_score
            + self.preference_fit_score
            + self.reliability_score
        )


class ScoringEngine:
    """
    상품 점수를 1000점 만점으로 산정합니다.

    Phase 1에서는 가격 + 리뷰 점수만 사용하고,
    이후 Phase에서 품질, 취향, 신뢰도 점수가 추가됩니다.
    """

    def calculate(
        self,
        product: RawProduct,
        budget_max: int | None = None,
        shop_trust_score: int = 70,
        llm_preference_score: float | None = None,
    ) -> ScoreBreakdown:
        breakdown = ScoreBreakdown()

        breakdown.price_score = self._calc_price_score(product, budget_max)
        breakdown.review_score = self._calc_review_score(product)
        breakdown.reliability_score = self._calc_reliability_score(shop_trust_score)

        if llm_preference_score is not None:
            breakdown.preference_fit_score = min(llm_preference_score, 200.0)

        # Phase 2에서 quality_score 구현 예정
        breakdown.quality_score = self._calc_basic_quality_score(product)

        return breakdown

    def _calc_price_score(self, product: RawProduct, budget_max: int | None) -> float:
        """가격 점수 계산 (최대 250점). 예산 초과 시 소프트 감점."""
        total = product.total_price
        if total is None:
            return 100.0  # 가격 정보 없음 → 중간 점수

        score = 250.0

        if budget_max and total > budget_max:
            # 예산 초과 비율에 따라 감점 (최대 -150점)
            over_ratio = (total - budget_max) / budget_max
            penalty = min(over_ratio * 150, 150)
            score -= penalty

        # 배송비가 없으면 추가 점수
        if product.delivery_fee == 0:
            score = min(score + 20, 250)

        return max(score, 0.0)

    def _calc_review_score(self, product: RawProduct) -> float:
        """리뷰 점수 계산 (최대 200점). Phase 1 기본 구현."""
        score = 0.0

        # 리뷰 수 점수 (최대 50점)
        review_count = product.review_count
        if review_count >= 1000:
            count_score = 50.0
        elif review_count >= 100:
            count_score = 35.0
        elif review_count >= 10:
            count_score = 20.0
        elif review_count >= 1:
            count_score = 10.0
        else:
            count_score = 0.0
        score += count_score

        # 평균 평점 점수 (최대 50점)
        if product.review_avg_rating is not None:
            rating = product.review_avg_rating
            rating_score = ((rating - 1) / 4) * 50  # 1~5 → 0~50
            score += max(rating_score, 0)

        # 리뷰 신뢰도 / 최근 트렌드: Phase 2에서 구현 (기본 점수 60점 부여)
        score += 60.0

        return min(score, 200.0)

    def _calc_reliability_score(self, shop_trust_score: int) -> float:
        """쇼핑몰 신뢰도 점수 (최대 100점)."""
        # trust_score (0~100) → 신뢰도 점수 (0~100)
        shop_score = shop_trust_score * 0.6  # 쇼핑몰 신뢰도 60점 만점
        seller_score = 40.0  # 판매자 신뢰도: Phase 5에서 구현
        return min(shop_score + seller_score, 100.0)

    def _calc_basic_quality_score(self, product: RawProduct) -> float:
        """기본 품질 점수 (Phase 2 전까지 임시). 브랜드 유무로만 판단."""
        if product.brand:
            return 120.0  # 브랜드 있음
        return 80.0  # 브랜드 없음

    def rank_products(
        self, scored_products: list[tuple[RawProduct, ScoreBreakdown]]
    ) -> list[tuple[RawProduct, ScoreBreakdown]]:
        """점수 기준 내림차순 정렬 후 Top 5 반환"""
        sorted_products = sorted(scored_products, key=lambda x: x[1].total, reverse=True)
        return sorted_products[:5]
