# Shopigent 개발 계획

## 프로젝트 개요

AI 기반 개인 쇼핑 에이전트. 사용자 취향을 학습하여 자율적으로 상품을 검색하고, 1000점 만점 점수로 최적 상품 Top 5를 선정하여 Web UI와 이메일로 리포트를 제공합니다.

## 핵심 요구사항

1. 자연어로 원하는 물건을 입력하면 자율 검색 및 최적 상품 리포트 생성
2. 결정된 주기(cron)에 따라 자동 반복 검색
3. 초기 취향 조사(온보딩)로 사용자 쇼핑 프로파일 구성
4. 국내 쇼핑몰(네이버, 11번가, G마켓, 쿠팡) + AliExpress 검색
5. 미지정 쇼핑몰은 신뢰성 자동 검증 후 사용
6. 1000점 만점 점수 산정 → Top 5 상품 선정
7. Web UI (로컬 전용) + 이메일 리포트
8. 가격 변동 추적/알림 (PRICE_WATCH)
9. 다양한 LLM 모델 선택적 사용 (LiteLLM 추상화)

## 기술 스택

| 영역 | 기술 |
|------|------|
| 백엔드 | Python 3.11+ + FastAPI |
| DB | SQLite + SQLAlchemy (async) + aiosqlite |
| 스케줄러 | APScheduler |
| 스크래핑 | Playwright + httpx + BeautifulSoup4 |
| LLM | LiteLLM (Claude → GPT-4 → Ollama 전환 가능) |
| 프론트엔드 | HTML + HTMX + Tailwind CSS + Jinja2 |
| 이메일 | aiosmtplib |

## 아키텍처

```
Web UI (HTMX, 127.0.0.1)
    │
FastAPI Application
    ├── API Routes
    │   ├── /onboarding  — 취향 설정
    │   ├── /tasks       — 검색 작업 CRUD
    │   ├── /reports     — 리포트 조회
    │   ├── /shops       — 쇼핑몰 관리
    │   └── /settings    — 시스템 설정
    ├── APScheduler      — 주기적 검색 트리거
    └── WebSocket        — 실시간 진행상황
    │
SupervisorOrchestrator (agent/orchestrator.py)
    │
    ├── [Step 1] QueryExpander — 자연어 → 검색 키워드 확장 (LLM)
    │
    ├── [Step 2] 병렬 ShopAgent 실행 (asyncio.gather)
    │     ├── NaverShopAgent
    │     │     ├── search()    — 네이버 API/웹 검색
    │     │     ├── analyze()   — LLM 취향 분석
    │     │     └── score()     — 1000점 계산
    │     │     → AgentResult 반환
    │     ├── CoupangShopAgent  (동일 구조)
    │     ├── ElevenStreetShopAgent (동일 구조)
    │     ├── GmarketShopAgent  (동일 구조)
    │     └── AliExpressShopAgent (동일 구조)
    │
    └── [Step 3] Supervisor 통합 처리 (순차)
          ├── aggregate()       — 전체 결과 병합 + 중복 제거
          ├── final_rank()      — 전체 Top 5 선정
          └── ReportGenerator   — HTML + Markdown + Email
    │
SQLite (data/shopigent.db)
```

## 병렬 에이전트 설계

### 처리 경계

| 단계 | 처리 방식 | 담당 | 이유 |
|------|----------|------|------|
| 검색 (scrape) | **병렬** (쇼핑몰별) | ShopAgent | 쇼핑몰 독립적 |
| LLM 취향 분석 (analyze) | **병렬** (쇼핑몰별) | ShopAgent | 상품 독립적 |
| 점수 계산 (score) | **병렬** (쇼핑몰별) | ShopAgent | 상품 독립적 |
| 중복 제거 | **순차** | Supervisor | 전체 결과 필요 |
| 최종 랭킹 | **순차** | Supervisor | 전체 결과 필요 |
| 리포트 생성 | **순차** | Supervisor | 전체 결과 필요 |

### AgentResult — 에이전트 결과 계약

각 ShopAgent가 Supervisor에게 반환하는 표준 데이터:

```python
@dataclass
class AgentStatus(str, Enum):
    SUCCESS = "success"    # 정상 완료
    PARTIAL = "partial"    # 일부 상품만 수집
    FAILED  = "failed"     # 전체 실패

@dataclass
class ScoredProduct:
    product: RawProduct
    score: ScoreBreakdown
    llm_assessment: str | None  # LLM 취향 분석 텍스트

@dataclass
class AgentResult:
    shop_name: str
    products: list[ScoredProduct]   # 검색 + 분석 + 점수까지 완료
    status: AgentStatus
    error: str | None
    elapsed_sec: float
```

### 에이전트 타임아웃 정책

| 쇼핑몰 | 타임아웃 | 비고 |
|--------|---------|------|
| 네이버 | 10초 | API 기반, 빠름 |
| 11번가 | 20초 | httpx + BS4 |
| G마켓 | 20초 | httpx + BS4 |
| 쿠팡 | 20초 | httpx + BS4 |
| AliExpress | 40초 | Playwright, 느림 |
| 미지정몰 | 40초 | Playwright + LLM DOM |

- 타임아웃 초과 에이전트: `AgentStatus.FAILED`로 처리, 나머지 결과로 계속 진행
- 최소 1개 에이전트 성공 시 리포트 생성 가능

### 파일 구조 (목표)

