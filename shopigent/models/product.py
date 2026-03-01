from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shopigent.database import Base


class ShopReliability(Base):
    __tablename__ = "shop_reliability"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shop_domain: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    shop_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_designated: Mapped[bool] = mapped_column(Boolean, default=False)  # 사용자 지정 쇼핑몰

    trust_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0~100
    domain_age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_ssl: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    business_reg_verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verification_detail: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON


class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("search_task_run.id"), nullable=False)
    shop_domain: Mapped[str] = mapped_column(Text, nullable=False)

    external_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)

    price: Mapped[int | None] = mapped_column(Integer, nullable=True)        # 원 단위
    delivery_fee: Mapped[int] = mapped_column(Integer, default=0)
    total_price: Mapped[int | None] = mapped_column(Integer, nullable=True)  # price + delivery_fee

    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand: Mapped[str | None] = mapped_column(Text, nullable=True)
    specs: Mapped[str | None] = mapped_column(Text, nullable=True)        # JSON
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    review_count: Mapped[int] = mapped_column(Integer, default=0)
    review_avg_rating: Mapped[float | None] = mapped_column(Float, nullable=True)

    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)     # JSON 원본
    scraped_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    run: Mapped["SearchTaskRun"] = relationship(back_populates="products")  # noqa: F821
    reviews: Mapped[list["Review"]] = relationship(back_populates="product")
    score: Mapped["ProductScore | None"] = relationship(back_populates="product")


class Review(Base):
    __tablename__ = "review"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), nullable=False)

    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_hash: Mapped[str | None] = mapped_column(Text, nullable=True)  # 개인정보 보호 해시
    reviewed_at: Mapped[str | None] = mapped_column(Text, nullable=True)  # DATE 문자열
    is_verified_purchase: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    fake_probability: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0~1

    product: Mapped["Product"] = relationship(back_populates="reviews")


class ProductScore(Base):
    __tablename__ = "product_score"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), unique=True, nullable=False)
    run_id: Mapped[int] = mapped_column(ForeignKey("search_task_run.id"), nullable=False)

    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)     # 0~1000
    price_score: Mapped[float | None] = mapped_column(Float, nullable=True)     # 0~250
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)   # 0~250
    review_score: Mapped[float | None] = mapped_column(Float, nullable=True)    # 0~200
    preference_fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0~200
    reliability_score: Mapped[float | None] = mapped_column(Float, nullable=True)    # 0~100

    score_breakdown: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON 세부 점수
    llm_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)   # LLM 평가 텍스트
    rank_in_run: Mapped[int | None] = mapped_column(Integer, nullable=True)   # 1~5

    calculated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="score")
