# CoinPulse 급등 알림 시스템 사양서

## 📋 문서 정보
- **작성일**: 2025.12.22
- **버전**: 1.0
- **목적**: 급등 알림 시스템의 용어, 로직, 요금제별 기능을 명확히 정의

---

## 🎯 핵심 개념

### 용어 정의

| 용어 | 영문 | 정의 | 예시 |
|------|------|------|------|
| **급등 모니터링** | Surge Monitoring | 시스템이 전체 마켓을 스캔하여 가격 급등을 감지하는 기능 | BTC가 5분 내 3% 상승 감지 |
| **급등 신호** | Surge Signal | 고신뢰도(80%+) 급등 예측 결과 | "BTC 급등 예상 (신뢰도 85%)" |
| **급등 알림** | Surge Alert | 급등 신호를 텔레그램으로 사용자에게 전송 | 텔레그램: "BTC 매수 추천 (85%)" |
| **관심 코인** | Favorite Coins | 사용자가 설정에서 선택한 우선 모니터링 코인 (최대 5개) | BTC, ETH, XRP, ADA, SOL |
| **자동매매 실행** | Auto Trading Execution | 알림 받고 실제로 거래를 자동 체결 (향후 구현) | 시스템이 자동으로 BTC 매수 주문 |

### 기능 분리

```
[급등 모니터링] (System)
   │
   ├─> [급등 신호 생성] (AI Prediction)
   │
   ├─> [필터링] (User Settings + Plan Limits)
   │    ├─ 관심 코인 우선
   │    ├─ 요금제별 제한
   │    └─ 보유 코인 처리
   │
   ├─> [급등 알림 전송] (Telegram)
   │
   └─> [자동매매 실행] (향후 구현)
```

---

## 🔧 관심 코인 설정 (설정 → 관심 코인 탭)

### 목적
사용자가 우선적으로 모니터링하고 알림을 받을 코인을 선택

### 기능

#### 1. 코인 선택
- **최대 5개** 코인 선택 가능
- 선택 가능 코인: BTC, ETH, XRP, ADA, SOL, DOGE, DOT, MATIC, LTC, LINK
- 체크박스 UI (직관적 선택)

#### 2. 각 코인별 설정

```
┌─────────────────────────────────┐
│ 비트코인 (BTC)                    │
├─────────────────────────────────┤
│ ☑ 급등 알림 받기                  │ ← 이 코인의 급등 신호를 알림 받을지
│ ☐ 자동매매 활성화 (Pro 전용)      │ ← 향후: 자동으로 거래 실행
│                                  │
│ 위험 허용도: [중립 ▼]             │ ← 보수적/중립/공격적
│ ☐ 손절매 활성화                   │ ← 자동 손절매 여부
└─────────────────────────────────┘
```

#### 설정 저장
- **저장 위치**: localStorage (클라이언트)
- **저장 형식**:
```json
{
  "selectedCoins": ["BTC", "ETH", "XRP"],
  "BTC": {
    "alertEnabled": true,
    "autoTradingEnabled": false,
    "risk": "moderate",
    "stopLoss": true
  },
  "ETH": {
    "alertEnabled": true,
    "autoTradingEnabled": false,
    "risk": "aggressive",
    "stopLoss": false
  }
}
```

---

## 📊 요금제별 기능

### Free 플랜 (무료)

| 기능 | 제공 여부 | 설명 |
|------|-----------|------|
| 급등 모니터링 | ✅ | 대시보드에서 급등 코인 확인 가능 (view only) |
| 텔레그램 알림 | ❌ | 알림 없음 |
| 관심 코인 설정 | ❌ | 선택 불가 |
| 자동매매 | ❌ | 불가 |

**사용자 경험**:
- 대시보드 → 급등 모니터링 페이지에서 현재 급등 중인 코인 확인
- "업그레이드하여 알림 받기" 배너 표시

---

### Basic 플랜 (₩49,000/월)

| 기능 | 제공 여부 | 세부사항 |
|------|-----------|----------|
| 급등 모니터링 | ✅ | 대시보드에서 확인 |
| 텔레그램 알림 | ✅ | **주 3회** 표시 (실제: 5회) |
| 관심 코인 설정 | ✅ | **최대 5개** 선택 |
| 자동매매 | ❌ | 불가 |

**알림 우선순위**:
1. 관심 코인 급등 신호 (신뢰도 80%+)
2. 관심 코인 외 급등 신호 (신뢰도 90%+)

