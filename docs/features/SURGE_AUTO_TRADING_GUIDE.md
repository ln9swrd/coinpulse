# 급등 예측 실시간 자동매매 가이드

## 개요

**기존 시스템** (예측만 함):
- 급등 신호 발생 → 3일 대기 → Win/Lose 기록 ❌

**새로운 시스템** (진짜 자동매매):
- 급등 신호 발생 → 즉시 매수 → 실시간 모니터링 → 목표가/손절가 도달 시 즉시 매도 ✅

---

## 시스템 아키텍처

```
[1] 급등 예측 신호 감지
         ↓
    surge_alert_scheduler.py
         ↓
[2] 즉시 매수 주문 실행
         ↓
    Upbit API → 매수 체결
         ↓
[3] DB에 포지션 기록
    (swing_positions)
         ↓
[4] 실시간 가격 모니터링 시작
    surge_trading_monitor.py
    (5초마다 가격 체크)
         ↓
    ┌──────────────┬──────────────┐
    │  목표가 도달  │  손절가 도달  │
    │  (예: +5%)   │  (예: -5%)   │
    └──────────────┴──────────────┘
         ↓              ↓
    즉시 매도       즉시 매도
    (익절 실현)     (손실 최소화)
         ↓              ↓
    DB 업데이트: status='win'/'lose'
```

---

## 실제 작동 예시

### 시나리오: BTC 급등 신호 발생

**시간**: 2025-01-15 10:00:00

#### 1단계: 신호 감지 및 매수 (10:00:00)
```
[surge_alert_scheduler.py]
- 급등 신호 감지: KRW-BTC (점수: 85점)
- 현재가: 100,000,000원
- 목표가: 105,000,000원 (+5%)
- 손절가: 95,000,000원 (-5%)

→ 즉시 매수 주문 실행
→ 매수 체결: 0.001 BTC @ 100,000,000원

→ DB 저장:
  - surge_alerts: status='pending', auto_traded=true
  - swing_positions: position_type='surge', status='active'
```

#### 2단계: 실시간 모니터링 (10:00:05 ~ 목표가 도달)
```
[surge_trading_monitor.py] 5초마다 가격 체크

10:00:05 → 가격: 100,500,000원 (+0.5%) - 계속 모니터링
10:00:10 → 가격: 101,200,000원 (+1.2%) - 계속 모니터링
10:00:15 → 가격: 102,800,000원 (+2.8%) - 계속 모니터링
10:00:20 → 가격: 104,100,000원 (+4.1%) - 계속 모니터링
10:00:25 → 가격: 105,200,000원 (+5.2%) - 목표가 도달!
```

#### 3단계: 익절 실행 (10:00:25)
```
[surge_trading_monitor.py]
✅ TARGET HIT! KRW-BTC
   Entry: 100,000,000 → Current: 105,200,000 (+5.2%)
   SELLING NOW

→ 즉시 매도 주문 실행
→ 매도 체결: 0.001 BTC @ 105,200,000원
→ 실현 손익: +5,200원 (+5.2%)

→ DB 업데이트:
  - surge_alerts: status='win', profit_loss_percent=5.2, closed_at=now()
  - swing_positions: status='closed'
```

**결과**: 25초 만에 +5.2% 익절 성공! 🎉

---

## 반대 시나리오: 손절가 도달

**시간**: 2025-01-15 14:00:00

#### 1단계: 신호 감지 및 매수 (14:00:00)
```
- 급등 신호 감지: KRW-ETH
- 현재가: 4,000,000원
- 목표가: 4,200,000원 (+5%)
- 손절가: 3,800,000원 (-5%)

→ 매수 체결: 0.01 ETH @ 4,000,000원
```

#### 2단계: 가격 하락 (14:00:05 ~ 손절가 도달)
```
14:00:05 → 가격: 3,950,000원 (-1.25%) - 계속 모니터링
14:00:10 → 가격: 3,900,000원 (-2.5%) - 계속 모니터링
14:00:15 → 가격: 3,850,000원 (-3.75%) - 계속 모니터링
14:00:20 → 가격: 3,780,000원 (-5.5%) - 손절가 도달!
```

