from shopigent.llm.token_counter import TokenCount, TokenCounter

SAMPLE_PRODUCT = {
    "title": "노스페이스 눕시 다운 패딩 점퍼 남성 겨울 구스다운 NJ1DQ55A",
    "brand": "노스페이스",
    "price": 289000,
    "delivery_fee": 0,
    "category": "패딩/점퍼",
    "review_count": 1842,
    "review_avg_rating": 4.7,
    "description": "구스다운 90% 충전재 사용. 방풍/방수 기능성 원단. 경량 압축 보관 가능.",
    "specs": {"소재": "겉감 100% 나일론, 충전재 구스다운 90%", "색상": "블랙, 네이비"},
}

SAMPLE_USER_PREFERENCE = "선호 브랜드: 노스페이스. 예산: 20~40만원. 선호 기능: 방풍, 방수."


def _build_query_expander_messages(query: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "당신은 쇼핑 검색 전문가입니다. "
                "사용자의 검색어를 분석하여 관련 키워드를 확장해주세요. "
                "결과는 JSON 배열로 반환하세요."
            ),
        },
        {
            "role": "user",
            "content": f"검색어: {query}\n\n관련 키워드 5개를 생성해주세요.",
        },
    ]


def _build_product_analyzer_messages(
    product: dict,
    user_preference: str,
) -> list[dict]:
    product_info = (
        f"상품명: {product['title']}\n"
        f"브랜드: {product['brand']}\n"
        f"가격: {product['price']:,}원\n"
        f"배송비: {product['delivery_fee']:,}원\n"
        f"카테고리: {product['category']}\n"
        f"리뷰 수: {product['review_count']:,}건\n"
        f"평균 평점: {product['review_avg_rating']}\n"
        f"설명: {product['description']}\n"
        f"스펙: {product['specs']}\n"
    )
    return [
        {
            "role": "system",
            "content": (
                "당신은 상품 품질 분석 전문가입니다. "
                "상품 정보와 사용자 선호도를 비교하여 적합도를 0~200점으로 평가해주세요. "
                "JSON으로 {score, reason} 형태로 반환하세요."
            ),
        },
        {
            "role": "user",
            "content": (
                f"## 사용자 선호도\n{user_preference}\n\n"
                f"## 상품 정보\n{product_info}\n"
                "위 상품의 취향 적합도를 평가해주세요."
            ),
        },
    ]


def _build_report_generator_messages(
    top5_products: list[dict],
    query: str,
) -> list[dict]:
    products_text = ""
    for i, p in enumerate(top5_products, 1):
        products_text += (
            f"\n### {i}위: {p['title']}\n"
            f"- 가격: {p['price']:,}원\n"
            f"- 브랜드: {p['brand']}\n"
            f"- 평점: {p['review_avg_rating']} ({p['review_count']:,}건)\n"
            f"- 설명: {p['description']}\n"
        )
    return [
        {
            "role": "system",
            "content": (
                "당신은 쇼핑 리포트 작성 전문가입니다. "
                "Top 5 상품 분석 결과를 보기 좋은 HTML 리포트로 작성해주세요. "
                "각 상품의 장단점, 추천 이유를 포함하세요."
            ),
        },
        {
            "role": "user",
            "content": (
                f"검색어: {query}\n\n"
                f"## Top 5 상품 분석 결과\n{products_text}\n"
                "위 상품들에 대한 상세 리포트를 HTML 형식으로 작성해주세요."
            ),
        },
    ]


class TestTokenCounting:
    def setup_method(self):
        self.counter = TokenCounter()

    def test_count_query_expander_tokens(self):
        """검색어 확장 프롬프트의 토큰 수를 측정한다."""
        messages = _build_query_expander_messages("겨울 패딩")
        result = self.counter.count_messages(messages)

        assert isinstance(result, TokenCount)
        assert result.input_tokens > 0
        # 토큰 상한: 검색어 확장은 짧은 프롬프트
        assert result.input_tokens < 5000
        print(f"\n[QueryExpander] input_tokens={result.input_tokens}")

    def test_count_product_analyzer_tokens(self):
        """상품 1건 분석 프롬프트의 토큰 수를 측정한다."""
        messages = _build_product_analyzer_messages(
            SAMPLE_PRODUCT,
            SAMPLE_USER_PREFERENCE,
        )
        result = self.counter.count_messages(messages)

        assert isinstance(result, TokenCount)
        assert result.input_tokens > 0
        # 토큰 상한: 상품 분석은 중간 길이
        assert result.input_tokens < 10000
        print(f"\n[ProductAnalyzer] input_tokens={result.input_tokens}")

    def test_count_report_generator_tokens(self):
        """Top5 리포트 생성 프롬프트의 토큰 수를 측정한다."""
        top5 = [SAMPLE_PRODUCT] * 5
        messages = _build_report_generator_messages(top5, "겨울 패딩")
        result = self.counter.count_messages(messages)

        assert isinstance(result, TokenCount)
        assert result.input_tokens > 0
        # 토큰 상한: 리포트 생성은 가장 긴 프롬프트
        assert result.input_tokens < 20000
        print(f"\n[ReportGenerator] input_tokens={result.input_tokens}")

    def test_token_count_is_positive(self):
        """어떤 메시지든 토큰 수는 0보다 크다."""
        messages = [{"role": "user", "content": "hello"}]
        result = self.counter.count_messages(messages)

        assert result.input_tokens > 0
        assert result.total_tokens > 0

    def test_token_count_dataclass_fields(self):
        """TokenCount는 input_tokens, output_tokens, total_tokens 필드를 갖는다."""
        messages = [{"role": "user", "content": "test"}]
        result = self.counter.count_messages(messages)

        assert hasattr(result, "input_tokens")
        assert hasattr(result, "output_tokens")
        assert hasattr(result, "total_tokens")
        assert result.total_tokens == result.input_tokens + result.output_tokens

    def test_custom_model_name(self):
        """모델명을 지정하면 해당 모델 기준으로 토큰을 카운팅한다."""
        counter = TokenCounter(model="gpt-4")
        messages = [{"role": "user", "content": "hello world"}]
        result = counter.count_messages(messages)

        assert result.input_tokens > 0
