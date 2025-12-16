# 🗺️ CoinPulse 전체 네비게이션 가이드

**작성일**: 2025-12-16
**목적**: 실제 접속 및 기능 검증

---

## 📍 기본 접속 정보

### 로컬 개발 환경
```
Base URL: http://localhost:8080
API Base: http://localhost:8080/api
```

### 프로덕션 환경
```
Base URL: https://coinpulse.sinsi.ai
API Base: https://coinpulse.sinsi.ai/api
```

---

## 🌐 프론트엔드 페이지 (총 18개)

### 1️⃣ 공개 페이지 (로그인 불필요)

| 페이지 | URL | 설명 | 주요 기능 |
|--------|-----|------|----------|
| **랜딩 페이지** | `/` 또는 `/index.html` | 서비스 소개 메인 | 기능 소개, 요금제, 회원가입 |
| **로그인** | `/login.html` | 사용자 로그인 | 이메일/비밀번호 로그인 |
| **회원가입** | `/signup.html` | 신규 회원가입 | 이메일 인증, 약관 동의 |
| **구독 페이지** | `/subscribe.html` | 요금제 선택 및 결제 | Free/Premium/Enterprise 선택 |
| **결제 완료** | `/payment-complete.html` | 결제 성공 화면 | 구독 활성화 확인 |
| **결제 실패** | `/payment-error.html` | 결제 실패 화면 | 에러 메시지 표시 |
| **결제 성공** | `/payment-success.html` | Toss Payments 콜백 | 빌링키 발급 성공 |

### 2️⃣ 사용자 페이지 (로그인 필요)

| 페이지 | URL | 설명 | 주요 기능 |
|--------|-----|------|----------|
| **대시보드** | `/dashboard.html` | 메인 대시보드 | 전체 기능 내비게이션 |
| **트레이딩 차트** | `/trading_chart.html` | TradingView 차트 | 기술적 분석, 그리기 도구 |
| **스윙 트레이딩** | `/swing_trading.html` | 스윙 트레이딩 관리 | 포지션 조회, 통계, 설정 |
| **실시간 대시보드** | `/realtime_dashboard.html` | 실시간 모니터링 | WebSocket 가격 업데이트 |
| **급등 모니터링** | `/surge_monitoring.html` | 급등 예측 후보 | AI 예측 스코어 표시 |
| **백테스트 결과** | `/backtest_results.html` | 백테스트 결과 조회 | 과거 성과 분석 |
| **환불 신청** | `/refund.html` | 환불 요청 페이지 | 환불 사유 입력 |
| **결제 페이지** | `/checkout.html` | 결제 진행 | Toss Payments 연동 |

### 3️⃣ 설정 페이지

| 페이지 | URL | 설명 | 주요 기능 |
|--------|-----|------|----------|
| **정책 관리** | `/policy_manager.html` | 트레이딩 정책 설정 | 매매 전략 설정 |
| **스윙 설정** | `/swing_trading_settings.html` | 스윙 트레이딩 설정 | 리스크 관리, 목표 수익률 |

### 4️⃣ 관리자 페이지 (Admin 전용)

| 페이지 | URL | 설명 | 주요 기능 |
|--------|-----|------|----------|
| **관리자 대시보드** | `/admin.html` | 통합 관리자 콘솔 | 사용자/구독/통계 관리 |

---

## 🔌 API 엔드포인트 (총 50+ 개)

### 1️⃣ 인증 API (`/api/auth`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| POST | `/api/auth/register` | 회원가입 | Public |
| POST | `/api/auth/login` | 로그인 | Public |
| POST | `/api/auth/logout` | 로그아웃 | User |
| POST | `/api/auth/refresh` | 토큰 갱신 | User |
| GET | `/api/auth/me` | 현재 사용자 정보 | User |

**테스트 예시**:
```bash
# 회원가입
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "username": "testuser"
  }'

# 로그인
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

---

### 2️⃣ 사용자 API (`/api/user`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/user/profile` | 프로필 조회 | User |
| PUT | `/api/user/profile` | 프로필 수정 | User |
| GET | `/api/user/plan` | 현재 구독 플랜 | User |
| GET | `/api/user/api-keys` | Upbit API 키 조회 | User |
| POST | `/api/user/api-keys` | Upbit API 키 저장 | User |

**테스트 예시**:
```bash
# 프로필 조회 (JWT 토큰 필요)
curl -X GET http://localhost:8080/api/user/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 3️⃣ 포트폴리오 API (`/api/holdings`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/holdings` | 보유 자산 조회 | User |
| GET | `/api/orders` | 주문 내역 조회 | User |
| GET | `/api/balance` | 잔고 조회 | User |