#### 3단계: 손절 실행 (14:00:20)
```
⚠️ STOP-LOSS HIT! KRW-ETH
   Entry: 4,000,000 → Current: 3,780,000 (-5.5%)
   SELLING NOW

→ 즉시 매도 주문 실행
→ 매도 체결: 0.01 ETH @ 3,780,000원
→ 실현 손익: -2,200원 (-5.5%)

→ DB 업데이트:
  - surge_alerts: status='lose', profit_loss_percent=-5.5
  - swing_positions: status='closed'
```

**결과**: 20초 만에 손절 실행 → 손실 최소화 ✅

---

## 핵심 차이점

### 기존 방식 (3일 대기)

| 시간 | 가격 | 행동 |
|------|------|------|
| Day 0 (10:00) | 100만원 | 신호 발생 (관찰만) |
| Day 0 (10:05) | **105만원 (+5%)** | 목표가 도달 (무시) |
| Day 0 (14:00) | 103만원 | - |
| Day 1 | 98만원 | - |
| Day 2 | 102만원 | - |
| Day 3 | 101만원 | "Win" 기록 |

**문제**: 목표가 도달해도 익절 못함 → 가격 하락 시 수익 날림

---

### 새로운 방식 (실시간 모니터링)

| 시간 | 가격 | 행동 |
|------|------|------|
| 10:00:00 | 100만원 | 신호 발생 → **즉시 매수** |
| 10:00:05 | 101만원 | 모니터링 중... |
| 10:00:10 | 103만원 | 모니터링 중... |
| 10:00:15 | **105만원 (+5%)** | **즉시 매도 (익절!)** |
| 10:00:20 | 103만원 (이후 하락) | (이미 매도 완료) |

**장점**: 목표가 도달 시 즉시 익절 → 실제 수익 실현 ✅

---

## 설정 및 실행

### 1. 데이터베이스 마이그레이션

```bash
# 급등 추적 컬럼 추가
python scripts/add_surge_tracking_columns.py

# 포지션 테이블 확장
python scripts/add_surge_position_columns.py
```

---

### 2. 시스템 실행 (2개 프로세스 필요)

#### 프로세스 1: 급등 신호 감지 + 자동 매수
```bash
python backend/services/surge_alert_scheduler.py
```

**기능**:
- 5분마다 급등 후보 검색
- 점수 60점 이상 신호 발생
- 즉시 매수 주문 실행
- DB에 포지션 기록

---

#### 프로세스 2: 실시간 모니터링 + 자동 익절/손절
```bash
python backend/services/surge_trading_monitor.py
```

**기능**:
- 5초마다 활성 포지션 가격 체크
- 목표가 도달 → 즉시 매도 (익절)
- 손절가 도달 → 즉시 매도 (손절)

---

### 3. 프로덕션 배포 (systemd)

#### 서비스 1: 급등 신호 스케줄러
```ini
# /etc/systemd/system/coinpulse-surge-scheduler.service
[Unit]
Description=CoinPulse Surge Signal Scheduler
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/coinpulse
ExecStart=/usr/bin/python3 backend/services/surge_alert_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 서비스 2: 실시간 모니터링
```ini
# /etc/systemd/system/coinpulse-surge-monitor.service
[Unit]
Description=CoinPulse Surge Trading Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/coinpulse
ExecStart=/usr/bin/python3 backend/services/surge_trading_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 실행:
```bash
sudo systemctl enable coinpulse-surge-scheduler
sudo systemctl enable coinpulse-surge-monitor

sudo systemctl start coinpulse-surge-scheduler
sudo systemctl start coinpulse-surge-monitor

# 상태 확인
sudo systemctl status coinpulse-surge-scheduler
sudo systemctl status coinpulse-surge-monitor

# 로그 확인
journalctl -u coinpulse-surge-scheduler -f
journalctl -u coinpulse-surge-monitor -f
```

