"""uv run python scripts/measure_tokens.py"""

from shopigent.llm.token_counter import TokenCounter

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


def build_query_expander_messages(query: str) -> list[dict]:
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


def build_product_analyzer_messages(product: dict, user_preference: str) -> list[dict]:
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


def build_report_generator_messages(top5_products: list[dict], query: str) -> list[dict]:
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


def main():
    counter = TokenCounter()

    calls = [
        ("QueryExpander", build_query_expander_messages("겨울 패딩")),
        (
            "ProductAnalyzer (1건)",
            build_product_analyzer_messages(SAMPLE_PRODUCT, SAMPLE_USER_PREFERENCE),
        ),
        (
            "ProductAnalyzer (20건 추정)",
            build_product_analyzer_messages(SAMPLE_PRODUCT, SAMPLE_USER_PREFERENCE),
        ),
        (
            "ReportGenerator (Top5)",
            build_report_generator_messages([SAMPLE_PRODUCT] * 5, "겨울 패딩"),
        ),
    ]

    print("=" * 65)
    print(f"{'호출 지점':<25} {'입력 토큰':>10} {'20건 추정':>10} {'비고'}")
    print("-" * 65)

    for name, messages in calls:
        result = counter.count_messages(messages)
        if "20건" in name:
            estimated = result.input_tokens * 20
            print(f"  {'(20건 병렬 호출 시)':.<25} {estimated:>10,} {'':>10} 1건×20")
        else:
            print(f"  {name:<25} {result.input_tokens:>10,}")

    print("-" * 65)

    query_tokens = counter.count_messages(calls[0][1]).input_tokens
    analyzer_tokens = counter.count_messages(calls[1][1]).input_tokens * 20
    report_tokens = counter.count_messages(calls[3][1]).input_tokens
    total = query_tokens + analyzer_tokens + report_tokens
    print(f"  {'합계 (1회 검색 추정)':<25} {total:>10,}")
    print("=" * 65)
    print(f"\n기준 모델: {counter.model}")
    print("※ output 토큰은 실제 LLM 응답에 따라 달라지므로 input만 측정")


if __name__ == "__main__":
    main()
