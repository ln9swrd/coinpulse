# CoinPulse 알림 시스템 사양서

## 문서 정보
- **작성일**: 2025.12.22
- **최종 수정**: 2025.12.22 (v2.0 - 시스템 재설계)
- **목적**: 투자조언 알림과 급등 알림 자동매매 시스템 정의

---

## 핵심 개념

### 두 가지 독립적인 시스템

```
┌─────────────────────────────────────────────────────────┐
│                    CoinPulse 알림 시스템                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. 투자조언 알림                2. 급등 알림 자동매매    │
│  (Investment Advisory)          (Surge Auto Trading)    │
│                                                          │
│  - 선택한 코인                  - 전체 마켓 스캔         │
│  - 투자 조언 알림               - 급등 감지              │
│  - 수동 판단                    - 자동 매수              │
│  - 알림만 제공                  - 예산/금액 설정         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 1. 투자조언 알림 (Investment Advisory)

### 개요
사용자가 선택한 코인(보유 중이거나 관심 있는 코인)에 대해 CoinPulse가 투자 조언을 제공

### 특징
- **사용자가 코인 선택** (요금제별 개수 제한)
- **알림만 제공** (자동 실행 없음)
- 매수/매도 타이밍, 손절 추천 등
- 텔레그램 알림

### 요금제별 제한

| 플랜 | 선택 가능 코인 수 | 알림 제공 |
|------|------------------|----------|
| Free | 0개 | 불가 |
| Basic | 3개 | 가능 |
| Pro | 5개 | 가능 |

### 알림 예시

```
[투자조언 알림]

코인: BTC (비트코인)
현재가: 52,000,000원

조언: 매수 타이밍
신뢰도: 85%
근거:
- 지지선 돌파 (51,500,000원)
- RSI 과매도 구간 탈출
- 거래량 20% 증가

추천 액션: 분할 매수 고려
목표가: 54,000,000원 (+3.8%)
손절가: 50,500,000원 (-2.9%)

[상세보기] [투자조언 설정]
```

### 데이터베이스 스키마

```sql
CREATE TABLE user_advisory_coins (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    coin VARCHAR(10) NOT NULL,           -- 'BTC', 'ETH', etc.
    market VARCHAR(20) NOT NULL,         -- 'KRW-BTC'
    alert_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, coin)
);
```

### API 엔드포인트

- `GET /api/user/advisory-coins` - 투자조언 코인 목록 조회
- `POST /api/user/advisory-coins` - 투자조언 코인 추가
- `DELETE /api/user/advisory-coins/<coin>` - 삭제

---

## 2. 급등 알림 자동매매 (Surge Auto Trading)

### 개요
시스템이 전체 마켓을 스캔하여 급등 신호를 감지하고, 사용자가 미리 설정한 예산/금액으로 자동 매수

### 특징
- **시스템이 자동 스캔** (전체 마켓)
- **자동 매수 실행** (사용자 설정 기반)
- 요금제별 주간 횟수 제한
- 예산 소진 시 자동 중지

### 사용자 설정 항목

```
급등 알림 자동매매 설정:

[기본 설정]
- 활성화: ON/OFF
- 총 예산: 1,000,000원
- 1회 투자금액: 100,000원

[위험 관리]
- 위험도: 보수적 / 중립 / 공격적
- 손절매: 활성화 (-5%)
- 익절: 활성화 (+10%)

[필터링]
- 최소 신뢰도: 80%
- 최대 보유 종목 수: 5개
- 제외 코인: DOGE, SHIB (설정 가능)

[알림]
- 텔레그램 알림: ON
- 매수 시 알림: ON
- 손익 알림: ON
```

### 요금제별 제한

| 플랜 | 주간 자동매수 횟수 | 총 예산 제한 |
|------|-------------------|-------------|
| Free | 0회 (대시보드 확인만) | 불가 |
| Basic | 주 5회 (실제) | 500만원 |
| Pro | 주 20회 (실제) | 무제한 |

**마케팅 전략**:
- Basic: "주 3회" 표시 → 실제 5회 제공
- Pro: "주 10회" 표시 → 실제 20회 제공

### 동작 흐름

```
[1단계: 급등 감지]
  - 시스템이 5분마다 전체 마켓 스캔
  - 급등 신호 감지 (AI 예측 81.25% 정확도)
  - 신뢰도 계산: 85%

[2단계: 설정 확인]
  - 사용자 설정 확인
    ✓ 활성화: ON
    ✓ 총 예산: 1,000,000원 (잔액: 800,000원)
    ✓ 1회 금액: 100,000원
    ✓ 최소 신뢰도: 80% (85% 충족)
    ✓ 주간 횟수: 3/5회 (여유 있음)
    ✓ 최대 보유: 3/5개 (여유 있음)

[3단계: 자동 매수]
  - 매수 주문 실행: DOGE 100,000원
  - 손절가 설정: -5%
  - 익절가 설정: +10%

[4단계: 알림 전송]
  텔레그램: "DOGE 급등 감지 - 10만원 자동 매수 완료"
```

### 알림 예시

```
[급등 알림 자동매매]

코인: DOGE (도지코인)
신뢰도: 85%
매수 완료: 100,000원
수량: 555 DOGE
평균 단가: 180원

손절가: 171원 (-5%)
익절가: 198원 (+10%)

이번 주 남은 횟수: 2/5회
잔여 예산: 700,000원

