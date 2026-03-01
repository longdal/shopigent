"""
Shopigent CLI 진입점.

사용법:
    uv run python -m shopigent.cli search "겨울 패딩"
    uv run python -m shopigent.cli search "노트북 가성비" --budget 1000000
"""

import asyncio
import sys
from datetime import datetime


def format_price(price: int | None) -> str:
    if price is None:
        return "가격 미상"
    return f"{price:,}원"


async def cmd_search(query: str, budget_max: int | None = None) -> None:
    from shopigent.agent.orchestrator import orchestrator

    print(f"\n🔍 검색 중: '{query}'")
    if budget_max:
        print(f"   예산 상한: {format_price(budget_max)}")
    print("-" * 60)

    result = await orchestrator.run(query, budget_max=budget_max)

    print(f"\n✅ 검색 완료 ({result.executed_at.strftime('%Y-%m-%d %H:%M')})")
    print(f"   총 {result.total_found}개 상품 중 Top {len(result.products)}개\n")

    # 결과 출력
    for i, (product, score) in enumerate(result.products, 1):
        print(f"{'='*60}")
        print(f"#{i}  {product.title[:50]}")
        print(f"    가격: {format_price(product.total_price)}", end="")
        if product.delivery_fee > 0:
            print(f" (배송비 {format_price(product.delivery_fee)} 포함)", end="")
        print()
        if product.brand:
            print(f"    브랜드: {product.brand}")
        print(f"    리뷰: {product.review_count}개", end="")
        if product.review_avg_rating:
            print(f" / 평점 {product.review_avg_rating:.1f}⭐", end="")
        print()
        print(f"    🏆 점수: {score.total:.0f}점 / 1000점")
        print(f"       가격({score.price_score:.0f}) + 품질({score.quality_score:.0f}) + "
              f"리뷰({score.review_score:.0f}) + 신뢰도({score.reliability_score:.0f})")
        print(f"    🔗 {product.url}")

    # doc/result.md 업데이트
    _save_to_result_md(query, result)
    print(f"\n📝 결과가 doc/result.md에 저장되었습니다.")


def _save_to_result_md(query: str, result) -> None:
    """검색 결과를 doc/result.md에 마크다운으로 저장"""
    lines = [
        f"# Shopigent 검색 결과\n",
        f"## 최근 검색: {query}\n",
        f"**실행 시각**: {result.executed_at.strftime('%Y-%m-%d %H:%M:%S')}  \n",
        f"**총 수집**: {result.total_found}개 → **Top {len(result.products)}개** 표시\n",
        "\n---\n",
    ]

    for i, (product, score) in enumerate(result.products, 1):
        lines.append(f"### #{i} {product.title[:60]}\n")
        lines.append(f"- **총 가격**: {format_price(product.total_price)}")
        if product.delivery_fee > 0:
            lines.append(f" (배송비 {format_price(product.delivery_fee)} 포함)")
        lines.append("\n")
        if product.brand:
            lines.append(f"- **브랜드**: {product.brand}\n")
        lines.append(f"- **리뷰**: {product.review_count}개")
        if product.review_avg_rating:
            lines.append(f" / 평점 {product.review_avg_rating:.1f}⭐")
        lines.append("\n")
        lines.append(f"- **점수**: `{score.total:.0f}점` "
                     f"(가격:{score.price_score:.0f} / 품질:{score.quality_score:.0f} / "
                     f"리뷰:{score.review_score:.0f} / 신뢰도:{score.reliability_score:.0f})\n")
        lines.append(f"- **링크**: {product.url}\n\n")

    try:
        with open("doc/result.md", "w", encoding="utf-8") as f:
            f.writelines(lines)
    except OSError as e:
        print(f"result.md 저장 실패: {e}")


def main():
    args = sys.argv[1:]
    if not args or args[0] != "search":
        print("사용법: python -m shopigent.cli search <검색어> [--budget <최대금액>]")
        sys.exit(1)

    query_parts = []
    budget_max = None
    i = 1
    while i < len(args):
        if args[i] == "--budget" and i + 1 < len(args):
            budget_max = int(args[i + 1])
            i += 2
        else:
            query_parts.append(args[i])
            i += 1

    query = " ".join(query_parts)
    if not query:
        print("검색어를 입력해주세요.")
        sys.exit(1)

    asyncio.run(cmd_search(query, budget_max=budget_max))


if __name__ == "__main__":
    main()