---

### 4️⃣ 자동 거래 API (`/api/auto-trading`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/auto-trading/status` | 자동거래 상태 (인증 필요) | User |
| GET | `/api/auto-trading/status/<user_id>` | 자동거래 상태 (레거시) | User |
| GET | `/api/auto-trading/config/<user_id>` | 설정 조회 | User |
| POST | `/api/auto-trading/config/<user_id>` | 설정 저장 | User |
| POST | `/api/auto-trading/start/<user_id>` | 자동거래 시작 | User |
| POST | `/api/auto-trading/stop/<user_id>` | 자동거래 중지 | User |
| POST | `/api/auto-trading/run-cycle/<user_id>` | 수동 실행 | User |
| GET | `/api/auto-trading/logs/<user_id>` | 로그 조회 | User |
| GET | `/api/auto-trading/positions/<user_id>` | 포지션 조회 | User |
| GET | `/api/auto-trading/history/<user_id>` | 거래 내역 | User |
| GET | `/api/auto-trading/stats/<user_id>` | 통계 조회 | User |
| POST | `/api/auto-trading/toggle/<user_id>` | 자동거래 토글 | User |

**테스트 예시**:
```bash
# 자동거래 상태 조회
curl -X GET http://localhost:8080/api/auto-trading/status/1

# 자동거래 시작
curl -X POST http://localhost:8080/api/auto-trading/start/1
```

---

### 5️⃣ 급등 예측 API (`/api/surge`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/surge/candidates` | 급등 후보 조회 | User |
| GET | `/api/surge/history` | 예측 기록 조회 | User |
| GET | `/api/surge/backtest` | 백테스트 결과 | User |

**테스트 예시**:
```bash
# 급등 후보 조회
curl -X GET "http://localhost:8080/api/surge/candidates?min_score=60"
```

---

### 6️⃣ 구독 API (`/api/subscription`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/subscription/plans` | 요금제 목록 | Public |
| GET | `/api/subscription/current` | 현재 구독 정보 | User |
| POST | `/api/subscription/subscribe` | 구독 신청 | User |
| POST | `/api/subscription/upgrade` | 플랜 업그레이드 | User |

---

### 7️⃣ 결제 API (`/api/payment`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/payment/status` | 결제 시스템 상태 | Public |
| GET | `/api/payment/billing/success` | 빌링키 발급 성공 콜백 | Public |
| GET | `/api/payment/billing/fail` | 빌링키 발급 실패 콜백 | Public |
| POST | `/api/payment/billing/execute` | 정기결제 실행 | User |
| GET | `/api/payment/billing/keys/<user_id>` | 빌링키 조회 | User |
| POST | `/api/payment/billing/keys/<id>/deactivate` | 빌링키 비활성화 | User |
| POST | `/api/payment/refund` | 환불 처리 ⭐ NEW | Admin |
| GET | `/api/payment/refund/status/<payment_key>` | 환불 상태 조회 ⭐ NEW | User |
| POST | `/api/payment/subscription/cancel/<user_id>` | 구독 취소 ⭐ NEW | User |

**테스트 예시**:
```bash
# 환불 처리 (관리자)
curl -X POST http://localhost:8080/api/payment/refund \
  -H "Content-Type: application/json" \
  -d '{
    "paymentKey": "payment_key_here",
    "cancelReason": "고객 요청",
    "cancelAmount": 10000
  }'

# 구독 취소
curl -X POST http://localhost:8080/api/payment/subscription/cancel/1 \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "서비스 불만족",
    "refund": false
  }'
```

---

### 8️⃣ 통계 API (`/api/stats`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/stats/overview` | 전체 통계 | Admin |
| GET | `/api/stats/users` | 사용자 통계 | Admin |
| GET | `/api/stats/revenue` | 수익 통계 | Admin |
| GET | `/api/stats/trading` | 거래 통계 | Admin |

---

### 9️⃣ 관리자 API (`/api/admin`)

#### A. 베타 테스터 관리 (`/api/admin/beta-testers`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/beta-testers` | 베타 테스터 목록 |
| POST | `/api/admin/beta-testers` | 베타 테스터 추가 |
| DELETE | `/api/admin/beta-testers/<id>` | 베타 테스터 삭제 |

