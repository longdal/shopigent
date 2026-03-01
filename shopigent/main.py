from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from shopigent.config import settings
from shopigent.database import create_tables
from shopigent.scheduler.manager import scheduler_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작: DB 테이블 생성 + 스케줄러 시작
    await create_tables()
    scheduler_manager.start()

    yield

    # 종료: 스케줄러 정지
    scheduler_manager.shutdown()


app = FastAPI(
    title="Shopigent",
    description="AI 기반 개인 쇼핑 에이전트",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
)

# 정적 파일
app.mount("/static", StaticFiles(directory="shopigent/web/static"), name="static")

# 라우터 등록 (각 Phase에서 추가)
from shopigent.api.routes import health  # noqa: E402
app.include_router(health.router)


@app.get("/")
async def root():
    return {"message": "Shopigent API 실행 중", "version": "0.1.0"}
