from shopigent.scraper.base import RawProduct

PRODUCT_ANALYZER_SYSTEM_PROMPT = (
    "당신은 쇼핑 상품 분석 전문가입니다.\n"
    "사용자 취향과 상품 정보를 비교하여 취향 적합도를 JSON으로 반환하세요.\n"
    '반드시 다음 형식의 JSON만 출력하세요: '
    '{"preference_fit_score": 0-200, "assessment": "평가 텍스트"}\n'
    "preference_fit_score는 0(완전 불일치)~200(완벽 일치) 범위의 정수입니다.\n"
    "assessment는 한국어로 2~3문장 이내로 작성하세요."
)


def format_product_analyzer_user_prompt(product: RawProduct, user_preference_text: str) -> str:
    price_str = f"{product.price:,}원" if product.price is not None else "가격 미상"
    return (
        f"[상품 정보]\n"
        f"- 상품명: {product.title}\n"
        f"- 가격: {price_str}\n"
        f"- 배송비: {product.delivery_fee:,}원\n"
        f"- 브랜드: {product.brand or '미상'}\n"
        f"- 카테고리: {product.category or '미상'}\n"
        f"- 설명: {product.description or '없음'}\n"
        f"- 리뷰 수: {product.review_count}\n"
        f"- 평균 평점: {product.review_avg_rating or '없음'}\n\n"
        f"[사용자 취향]\n{user_preference_text}"
    )