#### B. 사용자 관리 (`/api/admin/users`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/users` | 전체 사용자 목록 |
| GET | `/api/admin/users/<id>` | 사용자 상세 정보 |
| PUT | `/api/admin/users/<id>` | 사용자 정보 수정 |
| DELETE | `/api/admin/users/<id>` | 사용자 삭제 |

#### C. 혜택 관리 (`/api/admin/benefits`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/benefits` | 혜택 목록 |
| POST | `/api/admin/benefits` | 혜택 추가 |
| PUT | `/api/admin/benefits/<id>` | 혜택 수정 |
| DELETE | `/api/admin/benefits/<id>` | 혜택 삭제 |

#### D. 정지 관리 (`/api/admin/suspensions`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/suspensions` | 정지 목록 |
| POST | `/api/admin/suspensions` | 사용자 정지 |
| DELETE | `/api/admin/suspensions/<id>` | 정지 해제 |

#### E. 플랜 관리 (`/api/admin/plans`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/plans` | 플랜 목록 |
| POST | `/api/admin/plans` | 플랜 추가 |
| PUT | `/api/admin/plans/<id>` | 플랜 수정 |
| DELETE | `/api/admin/plans/<id>` | 플랜 삭제 |

#### F. 스케줄러 관리 (`/api/admin/scheduler`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/scheduler/status` | 스케줄러 상태 |
| POST | `/api/admin/scheduler/trigger` | 수동 실행 |
| POST | `/api/admin/scheduler/start` | 스케줄러 시작 |
| POST | `/api/admin/scheduler/stop` | 스케줄러 중지 |

---

### 🔟 헬스 체크 API (`/api/health`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/health` | 기본 헬스 체크 | Public |
| GET | `/api/health/detailed` | 상세 헬스 체크 | Public |
| GET | `/api/health/db` | 데이터베이스 헬스 체크 | Public |
| GET | `/api/health/ready` | Readiness probe | Public |
| GET | `/api/health/live` | Liveness probe | Public |

**테스트 예시**:
```bash
# 기본 헬스 체크
curl http://localhost:8080/health

# 상세 헬스 체크
curl http://localhost:8080/api/health/detailed
```

---

## 🧪 검증 시나리오

### 시나리오 1: 일반 사용자 흐름

1. **회원가입**:
   ```
   http://localhost:8080/signup.html
   → 이메일, 비밀번호 입력
   → 회원가입 완료
   ```

2. **로그인**:
   ```
   http://localhost:8080/login.html
   → 이메일, 비밀번호 입력
   → JWT 토큰 발급
   ```

3. **대시보드 접속**:
   ```
   http://localhost:8080/dashboard.html
   → 전체 기능 확인
   ```

4. **트레이딩 차트**:
   ```
   http://localhost:8080/trading_chart.html
   → 코인 선택 (BTC, ETH 등)
   → 지표 활성화 (RSI, MACD)
   → 그리기 도구 테스트
   ```

5. **스윙 트레이딩**:
   ```
   http://localhost:8080/swing_trading.html
   → 현재 포지션 확인
   → 급등 후보 확인
   → 자동거래 ON/OFF
   ```

6. **실시간 모니터링**:
   ```
   http://localhost:8080/realtime_dashboard.html
   → WebSocket 연결 확인
   → 실시간 가격 업데이트 확인
   ```

7. **급등 예측**:
   ```
   http://localhost:8080/surge_monitoring.html
   → Top 10 급등 후보 확인
   → AI 예측 스코어 확인
   ```

8. **구독 신청**:
   ```
   http://localhost:8080/subscribe.html
   → 플랜 선택 (Premium/Enterprise)
   → 결제 진행
   → 빌링키 발급
   ```

---

### 시나리오 2: 관리자 흐름

1. **관리자 대시보드**:
   ```
   http://localhost:8080/admin.html
   → 전체 통계 확인
   → 사용자 목록 확인
   ```

2. **베타 테스터 관리**:
   ```
   API: GET /api/admin/beta-testers
   → 베타 테스터 목록 조회

   API: POST /api/admin/beta-testers
   → 새 베타 테스터 추가
   ```

3. **사용자 정지**:
   ```
   API: POST /api/admin/suspensions
   → 사용자 정지 처리
   → 정지 사유 입력
   ```

4. **환불 처리**:
   ```
   API: POST /api/payment/refund
   → 결제 키 입력
   → 환불 사유 입력
   → 환불 처리
   ```

5. **스케줄러 관리**:
   ```
   API: GET /api/admin/scheduler/status
   → 스케줄러 상태 확인

   API: POST /api/admin/scheduler/trigger
   → 수동 실행
   ```

