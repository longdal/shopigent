# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**Shopigent** — AI 기반 개인 쇼핑 에이전트. 사용자 취향을 학습하여 자율적으로 상품을 검색하고, 1000점 만점 점수로 최적 상품 Top 5를 선정하여 Web UI와 이메일로 리포트를 제공합니다.

## 개발 추적 파일

개발 진행 시 다음 3개 파일을 반드시 업데이트하세요:
- `doc/plan.md` — 전체 개발 계획 및 아키텍처
- `doc/progress.md` — Phase별 진행 상황 (작업 시작/완료 시 업데이트)
- `doc/result.md` — 검색 실행 결과 및 테스트 결과

## 빠른 시작

```bash
# 의존성 설치 (uv 사용)
uv sync

# DB 마이그레이션
uv run alembic upgrade head

# 개발 서버 실행
make dev
# 또는
uv run uvicorn shopigent.main:app --reload --host 127.0.0.1 --port 8000

# Playwright 브라우저 설치 (최초 1회)
uv run playwright install chromium
```

## 주요 명령어

```bash
make dev          # 개발 서버 실행 (http://127.0.0.1:8000)
make test         # 전체 테스트 실행
make test-unit    # 단위 테스트만
make lint         # Ruff 린트
make format       # Ruff 포맷
make db-migrate   # Alembic 마이그레이션 적용
make db-revision  # 새 마이그레이션 파일 생성

# CLI 검색 (Phase 1 MVP)
uv run python -m shopigent.cli search "겨울 패딩"
```

## 아키텍처 핵심 구조

```
FastAPI (main.py) → API Routes → Agent Orchestrator
                              → APScheduler (주기 실행)
                              → WebSocket (실시간 진행상황)

Agent Orchestrator → Search Pipeline:
  1. QueryExpander (LLM) — 자연어 → 검색 키워드 확장
  2. ScraperFactory (병렬) — 쇼핑몰별 스크래퍼 실행
  3. ShopReliabilityValidator — 미지정 쇼핑몰 신뢰도 검증
  4. LLM ProductAnalyzer — 상품 품질/취향 부합도 분석
  5. ScoringEngine — 1000점 계산
  6. RankingEngine → Top 5
  7. ReportGenerator → HTML + doc/result.md + 이메일
```

## 핵심 모듈 위치

| 모듈 | 경로 | 역할 |
|------|------|------|
| 앱 진입점 | `shopigent/main.py` | FastAPI 앱 + APScheduler lifespan |
| 설정 | `shopigent/config.py` | Pydantic Settings, .env 로드 |
| DB 세션 | `shopigent/database.py` | SQLAlchemy async 세션 |
| 파이프라인 | `shopigent/agent/orchestrator.py` | 검색 파이프라인 총괄 |
| 점수 엔진 | `shopigent/scoring/engine.py` | 1000점 만점 핵심 로직 |
| LLM 추상화 | `shopigent/llm/provider.py` | LiteLLM 래퍼 (모델 전환 단일 진입점) |
| 스크래퍼 계약 | `shopigent/scraper/base.py` | BaseScraper ABC |
| DB 모델 | `shopigent/models/` | SQLAlchemy ORM |

## 대상 쇼핑몰

| 쇼핑몰 | 스크래퍼 | 비고 |
|--------|---------|------|
| 네이버쇼핑 | `scraper/shops/naver.py` | 공식 검색 API 우선 활용 |
| 11번가 | `scraper/shops/eleven_street.py` | httpx + BS4 |
| G마켓 | `scraper/shops/gmarket.py` | httpx + BS4 |
| 쿠팡 | `scraper/shops/coupang.py` | robots.txt 준수, 공개 검색만 |
| AliExpress | `scraper/shops/aliexpress.py` | Playwright |
| 미지정 쇼핑몰 | `scraper/shops/generic.py` | Playwright + LLM DOM 파싱 |

## 1000점 만점 점수 구성