[포지션 확인] [설정 변경]
```

### 시나리오별 동작

#### 시나리오 1: 정상 매수
- 조건: 모든 조건 충족
- 결과: 자동 매수 실행 + 알림

#### 시나리오 2: 예산 부족
- 조건: 잔여 예산 < 1회 투자금액
- 결과: 매수 미실행 + 알림 (예산 충전 필요)

#### 시나리오 3: 주간 한도 초과
- 조건: 이번 주 5/5회 사용
- 결과: 매수 미실행 + 알림 (다음 주 월요일 리셋)

#### 시나리오 4: 최대 보유 종목 초과
- 조건: 이미 5개 종목 보유
- 결과: 매수 미실행 (기존 종목 청산 후 가능)

#### 시나리오 5: 신뢰도 미달
- 조건: 급등 신뢰도 75% < 최소 신뢰도 80%
- 결과: 매수 미실행 (알림 없음)

### 데이터베이스 스키마

```sql
-- 급등 자동매매 설정
CREATE TABLE surge_auto_trading_settings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,

    -- 기본 설정
    enabled BOOLEAN DEFAULT false,
    total_budget BIGINT NOT NULL,           -- 총 예산 (원)
    amount_per_trade BIGINT NOT NULL,       -- 1회 투자금액 (원)

    -- 위험 관리
    risk_level VARCHAR(20) DEFAULT 'moderate',  -- conservative/moderate/aggressive
    stop_loss_enabled BOOLEAN DEFAULT true,
    stop_loss_percent FLOAT DEFAULT -5.0,
    take_profit_enabled BOOLEAN DEFAULT true,
    take_profit_percent FLOAT DEFAULT 10.0,

    -- 필터링
    min_confidence FLOAT DEFAULT 80.0,
    max_positions INTEGER DEFAULT 5,
    excluded_coins JSON,                     -- ['DOGE', 'SHIB']

    -- 알림
    telegram_enabled BOOLEAN DEFAULT true,

    -- 통계
    total_trades INTEGER DEFAULT 0,
    successful_trades INTEGER DEFAULT 0,
    total_profit_loss BIGINT DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 급등 알림 기록 (기존 surge_alerts 테이블 확장)
CREATE TABLE surge_alerts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    market VARCHAR(20) NOT NULL,
    coin VARCHAR(10) NOT NULL,
    confidence FLOAT NOT NULL,

    -- 가격 정보
    entry_price BIGINT,
    target_price BIGINT,
    stop_loss_price BIGINT,

    -- 자동매매 정보
    auto_traded BOOLEAN DEFAULT false,      -- 자동 매수 여부
    trade_amount BIGINT,                     -- 매수 금액
    trade_quantity FLOAT,                    -- 매수 수량
    order_id VARCHAR(50),                    -- Upbit 주문 ID

    -- 결과 정보
    status VARCHAR(20),                      -- pending/executed/stopped/completed
    profit_loss BIGINT,                      -- 손익 금액
    profit_loss_percent FLOAT,               -- 손익률

    -- 시간 정보
    sent_at TIMESTAMP NOT NULL,
    executed_at TIMESTAMP,
    closed_at TIMESTAMP,
    week_number INTEGER NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 비교 요약

| 항목 | 투자조언 알림 | 급등 알림 자동매매 |
|------|--------------|-------------------|
| **대상** | 사용자 선택 코인 | 시스템 스캔 전체 |
| **알림 방식** | 투자 조언 | 자동 매수 완료 |
| **실행** | 수동 판단 | 자동 실행 |
| **설정** | 코인 목록 | 예산, 금액, 위험도 |
| **요금제 제한** | 코인 개수 (0/3/5) | 주간 횟수 (0/5/20) |
| **목적** | 정보 제공 | 자동 수익 창출 |

---

## API 엔드포인트 목록

### 투자조언 알림
- `GET /api/user/advisory-coins` - 조언 코인 목록
- `POST /api/user/advisory-coins` - 코인 추가
- `DELETE /api/user/advisory-coins/<coin>` - 삭제

### 급등 알림 자동매매
- `GET /api/surge/auto-trading/settings` - 설정 조회
- `PUT /api/surge/auto-trading/settings` - 설정 수정
- `GET /api/surge/auto-trading/positions` - 현재 포지션
- `GET /api/surge/auto-trading/history` - 거래 내역
- `GET /api/surge/alerts` - 알림 기록
- `GET /api/surge/alerts/weekly-count` - 주간 횟수

---

## 구현 우선순위

### Phase 1 (완료)
- ✅ 데이터베이스 스키마 설계
- ✅ 기본 API 엔드포인트 구현
- ✅ 요금제별 제한 로직

### Phase 2 (진행 중)
- 🔄 투자조언 알림 시스템
- 🔄 급등 자동매매 설정 UI
- 🔄 자동 매수/매도 로직

### Phase 3 (예정)
- ⏳ 손익 자동 계산
- ⏳ 포지션 관리 대시보드
- ⏳ 성과 통계 및 리포트

---

## 보안 및 리스크 관리

### 자금 보호
- 예산 초과 방지 (hard limit)
- 1회 투자금액 검증
- 최대 보유 종목 제한

### 리스크 관리
- 자동 손절매 (설정값 기준)
- 자동 익절 (목표가 달성 시)
- 급등 신뢰도 필터링

### 모니터링
- 실시간 포지션 추적
- 손익 현황 대시보드
- 이상 거래 감지 및 알림

---

## 문의
- 개발팀: dev@coinpulse.ai
- 문서 위치: `/docs/features/SURGE_ALERT_SYSTEM.md`