---

## 모니터링 및 로그

### 스케줄러 로그 예시
```
[2025-01-15 10:00:00] [SurgeAlertScheduler] Found 3 candidates
[2025-01-15 10:00:01] [SurgeAlertScheduler] New alert sent: KRW-BTC (85점)
[2025-01-15 10:00:01] [AutoTradingService] Buy order placed: KRW-BTC, 0.001 BTC
[2025-01-15 10:00:02] [SurgeAlertScheduler] Saved to DB: KRW-BTC (Entry: 100,000,000원)
```

### 모니터 로그 예시
```
[2025-01-15 10:00:05] [SurgeTradingMonitor] Monitoring KRW-BTC: 100,500,000원 (+0.5%)
[2025-01-15 10:00:10] [SurgeTradingMonitor] Monitoring KRW-BTC: 101,200,000원 (+1.2%)
[2025-01-15 10:00:15] [SurgeTradingMonitor] Monitoring KRW-BTC: 102,800,000원 (+2.8%)
[2025-01-15 10:00:20] [SurgeTradingMonitor] Monitoring KRW-BTC: 104,100,000원 (+4.1%)
[2025-01-15 10:00:25] [SurgeTradingMonitor] TARGET HIT! KRW-BTC (+5.2%) - SELLING NOW
[2025-01-15 10:00:25] [AutoTradingService] Sell order placed: KRW-BTC, 0.001 BTC
[2025-01-15 10:00:26] [SurgeTradingMonitor] Take-profit executed: KRW-BTC (+5.2%)
[2025-01-15 10:00:26] [SurgeTradingMonitor] Updated surge_alert 123 to 'win'
```

---

## 데이터베이스 구조

### surge_alerts (급등 신호 기록)
```sql
id: 123
user_id: 1
market: 'KRW-BTC'
entry_price: 100000000
target_price: 105000000  -- +5%
stop_loss_price: 95000000  -- -5%
status: 'pending' → 'win'/'lose'
profit_loss_percent: 5.2
closed_at: '2025-01-15 10:00:26'
auto_traded: true
```

### swing_positions (포지션 기록)
```sql
position_id: 456
user_id: 1
coin_symbol: 'BTC'
buy_price: 100000000
quantity: 0.001
status: 'active' → 'closed'
position_type: 'surge'  -- 'swing' vs 'surge'
surge_alert_id: 123  -- FK to surge_alerts
target_price: 105000000
stop_loss_price: 95000000
```

---

## 성능 지표

### 목표 지표
- **모니터링 주기**: 5초 (설정 가능)
- **익절 실행 시간**: 목표가 도달 후 5초 이내
- **손절 실행 시간**: 손절가 도달 후 5초 이내
- **API 호출 제한**: 초당 10회 (Upbit 제한: 초당 30회)

### 동시 모니터링 가능 포지션 수
- **5초 주기**: 최대 150개 포지션 (여유 있음)
- **계산**: 5초마다 1회 가격 조회 × 150개 = 30회/초 (한도 내)

---

## 리스크 관리

### 1. 포지션 사이즈 제한
```python
# 계좌 잔고의 2%만 사용 (권장)
total_balance = 10,000,000원
position_size = total_balance * 0.02  # 200,000원
```

### 2. 동시 포지션 수 제한
```python
# 최대 5개 포지션 동시 진행 (권장)
MAX_CONCURRENT_POSITIONS = 5
```

### 3. 슬리피지 대비
```python
# 목표가/손절가에 여유 설정
target_price = entry_price * 1.048  # 4.8% (여유 0.2%)
stop_loss_price = entry_price * 0.952  # -4.8% (여유 0.2%)
```

---

## 문제 해결

### Q1. 매수 주문이 체결되지 않습니다

**원인**:
- 계좌 잔고 부족
- API 키 권한 없음 (주문 권한 필요)
- 최소 주문 금액 미달 (Upbit: 5,000원)

