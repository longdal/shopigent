"""ProductAnalyzer 단위 테스트 — LLM 취향 분석 및 JSON 출력 검증"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from shopigent.llm.analyzer import AnalysisResult, ProductAnalyzer
from shopigent.scraper.base import RawProduct


@pytest.fixture
def mock_llm_provider():
    provider = MagicMock()
    provider.complete_json = AsyncMock()
    return provider


@pytest.fixture
def sample_product():
    return RawProduct(
        url="https://example.com/product/1",
        title="노스페이스 눕시 패딩 700 다운",
        shop_domain="example.com",
        price=350000,
        delivery_fee=0,
        brand="노스페이스",
        description="700 필파워 구스다운, 방풍 기능, 겨울 아우터",
        review_count=1200,
        review_avg_rating=4.7,
    )


@pytest.fixture
def user_preference_text():
    return (
        "겨울 패딩을 찾고 있습니다. "
        "따뜻하고 가벼운 다운 패딩 선호, 브랜드는 노스페이스나 파타고니아"
    )


@pytest.mark.asyncio
async def test_analyze_returns_analysis_result(
    mock_llm_provider, sample_product, user_preference_text
):
    """AnalysisResult 타입 반환 확인"""
    mock_llm_provider.complete_json.return_value = {
        "preference_fit_score": 180,
        "assessment": "노스페이스 눕시 패딩은 사용자가 선호하는 브랜드이며 따뜻한 다운 패딩입니다.",
    }
    analyzer = ProductAnalyzer(llm_provider=mock_llm_provider)
    result = await analyzer.analyze(sample_product, user_preference_text)

    assert isinstance(result, AnalysisResult)
    assert isinstance(result.preference_fit_score, float)
    assert isinstance(result.assessment, str)


@pytest.mark.asyncio
async def test_score_in_valid_range(mock_llm_provider, sample_product, user_preference_text):
    """점수가 0~200 범위인지 확인"""
    mock_llm_provider.complete_json.return_value = {
        "preference_fit_score": 150,
        "assessment": "적합한 상품입니다.",
    }
    analyzer = ProductAnalyzer(llm_provider=mock_llm_provider)
    result = await analyzer.analyze(sample_product, user_preference_text)

    assert 0 <= result.preference_fit_score <= 200


@pytest.mark.asyncio
async def test_json_parse_failure_returns_default(
    mock_llm_provider, sample_product, user_preference_text
):
    """LLM이 invalid JSON 반환 시 기본값"""
    mock_llm_provider.complete_json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    analyzer = ProductAnalyzer(llm_provider=mock_llm_provider)
    result = await analyzer.analyze(sample_product, user_preference_text)

    assert result.preference_fit_score == 100.0
    assert result.assessment == "분석 실패"


@pytest.mark.asyncio
async def test_high_fit_product_gets_high_score(
    mock_llm_provider, sample_product, user_preference_text
):
    """취향 일치 상품 → 높은 점수 (mock)"""
    mock_llm_provider.complete_json.return_value = {
        "preference_fit_score": 190,
        "assessment": "브랜드, 기능, 스타일 모두 취향과 일치합니다.",
    }
    analyzer = ProductAnalyzer(llm_provider=mock_llm_provider)
    result = await analyzer.analyze(sample_product, user_preference_text)

    assert result.preference_fit_score >= 150


@pytest.mark.asyncio
async def test_low_fit_product_gets_low_score(mock_llm_provider, user_preference_text):
    """취향 불일치 상품 → 낮은 점수 (mock)"""
    low_fit_product = RawProduct(
        url="https://example.com/product/2",
        title="여름용 린넨 셔츠",
        shop_domain="example.com",
        price=45000,
        brand="유니클로",
        description="여름 시즌 린넨 소재 셔츠, 시원한 착용감",
    )
    mock_llm_provider.complete_json.return_value = {
        "preference_fit_score": 20,
        "assessment": "겨울 패딩을 찾는 사용자에게 여름 셔츠는 부적합합니다.",
    }
    analyzer = ProductAnalyzer(llm_provider=mock_llm_provider)
    result = await analyzer.analyze(low_fit_product, user_preference_text)

    assert result.preference_fit_score <= 50
