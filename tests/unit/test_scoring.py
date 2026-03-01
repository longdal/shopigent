"""점수 산정 엔진 단위 테스트"""

import pytest

from shopigent.scraper.base import RawProduct
from shopigent.scoring.engine import ScoringEngine


@pytest.fixture
def engine():
    return ScoringEngine()


@pytest.fixture
def sample_product():
    return RawProduct(
        url="https://example.com/product/1",
        title="테스트 상품",
        shop_domain="example.com",
        price=50000,
        delivery_fee=3000,
        review_count=100,
        review_avg_rating=4.5,
        brand="테스트브랜드",
    )


def test_total_score_max_1000(engine, sample_product):
    score = engine.calculate(sample_product)
    assert score.total <= 1000.0


def test_total_score_positive(engine, sample_product):
    score = engine.calculate(sample_product)
    assert score.total >= 0.0


def test_price_score_within_budget(engine, sample_product):
    """예산 내 상품은 가격 점수 감점 없음"""
    score = engine.calculate(sample_product, budget_max=100000)
    assert score.price_score == 250.0


def test_price_score_over_budget_penalty(engine, sample_product):
    """예산 초과 상품은 가격 점수 감점 (소프트 필터)"""
    score_within = engine.calculate(sample_product, budget_max=100000)
    score_over = engine.calculate(sample_product, budget_max=30000)
    assert score_over.price_score < score_within.price_score


def test_price_score_no_budget(engine, sample_product):
    """예산 미설정 시 최고 가격 점수"""
    score = engine.calculate(sample_product, budget_max=None)
    assert score.price_score == 250.0


def test_review_score_no_reviews(engine):
    product = RawProduct(
        url="https://example.com/product/2",
        title="리뷰 없는 상품",
        shop_domain="example.com",
        price=10000,
        review_count=0,
        review_avg_rating=None,
    )
    score = engine.calculate(product)
    assert score.review_score >= 0


def test_rank_top5(engine, sample_product):
    """상위 5개만 반환"""
    products = [
        RawProduct(
            url=f"https://example.com/{i}",
            title=f"상품{i}",
            shop_domain="example.com",
            price=i * 10000,
            review_count=i * 10,
            review_avg_rating=3.0 + (i % 3) * 0.5,
        )
        for i in range(1, 11)
    ]
    scored = [(p, engine.calculate(p)) for p in products]
    top5 = engine.rank_products(scored)
    assert len(top5) == 5


def test_rank_sorted_by_score(engine, sample_product):
    """점수 내림차순 정렬 확인"""
    products = [
        RawProduct(
            url=f"https://example.com/{i}",
            title=f"상품{i}",
            shop_domain="example.com",
            price=50000,
            review_count=i * 100,
            review_avg_rating=min(1.0 + i * 0.5, 5.0),
        )
        for i in range(1, 6)
    ]
    scored = [(p, engine.calculate(p)) for p in products]
    top5 = engine.rank_products(scored)
    scores = [s.total for _, s in top5]
    assert scores == sorted(scores, reverse=True)
