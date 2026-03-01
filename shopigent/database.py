from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from shopigent.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    # SQLite WAL 모드로 동시성 향상
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_tables() -> None:
    """앱 시작 시 테이블 생성 (Alembic 미사용 환경용)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
