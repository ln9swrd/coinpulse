# 다음 개발사항 정리 (2025-12-13)

## 📊 현재 시스템 현황

### ✅ 완료된 시스템 (프로덕션 배포 완료)

#### 1. 관리 시스템 (Admin Systems)
- **베타 테스터 관리**: `backend/routes/admin.py`
- **사용자 혜택 관리**: `backend/routes/benefits_admin.py`
- **플랜 설정 관리**: `backend/routes/plan_admin.py`
- **정지 시스템**: `backend/routes/suspension_admin.py`
- **사용자/결제 요청 관리**: `backend/routes/users_admin.py`
  - 사용자 목록 조회 (구독 정보 포함)
  - 구독 수동 수정
  - 결제 요청 생성/조회/승인
  - 결제 코드 생성 (CP + 6자리)

#### 2. 결제 시스템 (Payment System)
- **토스페이먼츠 빌링**: `backend/routes/payments.py`
  - 빌링키 발급 (성공/실패 콜백)
  - 정기결제 실행
  - 결제 상태 확인
- **구독 결제 페이지**: `frontend/subscribe.html`
  - 월간/연간 플랜 선택
  - 토스페이먼츠 SDK 통합
  - 동적 플랜 로딩
- **결제 완료 페이지**: `frontend/payment-complete.html`
- **환불 정책 페이지**: `frontend/refund.html`

#### 3. 자동매매 시스템 (Trading Systems)

**A. 급등 예측 시스템** (`backend/services/surge_predictor.py`)
- 5가지 기술적 분석 지표:
  - 거래량 분석 (Volume: 20점)
  - RSI 과매도 회복 (RSI: 25점)
  - 지지선 근접도 (Support: 20점)
  - 상승 추세 확인 (Trend: 20점)
  - 가격 모멘텀 (Momentum: 15점)
- 0-100점 스코어링 시스템
- 자동 후보 스캔 기능
- 추천 등급: strong_buy, buy, hold, pass

**B. 스윙 트레이딩 엔진** (`backend/services/swing_trading_engine.py`)
- 3일 보유 전략
- 급등 예측 통합 (SurgePredictor)
- 포지션 관리 (PositionTracker)
- 테스트 모드/실전 모드
- 자동 손절/익절
- 긴급 중지 시스템

**C. 포지션 추적** (`backend/services/position_tracker.py`)
- JSON 파일 기반 포지션 관리
- 수익률 실시간 계산
- 보유 기간 추적
- 손절/익절 조건 체크
- 거래 이력 저장

**D. 강화된 자동거래 엔진** (`backend/services/enhanced_auto_trading_engine.py`)
- **데이터베이스 기반** (vs position_tracker.py의 JSON)
- **Multi-user 지원** (user_id 기반)
- 실시간 Upbit API 주문 실행
- 리스크 관리 (최대 포지션, 예산 관리)
- 종합 로깅 (SwingTradingLog 테이블)

---

## 🚧 미완성 작업 (Priority 순서)

### Priority 1: 결제 시스템 완성 ⚠️ HIGH

#### 1.1 빌링키 DB 저장 기능 구현
**파일**: `backend/routes/payments.py:46-47`
```python
# TODO: DB에 빌링키 저장
# save_billing_key(customer_key, billing_key, billing_data)
```

**해야 할 작업**:
1. `billing_keys` 테이블 생성 (마이그레이션)
   ```sql
   CREATE TABLE billing_keys (
       id SERIAL PRIMARY KEY,
       user_id INTEGER REFERENCES users(id),
       customer_key VARCHAR(100) UNIQUE,
       billing_key VARCHAR(100),
       card_info JSONB,
       status VARCHAR(20) DEFAULT 'active',
       created_at TIMESTAMP DEFAULT NOW()
   );
   ```

2. `save_billing_key()` 함수 구현
   ```python
   def save_billing_key(user_id, customer_key, billing_key, billing_data):
       # DB에 빌링키 저장 로직
   ```

3. `/billing/success` 콜백 수정
   - 현재: billing_key를 화면에만 표시
   - 수정 후: user_id와 함께 DB에 저장

**예상 작업 시간**: 2-3시간

---

#### 1.2 자동 정기결제 스케줄러 구현
**현재 상태**: 빌링키 발급만 완료, 정기결제 자동 실행 없음

**해야 할 작업**:
1. 구독 만료일 체크 스케줄러 (매일 00:00 실행)
2. 만료 3일 전 결제 시도
3. 결제 실패 시 재시도 로직 (3회)
4. 결제 실패 알림 (이메일/SMS)
5. 구독 상태 자동 업데이트

**파일 생성**: `backend/services/subscription_scheduler.py`

**예상 작업 시간**: 4-6시간

---

### Priority 2: 자동매매 UI 구현 🎯 MEDIUM

#### 2.1 스윙 트레이딩 대시보드
**현재 상태**: 백엔드 로직 완성, UI 없음

**필요한 페이지**: `frontend/swing_trading.html`

**UI 기능**:
1. **실시간 포지션 현황**
   - 보유 코인 목록
   - 매수가/현재가/수익률
   - 보유 기간

2. **급등 후보 스캔 결과**
   - Top 10 코인 표시
   - 각 코인의 스코어 (0-100)
   - 5가지 지표 시각화 (거래량, RSI, 지지선, 추세, 모멘텀)

3. **자동매매 설정**
   - ON/OFF 토글
   - 테스트 모드/실전 모드 전환
   - 예산 설정
   - 최대 포지션 수 설정

4. **거래 이력**
   - 거래 내역 테이블
   - 수익률 차트
   - 승률 통계