**주간 제한**:
- 표시: "주 3회 알림"
- 실제: 5회 제공 (마케팅 전략)
- 초과 시: "이번 주 알림 한도 초과. 다음 주에 다시 알림받을 수 있습니다."

---

### Pro 플랜 (₩99,000/월)

| 기능 | 제공 여부 | 세부사항 |
|------|-----------|----------|
| 급등 모니터링 | ✅ | 대시보드에서 확인 |
| 텔레그램 알림 | ✅ | **주 10회** 표시 (실제: 20회) |
| 관심 코인 설정 | ✅ | **최대 5개** 선택 |
| 자동매매 | ✅ | **향후 구현** (현재는 알림만) |

**알림 우선순위**:
1. 관심 코인 급등 신호 (신뢰도 75%+)
2. 관심 코인 외 급등 신호 (신뢰도 85%+)

**주간 제한**:
- 표시: "주 10회 알림"
- 실제: 20회 제공 (마케팅 전략)

---

## 🎬 시스템 동작 흐름

### 1. 급등 신호 감지 (매 5분)

```python
# backend/services/surge_predictor.py
for market in all_markets:
    confidence = predict_surge(market)
    if confidence >= 80:
        create_surge_signal(market, confidence)
```

### 2. 사용자 필터링

```python
# backend/services/surge_alert_scheduler.py
for user in active_users:
    # 요금제 확인
    plan = user.plan  # 'free', 'basic', 'pro'

    if plan == 'free':
        continue  # 알림 없음

    # 주간 알림 횟수 확인
    alerts_this_week = count_alerts(user, current_week)
    max_alerts = get_max_alerts(plan)  # basic: 5, pro: 20

    if alerts_this_week >= max_alerts:
        continue  # 한도 초과

    # 관심 코인 확인
    favorite_coins = get_favorite_coins(user)

    # 알림 전송 조건
    if signal.market in favorite_coins:
        if signal.confidence >= 80:  # basic
            send_alert(user, signal)
    else:
        if signal.confidence >= 90:  # basic, 관심 코인 아닌 경우
            send_alert(user, signal)
```

### 3. 텔레그램 알림 전송

```
📈 급등 알림

코인: BTC (비트코인)
신뢰도: 85%
현재가: ₩95,000,000
예상 목표가: ₩98,000,000 (+3.2%)

[상세보기] [관심 코인에 추가]

이번 주 남은 알림: 2/5회
```

---

## 🔄 시나리오별 동작

### 시나리오 1: 관심 코인 급등 (일반적인 경우)

**조건**:
- 사용자: Basic 플랜
- 관심 코인: BTC, ETH, XRP (BTC 알림 활성화)
- 시스템: BTC 급등 감지 (신뢰도 85%)

**동작**:
1. ✅ 요금제 확인: Basic (알림 가능)
2. ✅ 주간 알림 횟수: 3/5회 (여유 있음)
3. ✅ 관심 코인 포함: BTC (알림 활성화)
4. ✅ 신뢰도 충족: 85% >= 80%
5. ✅ 텔레그램 알림 전송
6. ✅ 알림 횟수 증가: 4/5회

**결과**: 알림 전송 성공

---

### 시나리오 2: 이미 보유 중인 코인 급등

**조건**:
- 사용자: Pro 플랜
- 보유 코인: BTC 1,000,000원 (현재 수익률 +5%)
- 관심 코인: BTC (알림 활성화)
- 시스템: BTC 추가 급등 감지 (신뢰도 90%)

**동작**:
1. ✅ 요금제 확인: Pro (알림 가능)
2. ✅ 주간 알림 횟수: 10/20회 (여유 있음)
3. ✅ 관심 코인 포함: BTC (알림 활성화)
4. ✅ 보유 여부 확인: **이미 보유 중**
5. ✅ 알림 타입 변경: **"추가 매수 기회"**
6. ✅ 텔레그램 알림 전송

**알림 내용**:
```
📈 추가 매수 기회

코인: BTC (비트코인)
현재 보유: 1,000,000원 (+5%)
추가 급등 예상: 90% 신뢰도

추가 매수 시 예상 수익률: +12%

[추가 매수] [보유 유지]
```

**결과**: 추가 매수 기회 알림 전송

---

### 시나리오 3: 관심 코인 아닌 코인 급등

**조건**:
- 사용자: Basic 플랜
- 관심 코인: BTC, ETH (DOGE 없음)
- 시스템: DOGE 급등 감지 (신뢰도 95%)

