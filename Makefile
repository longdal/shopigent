.PHONY: dev test test-unit lint format db-migrate db-revision install playwright-install

# 개발 서버 실행
dev:
	uv run uvicorn shopigent.main:app --reload --host 127.0.0.1 --port 8000

# 의존성 설치
install:
	uv sync
	uv run playwright install chromium

# Playwright 브라우저만 설치
playwright-install:
	uv run playwright install chromium

# 테스트
test:
	uv run pytest tests/ -v

test-unit:
	uv run pytest tests/unit/ -v

# 린트 / 포맷
lint:
	uv run ruff check shopigent/ tests/

format:
	uv run ruff format shopigent/ tests/
	uv run ruff check --fix shopigent/ tests/

# DB 마이그레이션
db-migrate:
	uv run alembic upgrade head

db-revision:
	@read -p "마이그레이션 메시지: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"

db-downgrade:
	uv run alembic downgrade -1

# CLI 검색 (Phase 1 완료 후)
search:
	@read -p "검색어: " query; \
	uv run python -m shopigent.cli search "$$query"

# 데이터 폴더 초기화
init-data:
	mkdir -p data/reports