**API 엔드포인트 추가 필요**:
```python
# backend/routes/swing_trading_routes.py
@swing_trading_bp.route('/status', methods=['GET'])
def get_status():
    """현재 자동매매 상태 조회"""

@swing_trading_bp.route('/candidates', methods=['GET'])
def get_surge_candidates():
    """급등 후보 코인 조회"""

@swing_trading_bp.route('/positions', methods=['GET'])
def get_positions():
    """보유 포지션 조회"""

@swing_trading_bp.route('/settings', methods=['PUT'])
def update_settings():
    """자동매매 설정 변경"""
```

**예상 작업 시간**: 8-10시간

---

#### 2.2 급등 예측 실시간 모니터링 페이지
**파일 생성**: `frontend/surge_monitor.html`

**기능**:
1. 전체 코인 스코어 실시간 업데이트 (30초마다)
2. 스코어 60점 이상 코인 자동 알림
3. 각 코인 클릭 시 상세 분석 표시
4. 차트 연동 (trading_chart.html과 통합)

**예상 작업 시간**: 6-8시간

---

### Priority 3: 시스템 통합 및 정리 🔧 MEDIUM

#### 3.1 자동매매 엔진 통합 결정
**문제**: 중복된 두 시스템 존재

**시스템 A**: `position_tracker.py` + `swing_trading_engine.py`
- JSON 파일 기반
- 단일 사용자용
- 파일 I/O 의존

**시스템 B**: `enhanced_auto_trading_engine.py` + `db_position_tracker.py`
- 데이터베이스 기반
- Multi-user 지원
- 확장성 우수

**권장 방안**:
1. **시스템 B를 주력으로 선택** (Multi-user 지원)
2. 시스템 A를 백업/레거시로 보관
3. `swing_trading_engine.py`를 `enhanced_auto_trading_engine.py`로 마이그레이션
4. UI는 enhanced 버전 기준으로 개발

**예상 작업 시간**: 3-4시간 (마이그레이션 + 테스트)

---

#### 3.2 사용자 관리 UI 개선
**현재 파일**: `frontend/admin.html` (존재 여부 확인 필요)

**필요한 기능**:
1. 사용자 목록 테이블 (구독 정보 포함)
2. 구독 수동 변경 UI
3. 결제 요청 관리 UI
   - Pending 요청 목록
   - 승인/거부 버튼
   - 결제 코드 자동 생성

**백엔드 API**: 이미 완성됨 (`users_admin.py`)

**예상 작업 시간**: 4-6시간

---

### Priority 4: 프로덕션 안정화 🛡️ LOW

#### 4.1 에러 모니터링 강화
1. Sentry 또는 LogRocket 통합
2. 에러 발생 시 Slack/Discord 알림
3. 일일 시스템 상태 리포트 자동 생성

**예상 작업 시간**: 2-3시간

---

#### 4.2 데이터베이스 백업 자동화
1. PostgreSQL `pg_dump` 자동화 스크립트
2. 매일 00:00 KST 백업 실행
3. S3 또는 외부 스토리지 업로드
4. 7일 이상 백업 자동 삭제

**예상 작업 시간**: 2-3시간

---

#### 4.3 성능 최적화
1. API 응답 시간 프로파일링
2. 느린 쿼리 최적화 (EXPLAIN ANALYZE)
3. Redis 캐싱 도입 (가격 정보, 차트 데이터)
4. Connection pooling 튜닝

**예상 작업 시간**: 4-6시간

---

## 📅 제안 개발 로드맵 (2주 기준)

### Week 1 (Dec 13-19)
- [ ] **Day 1-2**: Priority 1.1 - 빌링키 DB 저장 구현
- [ ] **Day 3-4**: Priority 1.2 - 정기결제 스케줄러 구현
- [ ] **Day 5**: Priority 3.1 - 자동매매 엔진 통합 결정 및 마이그레이션

### Week 2 (Dec 20-26)
- [ ] **Day 1-3**: Priority 2.1 - 스윙 트레이딩 대시보드 UI 개발
- [ ] **Day 4-5**: Priority 2.2 - 급등 예측 모니터링 페이지 개발
- [ ] **Day 6-7**: Priority 3.2 - 사용자 관리 UI 개선

### Optional (Backlog)
- [ ] Priority 4.1 - 에러 모니터링 강화
- [ ] Priority 4.2 - 데이터베이스 백업 자동화
- [ ] Priority 4.3 - 성능 최적화

---

## 🎯 핵심 우선순위 (즉시 시작 가능)

1. **빌링키 DB 저장** (payments.py:46-47) - 2-3시간
2. **자동매매 엔진 통합** (A vs B 결정) - 3-4시간
3. **스윙 트레이딩 UI** (급등 예측 + 포지션 관리) - 8-10시간

**총 예상 시간**: 13-17시간 (약 2-3일)

---

## 📝 참고사항

### 동기화 완료 파일
- ✅ app.py (메인 Flask 앱)
- ✅ backend/routes/users_admin.py (신규)
- ✅ backend/routes/payments.py (신규)
- ✅ backend/services/surge_predictor.py (신규)
- ✅ backend/services/swing_trading_engine.py (신규)
- ✅ backend/services/position_tracker.py (신규)
- ✅ backend/services/enhanced_auto_trading_engine.py (신규)
- ✅ frontend/subscribe.html (신규)
- ✅ frontend/payment-complete.html (신규)
- ✅ frontend/refund.html (신규)

### 프로덕션 환경
- **서버**: Vultr (158.247.222.216)
- **도메인**: coinpulse.sinsi.ai
- **데이터베이스**: PostgreSQL (23 테이블)
- **웹서버**: Nginx + SSL

### 로컬 환경
- **경로**: D:\Claude\Projects\Active\coinpulse
- **데이터베이스**: SQLite (개발) + PostgreSQL (테스트)
- **서버**: Flask development server