```
shopigent/agent/
    orchestrator.py       — SupervisorOrchestrator (통합 처리)
    shop_agent.py         — BaseShopAgent ABC
    agents/
        naver_agent.py    — NaverShopAgent
        coupang_agent.py  — CoupangShopAgent
        eleven_agent.py   — ElevenStreetShopAgent
        gmarket_agent.py  — GmarketShopAgent
        aliexpress_agent.py — AliExpressShopAgent
```

## 1000점 점수 시스템

| 항목 | 최대 | 세부 구성 |
|------|------|----------|
| 가격 점수 | 250 | 예산 대비 가격(150) + 배송비 포함 경쟁력(100) |
| 품질 점수 | 250 | 재질/소재(80) + 브랜드(70) + 스펙 적합도(100) |
| 리뷰 점수 | 200 | 리뷰 수(50) + 평균평점(50) + 허위리뷰 감지(60) + 최근트렌드(40) |
| 취향 적합도 | 200 | LLM 일치도(150) + 카테고리 조건(50) |
| 신뢰도 | 100 | 쇼핑몰(60) + 판매자(40) |

- 예산 초과 상품: 소프트 필터 (가격 점수 감점, 목록 제외 X)
- 가중치: `user_preference` 테이블에서 동적 조정

## 태스크 유형

| 타입 | 설명 |
|------|------|
| `ONE_SHOT` | 1회 검색 후 완료 |
| `PERIODIC` | N주기마다 재검색 |
| `PRICE_WATCH` | 특정 상품 URL 가격 추적 |

## 개발 Phase

### Phase 0 — 환경 구성 (완료 기준: `make dev` 서버 실행)
- [ ] pyproject.toml + uv 설정
- [ ] SQLAlchemy 모델 정의 (6개 테이블)
- [ ] Alembic 마이그레이션
- [ ] FastAPI main.py (기본 라우터 + lifespan)
- [ ] config.py (.env 로드)
- [ ] Makefile 주요 명령어
- [ ] .gitignore, .env.example

### Phase 1 — MVP (완료 기준: CLI로 검색 → result.md Top 5 출력)
- [ ] 네이버쇼핑 API 스크래퍼 (`scraper/shops/naver.py`)
- [ ] LLM 분석 기본 (`llm/provider.py`, `llm/analyzer.py`)
- [ ] 기본 점수 산정 (가격 + 리뷰)
- [ ] Markdown 리포트 → `doc/mvp_result.md`
- [ ] CLI 진입점 (`shopigent/cli.py`)

### Phase 2 — 병렬 멀티 ShopAgent + 완전한 점수 시스템
> 핵심: 각 쇼핑몰이 독립 에이전트로 동작, 검색~스코어링까지 병렬 처리

- [ ] `BaseShopAgent` ABC 정의 (`agent/shop_agent.py`)
  - `search()`, `analyze()`, `score()` 인터페이스
  - `AgentResult` / `ScoredProduct` 데이터 계약
- [ ] `NaverShopAgent` 구현 (기존 NaverScraper 래핑)
- [ ] `ElevenStreetShopAgent` 구현 (httpx + BS4)
- [ ] `GmarketShopAgent` 구현 (httpx + BS4)
- [ ] `CoupangShopAgent` 구현 (공개 검색, robots.txt 준수)
- [ ] `AliExpressShopAgent` 구현 (Playwright)
- [ ] `SupervisorOrchestrator` 리팩토링
  - `asyncio.gather` + 타임아웃으로 병렬 에이전트 실행
  - 부분 실패 허용 (PARTIAL/FAILED 에이전트 스킵)
  - 전체 결과 통합 + 중복 제거 + 최종 Top 5
- [ ] 1000점 전체 점수 구현 (취향 적합도 포함)
- [ ] 리뷰 허위 감지 기본 구현

### Phase 3 — Web UI + 스케줄러 + 이메일
- [ ] HTMX 기반 Web UI (대시보드/태스크관리/리포트)
- [ ] APScheduler 연동 (cron 기반 자동 실행)
- [ ] 이메일 HTML 리포트 발송
- [ ] WebSocket 실시간 진행상황 (에이전트별 진행률 표시)

### Phase 4 — 온보딩 + 취향 시스템
- [ ] 5단계 온보딩 설문 UI
- [ ] 취향 가중치 → 점수 연동
- [ ] LLM 취향 프로파일 자동 생성

### Phase 5 — 미지정 쇼핑몰 신뢰성 검증
- [ ] ShopReliabilityValidator (도메인 나이, SSL, 사업자 등록)
- [ ] `GenericShopAgent` (Playwright + LLM DOM 파싱)
- [ ] 신뢰도 UI + 수동 승인 워크플로우

### Phase 6 — 가격 추적 + 고도화
- [ ] PRICE_WATCH 태스크 타입
- [ ] 가격 알림 이메일
- [ ] LLM 비용 추적 대시보드
- [ ] 성능 최적화 (캐싱, 에이전트 결과 재사용)

## 데이터 모델

```
user_profile (1) ─── (N) user_preference
                 ─── (N) search_task (1) ─── (N) search_task_run
                                                       │
                                               (N) product ─── (N) review
                                                       │
                                               (1) product_score
                                                       │
                                               (1) report
shop_reliability (별도, domain 기준)
```

## 주요 제약사항

- 쿠팡: robots.txt 정책 준수 (공개 검색 결과 수준만)
- Web UI: 로컬 전용 (127.0.0.1), 인증 불필요
- LLM: LiteLLM을 통해 추상화 (직접 API 호출 금지)
- 스크래핑: 요청 딜레이 2~8초, User-Agent 로테이션
- 에이전트 실패: 최소 1개 성공 시 리포트 생성 진행 (부분 실패 허용)
