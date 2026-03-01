# Shopigent 개발 진행 상황

## 현재 Phase: Phase 0 — 환경 구성

## Phase 0 체크리스트

- [x] pyproject.toml + uv 설정
- [x] SQLAlchemy 모델 (user_profile, user_preference, search_task, search_task_run, product, product_score, shop_reliability, review, report)
- [x] Alembic 마이그레이션 초기 설정 + `migrations/versions/136d9d1a52c5_initial_schema.py`
- [x] FastAPI main.py (기본 lifespan + 라우터 등록)
- [x] config.py (Pydantic Settings)
- [x] database.py (async SQLAlchemy 엔진)
- [x] Makefile
- [x] .gitignore
- [x] .env.example
- [x] 디렉토리 구조 생성

**Phase 0 완료** ✅ (`make dev`로 서버 정상 실행 확인)

## Phase 1 체크리스트 (현재)

- [x] 네이버쇼핑 API 스크래퍼 기본 구현 (`scraper/shops/naver.py`)
- [x] LLM Provider 추상화 (`llm/provider.py` - LiteLLM 기반)
- [x] 점수 엔진 기본 구현 (`scoring/engine.py` - 가격+리뷰)
- [x] 파이프라인 오케스트레이터 (`agent/orchestrator.py`)
- [x] CLI 진입점 (`shopigent/cli.py`)
- [ ] 네이버 쇼핑 API 키 설정 후 실제 검색 테스트
- [ ] LLM 취향 분석 기본 구현 (`llm/analyzer.py`)

---

## 변경 이력

### 2026-02-28

- 프로젝트 초기화
- CLAUDE.md, doc/plan.md, doc/progress.md, doc/result.md 생성
- 아키텍처 설계 확정
  - 기술 스택: Python 3.11 + FastAPI + SQLite + APScheduler + LiteLLM + HTMX
  - 대상 쇼핑몰: 국내 4개 + AliExpress
  - 점수 시스템: 1000점 만점 (가격250 + 품질250 + 리뷰200 + 취향200 + 신뢰100)
  - Phase 0~6 개발 계획 수립

- Phase 0 완료
  - 전체 디렉토리 구조 생성
  - SQLAlchemy 모델 9개 테이블 (async SQLite)
  - Alembic 마이그레이션 초기화 + 적용 완료
  - FastAPI + APScheduler lifespan 연동
  - 단위 테스트 8개 통과 (scoring engine)
  - `http://127.0.0.1:8000` 서버 정상 실행 확인

- Phase 1 부분 완료
  - 네이버쇼핑 API 스크래퍼 구현
  - LiteLLM 기반 LLM Provider 구현
  - 점수 엔진 기본 구현 (가격+리뷰+신뢰도)
  - 검색 파이프라인 오케스트레이터 구현
  - CLI 검색 진입점 구현