| 항목 | 최대 | 가중치 조정 |
|------|------|------------|
| 가격 (예산 대비 + 배송비) | 250점 | user_preference.weight_price |
| 품질 (재질/브랜드/스펙) | 250점 | user_preference.weight_quality |
| 리뷰 (수/평점/신뢰도/트렌드) | 200점 | user_preference.weight_review_quality |
| 취향 적합도 (LLM 평가) | 200점 | user_preference.weight_preference_fit |
| 쇼핑몰+판매자 신뢰도 | 100점 | 고정 |

예산 초과 상품은 소프트 필터 (가격 점수 감점, 목록 제외 안 함).

## LLM 모델 전환

`.env`의 `LLM_PRIMARY_MODEL` 값만 변경하면 모델 전환 가능:
```bash
LLM_PRIMARY_MODEL=claude-sonnet-4-6      # 기본
LLM_PRIMARY_MODEL=gpt-4o-mini            # 비용 절감
LLM_PRIMARY_MODEL=ollama/mistral         # 로컬 실행
```
`shopigent/llm/provider.py`의 `LLMProvider` 클래스가 LiteLLM을 통해 단일 인터페이스 제공.

## 개발 규칙

- 모든 DB 접근은 `async` 세션 사용 (`aiosqlite`)
- 스크래퍼는 `BaseScraper` ABC를 반드시 구현
- 새 스크래퍼 추가 시 `ScraperFactory`에 등록
- LLM 호출은 반드시 `LLMProvider`를 통해 (직접 API 호출 금지)
- 점수 계산 로직은 `scoring/calculators/` 하위 개별 파일에 분리
- 환경변수는 `config.py`의 `Settings` 클래스로만 접근

## 환경 설정

`.env.example` 복사 후 값 채우기:
```bash
cp .env.example .env
```

필수 설정:
- `ANTHROPIC_API_KEY` — Claude API 키
- `SMTP_*` — 이메일 발송 설정
- `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` — 네이버 검색 API (Phase 1)

## 멀티 에이전트 개발 워크플로우

모든 개발은 GitHub Issues 기반으로 추적하며, TDD(Red→Green→Refactor) 방식을 따른다.
PR은 사용자 확인 후 머지한다. 자동 머지 금지.

---

### Git 브랜치 전략

```
main          ← 안정 릴리즈만 (release 머지 시점)
develop       ← 개발 통합 브랜치 (feature 브랜치들의 머지 대상)
feature/{N}   ← Issue 번호별 기능 브랜치 (예: feature/12)
release/vX.X.X ← 릴리즈 준비 브랜치 (develop → release → main)
```

**브랜치 생성 규칙**:
```bash
# 기능 개발 시작
git checkout develop
git pull origin develop
git checkout -b feature/{issue-번호}

# 릴리즈 준비
git checkout -b release/v1.0.0 develop
```

---

### 에이전트 역할 분리

| 에이전트 | 역할 | 담당 작업 |
|---------|------|---------|
| **Supervisor** | 조율·통합 | 작업 분해, Issue 생성, 브랜치 관리, PR 생성, 최종 보고 |
| **DevAgent** | 구현 전담 | TDD 사이클 실행, 코드 작성, 단위 테스트, 동작 검증 |
| **ReviewAgent** | 리뷰 전담 | 코드 품질 검토, 보안/성능/설계 리뷰, 리뷰 코멘트 작성 |

---

### 디렉토리 구조

```
agents/
├── supervisor/
│   ├── plan.md       ← 전체 작업 분해 + Issue 번호 + 브랜치 목록
│   ├── process.md    ← 에이전트별 완료 현황 추적
│   └── result.md     ← 최종 통합 결과
├── agent-001-dev/    ← DevAgent (구현 담당)
│   ├── plan.md       ← 담당 Issue, 브랜치명, 구현 방식
│   ├── process.md    ← TDD 단계별 체크리스트
│   └── result.md     ← 완료 파일 목록, 테스트 결과
├── agent-001-review/ ← ReviewAgent (리뷰 담당)
│   ├── plan.md       ← 리뷰 대상 PR 번호, 리뷰 기준
│   ├── process.md    ← 리뷰 체크리스트 진행
│   └── result.md     ← 리뷰 결과 (승인/수정요청 + 상세 내용)
└── ...
```

---

### GitHub Issues 라벨 체계