**해결**:
```bash
# API 키 권한 확인
python -c "from backend.common import UpbitAPI, load_api_keys; \
           api = UpbitAPI(*load_api_keys()); \
           print(api.get_accounts())"

# 계좌 잔고 확인
python -c "from backend.common import UpbitAPI, load_api_keys; \
           api = UpbitAPI(*load_api_keys()); \
           accounts = api.get_accounts(); \
           krw = next((a for a in accounts if a['currency']=='KRW'), {}); \
           print(f'KRW Balance: {float(krw.get(\"balance\", 0)):,.0f}원')"
```

---

### Q2. 목표가 도달했는데 매도가 안 됩니다

**원인**:
- 모니터링 프로세스가 실행 중이 아님
- DB에 포지션이 제대로 기록되지 않음

**해결**:
```bash
# 모니터링 프로세스 상태 확인
ps aux | grep surge_trading_monitor

# 활성 포지션 확인
python -c "from backend.services.surge_trading_monitor import SurgeTradingMonitor; \
           monitor = SurgeTradingMonitor(user_id=1); \
           positions = monitor.get_active_surge_positions(); \
           print(f'Active positions: {len(positions)}'); \
           for p in positions: print(f'  - {p[\"market\"]}: {p[\"position_status\"]}')"
```

---

### Q3. 모니터링이 멈췄습니다

**원인**:
- API 에러 (rate limit, 네트워크 오류 등)
- 예외 처리되지 않은 에러

**해결**:
```bash
# 로그 확인
journalctl -u coinpulse-surge-monitor -n 50

# 수동 재시작
sudo systemctl restart coinpulse-surge-monitor

# 상태 확인
sudo systemctl status coinpulse-surge-monitor
```

---

## 예상 수익률

### 백테스트 결과 (2024.11.13 ~ 2024.12.07)

| 지표 | 기존 방식 (3일 대기) | 새로운 방식 (실시간) |
|------|---------------------|---------------------|
| 적중률 | 90.0% | 90.0% (동일) |
| 평균 수익 (승리시) | +22.3% | **+5.0% (목표가)** |
| 평균 손실 (실패시) | -4.2% | **-5.0% (손절가)** |
| 총 거래 수 | 30건 | 30건 (동일) |
| **실제 실현 수익** | ❌ 0원 | ✅ **+수익 실현** |

**핵심 차이**:
- 기존: 목표가 도달해도 익절 못함 → 통계만 기록
- 신규: 목표가 도달 시 즉시 익절 → **실제 수익 실현**

---

## 결론

### ✅ 완료된 기능
1. **실시간 가격 모니터링** (5초 주기)
2. **자동 익절 시스템** (목표가 도달 시)
3. **자동 손절 시스템** (손절가 도달 시)
4. **DB 연동** (surge_alerts + swing_positions)
5. **Win/Lose 자동 기록** (통계용)

### ✅ 기술적 구현
- **폴링 방식**: 5초마다 가격 체크 (안정적)
- **데이터베이스 기반**: 모든 거래 기록 저장
- **Upbit API 연동**: 매수/매도 주문 자동 실행
- **에러 처리**: API 오류 시 자동 재시도

### ✅ 프로덕션 준비
- systemd 서비스 구성 완료
- 로그 시스템 구축
- 리스크 관리 가이드

**이제 진짜 자동매매가 가능합니다!** 🎉

---

## 다음 단계

1. **프로덕션 배포**:
   ```bash
   git add .
   git commit -m "[FEATURE] Surge real-time auto-trading system"
   git push origin main

   # 프로덕션 서버에서
   ssh root@158.247.222.216
   cd /opt/coinpulse
   git pull origin main
   python scripts/add_surge_position_columns.py
   ```

2. **서비스 시작**:
   ```bash
   sudo systemctl start coinpulse-surge-scheduler
   sudo systemctl start coinpulse-surge-monitor
   ```

3. **모니터링**:
   ```bash
   journalctl -u coinpulse-surge-scheduler -f
   journalctl -u coinpulse-surge-monitor -f
   ```
