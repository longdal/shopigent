from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shopigent.database import Base


class TaskType(str, Enum):
    ONE_SHOT = "one_shot"       # 1회 검색 후 완료
    PERIODIC = "periodic"       # N주기마다 재검색
    PRICE_WATCH = "price_watch" # 특정 상품 가격 추적


class TaskStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class RunStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SearchTask(Base):
    __tablename__ = "search_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profile.id"), nullable=False)

    title: Mapped[str] = mapped_column(Text, nullable=False)
    natural_query: Mapped[str] = mapped_column(Text, nullable=False)
    expanded_queries: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON []

    task_type: Mapped[str] = mapped_column(Text, default=TaskType.ONE_SHOT)
    status: Mapped[str] = mapped_column(Text, default=TaskStatus.ACTIVE)

    # 스케줄 설정 (PERIODIC 타입에서 사용)
    cron_expression: Mapped[str | None] = mapped_column(Text, nullable=True)  # "0 9 * * 1"

    # 검색 조건
    target_shops: Mapped[str | None] = mapped_column(Text, nullable=True)    # JSON [] or NULL(전체)
    budget_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extra_constraints: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # PRICE_WATCH 전용
    watch_product_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    watch_target_price: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["UserProfile"] = relationship(back_populates="tasks")  # noqa: F821
    runs: Mapped[list["SearchTaskRun"]] = relationship(back_populates="task")


class SearchTaskRun(Base):
    __tablename__ = "search_task_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("search_task.id"), nullable=False)

    status: Mapped[str] = mapped_column(Text, default=RunStatus.RUNNING)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    products_found: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    task: Mapped["SearchTask"] = relationship(back_populates="runs")
    products: Mapped[list["Product"]] = relationship(back_populates="run")  # noqa: F821
    report: Mapped["Report | None"] = relationship(back_populates="run")    # noqa: F821