| 라벨 | 용도 |
|------|------|
| `task` | 구현 작업 |
| `bug` | 버그 / 오류 |
| `phase-0` ~ `phase-6` | 해당 Phase |
| `needs-review` | ReviewAgent 리뷰 대기 |
| `needs-fix` | 리뷰 후 수정 필요 |
| `approved` | 리뷰 통과, PR 머지 대기 중 |
| `blocked` | 선행 Issue 완료 대기 |

---

### Issue 생성 형식

**작업 Issue**:
```bash
gh issue create \
  --title "[Phase-N] 기능명 구현" \
  --body "## 목표
...
## 완료 조건
- [ ] Red: 실패 테스트 작성
- [ ] Green: 테스트 통과 구현
- [ ] Refactor: 코드 개선
- [ ] 동작 검증
- [ ] 리뷰 통과" \
  --label "task,phase-N"
```

**버그 Issue**:
```bash
gh issue create \
  --title "[BUG] 오류 설명" \
  --body "## 증상
...
## 재현 방법
...
## 예상 원인
..." \
  --label "bug,phase-N"
```

---

### TDD 사이클 (DevAgent 필수 준수)

각 기능 구현은 반드시 Red → Green → Refactor 순서로 진행한다.
**한 번에 테스트 하나씩** — 하나의 테스트를 작성하고, 통과시키고, 구조를 개선한다.

```
🔴 RED
  1. 기능의 작은 단위를 정의하는 실패 테스트 하나만 작성
     - 테스트 이름은 동작을 설명 (예: test_should_return_top5_ranked_products)
     - 실패 메시지가 명확하고 이해 가능해야 함
  2. make test 실행 → 해당 테스트가 실패함을 확인 (필수)
  3. process.md에 "Red 완료" 체크

🟢 GREEN
  4. 테스트를 통과하는 최소한의 코드만 작성 (과도한 구현 금지)
  5. make test 실행 → 전체 테스트 통과 확인
  6. process.md에 "Green 완료" 체크

🔵 REFACTOR (Tidy First)
  7. 구조적 변경과 동작 변경을 반드시 분리 (아래 Tidy First 원칙 참조)
  8. make lint 통과 확인
  9. make test 재실행 → 여전히 통과 확인
 10. process.md에 "Refactor 완료" 체크
 11. 다음 기능 단위로 RED부터 반복
```

---

### Tidy First 원칙 (Kent Beck)

모든 변경은 **구조 변경(Structural)**과 **동작 변경(Behavioral)** 중 하나에만 속해야 한다.
**두 가지를 같은 커밋에 절대 섞지 않는다.**

| 구분 | 설명 | 예시 |
|------|------|------|
| **구조 변경** | 동작은 그대로, 코드 구조만 변경 | 함수 추출, 이름 변경, 파일 이동, 중복 제거 |
| **동작 변경** | 새 기능 추가 또는 기존 동작 수정 | 새 메서드 구현, 버그 수정, 로직 변경 |

**규칙**:
- 구조 변경이 필요하면 동작 변경 전에 먼저 수행
- 구조 변경 후 `make test` → 통과 확인 → 커밋 (구조 커밋)
- 그 후 동작 변경 → 테스트 → 커밋 (동작 커밋)

---

### 커밋 규율

커밋은 아래 조건이 **모두** 충족될 때만 수행한다:

- [ ] `make test` 전체 통과
- [ ] `make lint` 경고 0개
- [ ] 단일 논리 단위의 변경 (구조 또는 동작, 둘 중 하나만)

**커밋 메시지 형식**:
```
[structural] 함수 추출: score 계산을 _calculate_price_score()로 분리
[behavioral] NaverShopAgent.search() 구현 - API 호출 + 결과 파싱
[behavioral][fix] 예산 초과 시 가격 점수 감점 로직 수정
```

**작은 커밋 원칙**: 크고 드문 커밋보다 작고 잦은 커밋을 지향한다.

---

### 버그 수정 TDD 패턴

버그 발견 시 다음 순서로 진행한다:

```
1. API 수준 실패 테스트 작성 (사용자 관점 재현)
   → 예: test_cli_search_returns_5_results_when_naver_fails

2. 최소 단위 실패 테스트 작성 (버그 원인 정확히 핀포인트)
   → 예: test_orchestrator_skips_failed_agent_and_continues

3. 두 테스트를 모두 통과시키는 수정 구현

4. make test 전체 통과 확인

5. Bug Issue에 재현 테스트 코드 + 수정 내용 코멘트
```

---

### 전체 워크플로우

```
[Supervisor]
  1. supervisor/plan.md 작성 (작업 분해 + Issue 생성)
  2. 각 Issue마다 feature/{N} 브랜치 생성
  3. DevAgent 병렬 실행 (Issue별, Agent 툴 사용)

[DevAgent — feature/{N} 브랜치에서]
  4. Issue에 "작업 시작" 코멘트
     gh issue comment {N} --body "🚀 작업 시작 (DevAgent)"
  5. TDD: Red → Green → Refactor 사이클 실행
  6. 동작 검증 (CLI 실행 또는 서버 응답 확인)
  7. feature/{N} → develop PR 생성
     gh pr create --base develop --head feature/{N} \
       --title "[#{N}] 기능명" --body "Closes #{N}"
  8. PR 번호를 Supervisor에 보고

[Supervisor]
  9. Issue 라벨 변경: needs-review 추가
 10. ReviewAgent 실행 (PR 번호 전달)

[ReviewAgent — PR 리뷰]
 11. 코드 변경사항 전체 검토
     - 설계 적합성 (CLAUDE.md 개발 규칙 준수)
     - 테스트 커버리지 충분성
     - 보안 취약점 없음
     - 성능 이슈 없음
 12. 수정 필요 시 → PR 코멘트 작성 + Issue에 needs-fix 라벨
     DevAgent 수정 후 재리뷰 (5번으로 돌아감)
 13. 승인 시 → result.md에 리뷰 통과 기록 + approved 라벨

[Supervisor → 사용자]
 14. PR 링크 + 리뷰 결과 요약 보고
     "PR #{PR번호} 리뷰 완료. 머지 승인 요청드립니다."
 15. ⏸ 사용자 승인 대기 (자동 머지 금지)
 16. 사용자 승인 후 → feature/{N} → develop 머지
 17. Issue close
```

---

### ReviewAgent 리뷰 체크리스트

```
코드 품질
- [ ] CLAUDE.md 개발 규칙 준수 (async, BaseScraper, LLMProvider 등)
- [ ] 함수/변수 명명이 의도를 드러내는가
- [ ] 중복 코드 없음
- [ ] 불필요한 복잡도 없음

테스트
- [ ] TDD Red-Green-Refactor 사이클 준수
- [ ] 핵심 경로 단위 테스트 존재
- [ ] 경계값/예외 케이스 테스트 포함
- [ ] make test 통과

안정성
- [ ] 예외 처리 적절함
- [ ] 비동기 처리 올바름 (async/await)
- [ ] 리소스 누수 없음 (DB 세션, HTTP 커넥션)

보안
- [ ] 외부 입력값 검증
- [ ] 민감 정보 로그 출력 없음
- [ ] SQL Injection / XSS 취약점 없음
```

---

### Supervisor 자동 수정 규칙

| 문제 유형 | 조치 |
|---------|------|
| 린트/타입 오류 | DevAgent 직접 수정 후 재커밋 |
| 테스트 실패 | Bug Issue 등록 → DevAgent 수정 → 재검증 |
| 리뷰 수정 요청 | needs-fix 라벨 → DevAgent 수정 → ReviewAgent 재리뷰 |
| 동작 검증 실패 | Bug Issue 등록 → 수정 → 재검증 |
| 요구사항 누락 | 기존 Issue 재오픈 또는 새 task Issue 등록 |

---

### 릴리즈 프로세스

```bash
# develop이 안정적일 때 릴리즈 브랜치 생성
git checkout -b release/vX.X.X develop

# 릴리즈 테스트 통과 후 main 머지 (사용자 확인 필요)
gh pr create --base main --head release/vX.X.X \
  --title "Release vX.X.X" --body "릴리즈 내용..."
```
