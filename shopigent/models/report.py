from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shopigent.database import Base


class Report(Base):
    __tablename__ = "report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("search_task_run.id"), unique=True, nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("search_task.id"), nullable=False)

    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    html_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    markdown_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    run: Mapped["SearchTaskRun"] = relationship(back_populates="report")  # noqa: F821