---

## 📊 테스트 체크리스트

### 프론트엔드 테스트

- [ ] **랜딩 페이지** (`/index.html`)
  - [ ] 기능 소개 표시
  - [ ] 요금제 표시
  - [ ] 회원가입 버튼 작동

- [ ] **로그인** (`/login.html`)
  - [ ] 이메일/비밀번호 입력
  - [ ] 로그인 성공 시 JWT 저장
  - [ ] 로그인 실패 시 에러 메시지

- [ ] **대시보드** (`/dashboard.html`)
  - [ ] 사이드바 내비게이션 작동
  - [ ] 모든 링크 클릭 가능
  - [ ] 사용자 정보 표시

- [ ] **트레이딩 차트** (`/trading_chart.html`)
  - [ ] 차트 로딩
  - [ ] 코인 선택 드롭다운
  - [ ] 지표 토글 (RSI, MACD 등)
  - [ ] 그리기 도구 작동

- [ ] **스윙 트레이딩** (`/swing_trading.html`)
  - [ ] 포지션 리스트 표시
  - [ ] 급등 후보 표시
  - [ ] 자동거래 토글
  - [ ] 통계 카드 표시

- [ ] **실시간 대시보드** (`/realtime_dashboard.html`)
  - [ ] WebSocket 연결 상태 표시
  - [ ] 실시간 가격 업데이트
  - [ ] 8개 코인 모니터링

- [ ] **급등 모니터링** (`/surge_monitoring.html`)
  - [ ] Top 10 후보 표시
  - [ ] AI 스코어 표시
  - [ ] 상세 정보 표시

---

### API 테스트

#### 인증 API
- [ ] POST `/api/auth/register` - 회원가입
- [ ] POST `/api/auth/login` - 로그인
- [ ] GET `/api/auth/me` - 현재 사용자 정보

#### 거래 API
- [ ] GET `/api/auto-trading/status/1` - 자동거래 상태
- [ ] POST `/api/auto-trading/start/1` - 자동거래 시작
- [ ] POST `/api/auto-trading/stop/1` - 자동거래 중지

#### 급등 예측 API
- [ ] GET `/api/surge/candidates` - 급등 후보 조회

#### 결제 API
- [ ] POST `/api/payment/refund` - 환불 처리
- [ ] POST `/api/payment/subscription/cancel/1` - 구독 취소

#### 관리자 API
- [ ] GET `/api/admin/users` - 사용자 목록
- [ ] GET `/api/admin/beta-testers` - 베타 테스터 목록
- [ ] POST `/api/admin/scheduler/trigger` - 스케줄러 수동 실행

#### 헬스 체크 API
- [ ] GET `/health` - 기본 헬스 체크
- [ ] GET `/api/health/detailed` - 상세 헬스 체크

---

## 🔑 테스트 계정 (예시)

### 일반 사용자
```
Email: user@coinpulse.com
Password: test1234
User ID: 1
```

### 관리자
```
Email: admin@coinpulse.com
Password: admin1234
User ID: 0 (관리자)
```

---

## 🚀 빠른 시작 명령어

### 서버 시작
```bash
# 통합 서버 (권장)
python app.py

# 포트 확인
netstat -ano | findstr ":8080"
```

### API 테스트
```bash
# 헬스 체크
curl http://localhost:8080/health

# 급등 후보 조회
curl http://localhost:8080/api/surge/candidates

# 자동거래 상태 조회
curl http://localhost:8080/api/auto-trading/status/1
```

---

## 📝 주의사항

1. **JWT 토큰**: 대부분의 API는 JWT 인증 필요
   - 로그인 후 `access_token` 저장
   - 헤더에 `Authorization: Bearer <token>` 포함

2. **CORS**: 브라우저에서 직접 API 호출 시 CORS 설정 확인
   - 로컬: `http://localhost:8080` 허용됨
   - 프로덕션: `https://coinpulse.sinsi.ai` 허용됨

3. **Rate Limiting**: 보안 미들웨어로 인한 제한
   - 일반 API: 60 req/min
   - 인증 API: 5 req/min
   - 거래 API: 10 req/min

4. **Telegram Bot**: 환경 변수 `TELEGRAM_BOT_TOKEN` 설정 필요
   - 설정 안 하면 자동으로 비활성화

5. **환불 API**: 관리자 권한 필요
   - 일반 사용자는 구독 취소만 가능

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-12-16
**작성자**: CoinPulse Team
