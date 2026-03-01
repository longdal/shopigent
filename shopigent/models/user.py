from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shopigent.database import Base


class UserProfile(Base):
    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    preferences: Mapped[list["UserPreference"]] = relationship(back_populates="user")
    tasks: Mapped[list["SearchTask"]] = relationship(back_populates="user")  # noqa: F821


class UserPreference(Base):
    __tablename__ = "user_preference"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profile.id"), nullable=False)
    # NULL이면 전역 설정, 값이 있으면 카테고리별 설정
    category: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 점수 가중치 (합계가 반드시 1.0일 필요는 없음, 엔진이 정규화)
    weight_price: Mapped[float] = mapped_column(Float, default=0.25)
    weight_quality: Mapped[float] = mapped_column(Float, default=0.25)
    weight_delivery: Mapped[float] = mapped_column(Float, default=0.10)
    weight_brand_trust: Mapped[float] = mapped_column(Float, default=0.15)
    weight_review_quality: Mapped[float] = mapped_column(Float, default=0.15)
    weight_preference_fit: Mapped[float] = mapped_column(Float, default=0.10)

    price_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # JSON 배열 (문자열로 저장)
    preferred_shops: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON []
    blacklisted_shops: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON []

    free_text_preference: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_preference_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["UserProfile"] = relationship(back_populates="preferences")