**동작**:
1. ✅ 요금제 확인: Basic (알림 가능)
2. ✅ 주간 알림 횟수: 4/5회 (여유 있음)
3. ❌ 관심 코인 미포함: DOGE
4. ✅ 신뢰도 매우 높음: 95% >= 90%
5. ✅ 텔레그램 알림 전송 (특별 알림)

**알림 내용**:
```
🔥 고신뢰도 급등 알림

코인: DOGE (도지코인)
신뢰도: 95% ⭐
현재가: ₩180
예상 상승률: +8%

[관심 코인에 추가] [상세보기]

💡 관심 코인에 추가하면 우선 알림을 받을 수 있습니다.
```

**결과**: 특별 알림 전송 (관심 코인 추가 유도)

---

### 시나리오 4: 주간 한도 초과

**조건**:
- 사용자: Basic 플랜
- 주간 알림 횟수: 5/5회 (한도 도달)
- 시스템: ETH 급등 감지 (신뢰도 88%)

**동작**:
1. ✅ 요금제 확인: Basic (알림 가능)
2. ❌ 주간 알림 횟수: 5/5회 (한도 초과)
3. ❌ 알림 전송 중단

**사용자 경험**:
- 텔레그램 알림 없음
- 대시보드에는 표시됨
- 다음 주 월요일 00:00에 한도 리셋

**대시보드 메시지**:
```
⚠️ 이번 주 알림 한도 초과

이번 주 알림을 모두 사용했습니다.
다음 주 월요일부터 다시 알림을 받을 수 있습니다.

[Pro로 업그레이드] (주 10회 → 더 많은 기회)
```

**결과**: 알림 미전송 (한도 초과)

---

### 시나리오 5: Free 플랜 사용자

**조건**:
- 사용자: Free 플랜
- 시스템: BTC, ETH, DOGE 급등 감지

**동작**:
1. ❌ 요금제 확인: Free (알림 불가)
2. ❌ 텔레그램 알림 전송하지 않음
3. ✅ 대시보드에만 표시

**사용자 경험**:
- 대시보드 → 급등 모니터링 페이지에 급등 코인 리스트 표시
- 각 코인 옆에 "알림 받기" 버튼 → 클릭 시 업그레이드 페이지

**결과**: 알림 없음 (대시보드에서만 확인 가능)

---

## 🛠️ 구현 상태

### 완료된 기능 ✅

- [x] 급등 예측 알고리즘 (신뢰도 81.25%)
- [x] 텔레그램 봇 연동
- [x] 요금제별 기능 제한
- [x] 관심 코인 설정 UI
- [x] 대시보드 급등 모니터링 페이지

### 구현 필요 🔲

- [ ] 주간 알림 횟수 카운팅 로직
- [ ] 보유 코인 급등 시 "추가 매수" 알림
- [ ] 관심 코인 외 고신뢰도 알림
- [ ] 알림 우선순위 필터링
- [ ] 자동매매 실행 (Pro 플랜 전용)

---

## 📝 데이터베이스 스키마

### surge_alerts 테이블
```sql
CREATE TABLE surge_alerts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    market VARCHAR(20) NOT NULL,  -- 'KRW-BTC'
    confidence FLOAT NOT NULL,    -- 85.5
    signal_type VARCHAR(20),      -- 'favorite', 'high_confidence', 'additional_buy'
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    week_number INTEGER NOT NULL, -- 202452 (년+주차)
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_alerts_user_week ON surge_alerts(user_id, week_number);
```

### user_favorite_coins 테이블
```sql
CREATE TABLE user_favorite_coins (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    coin VARCHAR(10) NOT NULL,    -- 'BTC'
    alert_enabled BOOLEAN DEFAULT true,
    auto_trading_enabled BOOLEAN DEFAULT false,
    risk_level VARCHAR(20) DEFAULT 'moderate',  -- 'conservative', 'moderate', 'aggressive'
    stop_loss_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, coin)
);
```

---

## 🔐 보안 및 성능

### Rate Limiting
- 각 사용자당 최대 API 호출: 100회/시간
- 텔레그램 알림: 요금제별 주간 제한

### 캐싱 전략
- 급등 신호: 5분 캐시
- 사용자 설정: 60초 캐시
- 요금제 정보: 300초 캐시

### 모니터링
- 알림 전송 성공률 추적
- 신호 정확도 추적
- 사용자 피드백 수집

---

## 📞 문의

시스템 관련 문의사항은 다음으로 연락주세요:
- 개발팀: dev@coinpulse.ai
- 시스템 문서: `/docs/features/SURGE_ALERT_SYSTEM.md`
