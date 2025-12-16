# 🗺️ CoinPulse 네비게이션 시스템 종합 분석

**작성일**: 2025-12-14
**프로덕션 환경**: https://coinpulse.sinsi.ai
**목적**: 완전한 웹서비스 구축을 위한 현황 및 누락 기능 파악

---

## 📋 목차

1. [일반 사용자 네비게이션](#1-일반-사용자-네비게이션)
2. [관리자 네비게이션](#2-관리자-네비게이션)
3. [요금제 시스템](#3-요금제-시스템)
4. [구현 완료 기능](#4-구현-완료-기능)
5. [미구현 기능](#5-미구현-기능)
6. [우선순위 개발 계획](#6-우선순위-개발-계획)

---

## 1. 일반 사용자 네비게이션

### 1.1 공개 페이지 (비로그인)

#### 🏠 랜딩 페이지
- **URL**: `https://coinpulse.sinsi.ai/`
- **파일**: `frontend/index.html`
- **기능**:
  - 서비스 소개
  - 주요 기능 (#features)
  - 요금제 안내 (#pricing)
  - 회사 소개 (#about)
- **CTA**:
  - "시작하기" → `/signup.html`
  - "로그인" → `/login.html`
  - "7일 무료 체험" → `/signup.html`
- **요금제 연동**: ❌ 없음 (공개 페이지)

#### 🔐 회원가입/로그인
- **회원가입**: `/signup.html`
  - API: `POST /api/auth/register`
  - 이메일 인증 시스템 ✅
- **로그인**: `/login.html`
  - API: `POST /api/auth/login`
  - JWT 토큰 기반 인증 ✅
- **비밀번호 재설정**: `/api/auth/request-password-reset`
- **요금제 연동**: ❌ 없음 (기본 FREE 플랜)

#### 📊 급등 예측 공개 페이지 (NEW - MVP 1차)
- **실시간 모니터링**: `/surge_monitoring.html`
  - API: `GET /api/surge-candidates`
  - 30초 자동 새로고침
  - 백테스트 통계 표시 (81.25% 적중률)
  - **요금제 연동**: ❌ 없음 (공개)

- **백테스트 결과**: `/backtest_results.html`
  - API: `GET /api/surge-backtest-results`
  - 16건 거래 상세 내역
  - 주간별 성과 분석
  - **요금제 연동**: ❌ 없음 (투명성 보장)

---

### 1.2 사용자 대시보드 (로그인 필요)

#### 📱 메인 대시보드
- **URL**: `/dashboard.html`
- **파일**: `frontend/dashboard.html`
- **네비게이션 메뉴**:

| 메뉴 | 페이지 ID | API 엔드포인트 | 설명 | 요금제 |
|------|-----------|----------------|------|--------|
| **개요** | `#overview` | `/api/stats/summary` | 포트폴리오 요약, 최근 활동 | ✅ 모든 플랜 |
| **거래** | `#trading` | `/api/holdings` | 실시간 차트, 매수/매도 | ✅ 모든 플랜 |
| **포트폴리오** | `#portfolio` | `/api/account/balance` | 보유 자산, 수익률 분석 | ✅ 모든 플랜 |
| **자동매매** | `#auto-trading` | `/api/auto-trading/*` | 자동매매 설정 및 모니터링 | 🔒 PREMIUM |
| **거래 내역** | `#history` | `/api/orders` | 과거 주문 내역 조회 | ✅ 모든 플랜 |
| **요금제** | `#pricing` | `/api/payment/plans` | 플랜 업그레이드 | ✅ 모든 플랜 |
| **설정** | `#settings` | `/api/auth/profile` | 프로필, API 키 관리 | ✅ 모든 플랜 |

#### 🔗 대시보드 퀵링크
- **차트 전체화면**: `/trading_chart.html`
- **스윙 트레이딩 설정**: `/swing_trading_settings.html`
- **정책 관리**: `/policy_manager.html`

---

### 1.3 전문 거래 페이지

#### 📈 거래 차트 (고급)
- **URL**: `/trading_chart.html`
- **파일**: `frontend/trading_chart.html` (45,973 bytes)
- **주요 기능**:
  - TradingView 스타일 차트
  - 20+ 기술적 지표 (이평선, RSI, MACD, 볼린저밴드 등)
  - 지지/저항선 자동 감지
  - 그리기 도구 (추세선, 피보나치)
  - 다크/라이트 테마
  - 멀티 타임프레임 (1분~1일)
- **API**:
  - `GET /api/upbit/candles/days` - 차트 데이터
  - `GET /api/trading/current-price/<market>` - 현재가
- **요금제 연동**:
  - ✅ FREE: 기본 지표, 7일 데이터
  - 🔒 PREMIUM: 고급 지표, 무제한 데이터

#### 🤖 스윙 트레이딩 설정
- **URL**: `/swing_trading_settings.html`
- **파일**: `frontend/swing_trading_settings.html` (25,448 bytes)
- **주요 기능**:
  - 자동매매 전략 설정
  - 진입/청산 조건 설정
  - 손절/익절 설정
  - 백테스팅
- **API**:
  - `GET /api/auto-trading/config/<user_id>` - 설정 조회
  - `POST /api/auto-trading/config/<user_id>` - 설정 저장
  - `POST /api/auto-trading/start/<user_id>` - 자동매매 시작
  - `POST /api/auto-trading/stop/<user_id>` - 자동매매 중지
- **요금제 연동**: 🔒 **PREMIUM 전용**
  - FREE: 조회만 가능
  - PREMIUM: 3개 동시 전략 실행

#### 📋 정책 관리
- **URL**: `/policy_manager.html`
- **파일**: `frontend/policy_manager.html` (16,368 bytes)
- **주요 기능**:
  - 거래 정책 생성/수정/삭제
  - 정책 템플릿
  - 시뮬레이션
- **API**: 파일 기반 (`trading_policies.json`)
- **요금제 연동**:
  - ✅ FREE: 1개 정책
  - 🔒 PREMIUM: 무제한 정책

---

### 1.4 결제 및 구독

#### 💳 결제 시스템
- **URL**: `/checkout.html`
- **파일**: `frontend/checkout.html` (16,234 bytes)
- **API**:
  - `GET /api/payment/plans` - 요금제 목록
  - `POST /api/payment/checkout` - 결제 시작
  - `POST /api/payment/confirm` - 결제 확인
- **결제 수단**: Toss Payments 연동 ✅
- **결과 페이지**:
  - 성공: `/payment-success.html`
  - 완료: `/payment-complete.html`
  - 실패: `/payment-error.html`

#### 📦 구독 관리
- **URL**: `/subscribe.html`
- **API**:
  - `GET /api/payment/subscription` - 현재 구독 조회
  - `POST /api/payment/subscription/cancel` - 구독 취소
  - `GET /api/payment/transactions` - 결제 내역

#### 💰 환불
- **URL**: `/refund.html`
- **설명**: 환불 정책 안내

---

## 2. 관리자 네비게이션

### 2.1 관리자 대시보드

#### 🔧 Admin Dashboard v2.0
- **URL**: `/admin.html`
- **파일**: `frontend/admin.html` (35,965 bytes)
- **인증**: 관리자 권한 필요
- **주요 섹션**:
  - 사용자 관리
  - 베타 테스터 관리
  - 구독 관리
  - 혜택 관리 (일시 중지/재개)
  - 요금제 설정
  - 통계 및 분석

### 2.2 관리자 API 엔드포인트

#### 👥 사용자 관리 (`/api/admin`)
| 엔드포인트 | 메서드 | 기능 | 상태 |
|------------|--------|------|------|
| `/api/admin/users` | GET | 사용자 목록 조회 | ✅ |
| `/api/admin/users/<user_id>` | GET | 사용자 상세 | ✅ |
| `/api/admin/users/<user_id>` | PUT | 사용자 수정 | ✅ |
| `/api/admin/users/<user_id>` | DELETE | 사용자 삭제 | ✅ |
| `/api/admin/users/<user_id>/suspend` | POST | 계정 정지 | ✅ |
| `/api/admin/users/<user_id>/resume` | POST | 정지 해제 | ✅ |

#### 🧪 베타 테스터 관리 (`/api/admin`)
| 엔드포인트 | 메서드 | 기능 | 상태 |
|------------|--------|------|------|
| `/api/admin/beta-testers` | GET | 베타 테스터 목록 | ✅ |
| `/api/admin/beta-testers` | POST | 베타 테스터 등록 | ✅ |
| `/api/admin/beta-testers/<id>` | DELETE | 등록 취소 | ✅ |
| `/api/admin/beta-testers/<id>/status` | PUT | 상태 변경 | ✅ |

#### 🎁 혜택 관리 (`/api/admin/benefits`)
| 엔드포인트 | 메서드 | 기능 | 상태 |
|------------|--------|------|------|
| `/api/admin/benefits` | GET | 혜택 목록 조회 | ✅ (비활성화) |
| `/api/admin/benefits` | POST | 혜택 생성 | ✅ (비활성화) |
| `/api/admin/benefits/<id>` | PUT | 혜택 수정 | ✅ (비활성화) |
| `/api/admin/benefits/<id>` | DELETE | 혜택 삭제 | ✅ (비활성화) |
| `/api/admin/benefits/bulk` | POST | 대량 혜택 부여 | ✅ (비활성화) |
| `/api/admin/benefits/expire` | POST | 혜택 만료 처리 | ✅ (비활성화) |
| `/api/admin/benefits/stats` | GET | 혜택 통계 | ✅ (비활성화) |

> ⚠️ **참고**: 혜택 관리 시스템은 `app.py`에서 일시적으로 비활성화됨

#### 🚫 계정 정지 관리 (`/api/admin/suspensions`)
| 엔드포인트 | 메서드 | 기능 | 상태 |
|------------|--------|------|------|
| `/api/admin/suspensions` | GET | 정지 목록 조회 | ✅ (비활성화) |
| `/api/admin/suspensions` | POST | 계정 정지 | ✅ (비활성화) |
| `/api/admin/suspensions/<id>` | DELETE | 정지 해제 | ✅ (비활성화) |
| `/api/admin/suspensions/user/<email>` | GET | 사용자별 정지 내역 | ✅ (비활성화) |

> ⚠️ **참고**: 정지 관리 시스템은 `app.py`에서 일시적으로 비활성화됨

#### 📋 요금제 관리 (`/api/admin/plans`)
| 엔드포인트 | 메서드 | 기능 | 상태 |
|------------|--------|------|------|
| `/api/admin/plans` | GET | 요금제 목록 조회 | ✅ |
| `/api/admin/plans/<plan_code>` | GET | 요금제 상세 | ✅ |
| `/api/admin/plans` | POST | 요금제 생성 | ✅ |
| `/api/admin/plans/<id>` | PUT | 요금제 수정 | ✅ |
| `/api/admin/plans/<id>` | DELETE | 요금제 삭제 | ✅ |
| `/api/admin/plans/public` | GET | 공개 요금제 목록 | ✅ |
| `/api/admin/plans/compare` | GET | 요금제 비교 | ✅ |
| `/api/admin/plans/check-limit` | POST | 사용 제한 체크 | ✅ |

#### 📊 통계 API (`/api/stats`)
| 엔드포인트 | 메서드 | 기능 | 상태 |
|------------|--------|------|------|
| `/api/stats/summary` | GET | 전체 요약 통계 | ✅ |
| `/api/stats/users` | GET | 사용자 통계 | ✅ |
| `/api/stats/trades` | GET | 거래 통계 | ✅ |
| `/api/stats/active` | GET | 활성 사용자 | ✅ |
| `/api/stats/beta` | GET | 베타 테스터 통계 | ✅ |

---

## 3. 요금제 시스템

### 3.1 요금제 구조

#### 📦 현재 요금제 (2단계)

| 플랜 | 코드 | 월 가격 | 특징 | 상태 |
|------|------|---------|------|------|
| **무료** | `FREE` | ₩0 | 기본 기능 | ✅ 활성 |
| **프리미엄** | `PREMIUM` | ₩15,000 | 고급 기능 + 자동매매 | ✅ 활성 |

> 💡 **참고**: `PlanConfig` 모델을 통해 동적 요금제 생성 가능

### 3.2 기능별 요금제 매핑

#### 🎯 핵심 기능

| 기능 | FREE | PREMIUM | API 체크 |
|------|------|---------|----------|
| **차트 조회** | ✅ 기본 지표 | ✅ 고급 지표 | ❌ |
| **거래 실행** | ✅ 수동 | ✅ 수동 + 자동 | ❌ |
| **포트폴리오** | ✅ 조회 | ✅ 조회 + 분석 | ❌ |
| **급등 예측** | ✅ 공개 | ✅ 공개 + 알림 | ❌ |
| **자동매매** | ❌ | ✅ 3개 전략 | ✅ |
| **백테스팅** | ❌ | ✅ 무제한 | ❌ |
| **API 접근** | ❌ | ✅ 제한적 | ❌ |

#### 📊 데이터 제한

| 항목 | FREE | PREMIUM | 적용 여부 |
|------|------|---------|-----------|
| **차트 데이터** | 7일 | 무제한 | ❌ |
| **거래 내역** | 30일 | 무제한 | ❌ |
| **모니터링 코인** | 1개 | 10개 | ❌ |
| **관심 목록** | 1개 | 무제한 | ❌ |
| **정책 수** | 1개 | 무제한 | ❌ |

#### 🆘 지원 서비스

| 항목 | FREE | PREMIUM |
|------|------|---------|
| **지원 채널** | 커뮤니티 | 우선 지원 |
| **응답 시간** | 72시간 | 24시간 |
| **전화 지원** | ❌ | ✅ |

### 3.3 요금제 연동 현황

#### ✅ 연동 완료
- 자동매매 API (`/api/auto-trading/*`)
  - 코드: `backend/routes/auto_trading_routes.py`
  - 체크: user_id 기반 권한 확인

#### ❌ 연동 필요
1. **차트 데이터 제한**: 히스토리 기간 제한
2. **포트폴리오 분석**: 고급 지표 잠금
3. **모니터링 코인 수**: 동시 모니터링 제한
4. **관심 목록 수**: watchlist 개수 제한
5. **정책 수**: 거래 정책 개수 제한
6. **백테스팅**: 실행 제한
7. **API 호출 수**: Rate limiting

---

## 4. 구현 완료 기능

### 4.1 인증 및 회원 관리 ✅
- 회원가입/로그인 (JWT)
- 이메일 인증
- 비밀번호 재설정
- 프로필 관리
- API 키 관리
- 세션 관리

### 4.2 거래 시스템 ✅
- 실시간 차트 (TradingView 스타일)
- 20+ 기술적 지표
- 수동 매수/매도
- 자동매매 엔진
- 스윙 트레이딩
- 정책 관리
- 주문 내역 동기화 (DB-first)

### 4.3 포트폴리오 관리 ✅
- 보유 자산 조회
- 계좌 잔고 확인
- 주문 내역 조회
- 분석 통계

### 4.4 급등 예측 시스템 ✅ (NEW - MVP 1차)
- 백테스트 검증 (81.25% 적중률)
- 5가지 기술적 지표 분석
- 실시간 모니터링 UI
- 백테스트 결과 공개 페이지
- 텔레그램 봇 준비 완료

### 4.5 결제 및 구독 ✅
- Toss Payments 연동
- 요금제 관리
- 구독 관리
- 결제 내역

### 4.6 관리자 시스템 ✅
- 사용자 관리
- 베타 테스터 관리
- 요금제 설정
- 통계 대시보드
- 혜택 관리 (비활성화)
- 계정 정지 (비활성화)

### 4.7 시스템 모니터링 ✅
- 헬스 체크 (`/health`)
- DB 상태 체크
- 통계 API

---

## 5. 미구현 기능

### 5.1 🔴 높은 우선순위 (1-2주)

#### 1. 요금제 연동 강화
- **현황**: 자동매매만 체크
- **필요**:
  - [ ] 차트 데이터 기간 제한 (FREE: 7일)
  - [ ] 모니터링 코인 수 제한 (FREE: 1개, PREMIUM: 10개)
  - [ ] 정책 개수 제한 (FREE: 1개, PREMIUM: 무제한)
  - [ ] API Rate Limiting (FREE: 100req/h, PREMIUM: 1000req/h)
- **영향도**: ⭐⭐⭐⭐⭐
- **파일**:
  - `backend/middleware/subscription_check.py` (생성 필요)
  - 각 route 파일에 decorator 추가

#### 2. 텔레그램 알림 봇 활성화
- **현황**: 코드 완성, 토큰 미설정
- **필요**:
  - [ ] @BotFather에서 봇 생성
  - [ ] `.env`에 `TELEGRAM_BOT_TOKEN` 추가
  - [ ] `surge_alert_scheduler.py` systemd 등록
  - [ ] 대시보드에서 구독 설정 UI 추가
- **영향도**: ⭐⭐⭐⭐
- **파일**:
  - `backend/services/surge_alert_scheduler.py` ✅
  - `backend/services/telegram_bot.py` ✅
  - `frontend/dashboard.html` (UI 추가 필요)

#### 3. 대시보드 급등 예측 통합
- **현황**: 별도 페이지로 존재
- **필요**:
  - [ ] 대시보드에 급등 후보 위젯 추가
  - [ ] 알림 설정 UI
  - [ ] 텔레그램 연동 설정
- **영향도**: ⭐⭐⭐⭐
- **파일**: `frontend/dashboard.html`

#### 4. 공개 페이지 개선
- **현황**: 랜딩 페이지 기본 구조만
- **필요**:
  - [ ] 실제 백테스트 데이터 연동
  - [ ] 라이브 급등 후보 표시
  - [ ] 성공 사례 (testimonial)
  - [ ] FAQ 섹션
  - [ ] 블로그/가이드 섹션
- **영향도**: ⭐⭐⭐
- **파일**: `frontend/index.html`

---

### 5.2 🟡 중간 우선순위 (2-4주)

#### 5. 알림 시스템
- **현황**: 텔레그램만 지원 (미활성화)
- **필요**:
  - [ ] 이메일 알림
  - [ ] 웹 푸시 알림 (PWA)
  - [ ] SMS 알림 (선택)
  - [ ] 디스코드 웹훅
- **영향도**: ⭐⭐⭐
- **새 파일**:
  - `backend/services/notification_service.py`
  - `backend/services/email_service.py`

#### 6. 소셜 기능
- **현황**: 없음
- **필요**:
  - [ ] 거래 전략 공유
  - [ ] 팔로우/팔로워
  - [ ] 리더보드
  - [ ] 커뮤니티 피드
- **영향도**: ⭐⭐
- **새 파일**:
  - `backend/routes/social_routes.py`
  - `frontend/community.html`

#### 7. 고급 분석 도구
- **현황**: 기본 차트만
- **필요**:
  - [ ] 포트폴리오 리밸런싱 추천
  - [ ] 위험도 분석
  - [ ] 상관관계 분석
  - [ ] AI 추천 시스템
- **영향도**: ⭐⭐⭐
- **새 파일**:
  - `backend/services/analytics_service.py`
  - `frontend/analytics.html`

#### 8. 모바일 앱
- **현황**: 반응형 웹만
- **필요**:
  - [ ] PWA 변환
  - [ ] React Native 앱
  - [ ] 앱스토어 배포
- **영향도**: ⭐⭐⭐⭐
- **새 폴더**: `mobile/`

---

### 5.3 🟢 낮은 우선순위 (1-3개월)

#### 9. API 마켓플레이스
- **현황**: API 키 관리만
- **필요**:
  - [ ] 공개 API 문서
  - [ ] API 키 티어 관리
  - [ ] Webhook 지원
  - [ ] GraphQL API
- **영향도**: ⭐⭐
- **새 파일**:
  - `backend/routes/api_marketplace.py`
  - `docs/api/`

#### 10. 전략 마켓플레이스
- **현황**: 개인 정책만
- **필요**:
  - [ ] 전략 공유/판매
  - [ ] 구독형 전략
  - [ ] 전략 평가 시스템
  - [ ] 라이센스 관리
- **영향도**: ⭐⭐
- **새 파일**:
  - `backend/routes/strategy_marketplace.py`
  - `frontend/marketplace.html`

#### 11. 멀티 거래소 지원
- **현황**: Upbit만
- **필요**:
  - [ ] 바이낸스 연동
  - [ ] 코인원 연동
  - [ ] 빗썸 연동
  - [ ] 통합 포트폴리오 뷰
- **영향도**: ⭐⭐⭐⭐
- **새 파일**:
  - `backend/common/binance_api.py`
  - `backend/common/coinone_api.py`

#### 12. 세금 및 리포팅
- **현황**: 없음
- **필요**:
  - [ ] 거래 세금 계산
  - [ ] 연간 리포트 생성
  - [ ] CSV/Excel 내보내기
  - [ ] 회계 소프트웨어 연동
- **영향도**: ⭐⭐⭐
- **새 파일**:
  - `backend/services/tax_service.py`
  - `frontend/reports.html`

---

## 6. 우선순위 개발 계획

### Phase 1: 즉시 (1-2주) 🔴

**목표**: 완전한 MVP 출시

1. **요금제 연동 완성** (3일)
   - [ ] Middleware 개발
   - [ ] 각 API에 적용
   - [ ] 프론트엔드 잠금 UI

2. **텔레그램 봇 활성화** (2일)
   - [ ] 봇 생성 및 토큰 발급
   - [ ] systemd 등록
   - [ ] 대시보드 UI 통합

3. **대시보드 개선** (3일)
   - [ ] 급등 예측 위젯 추가
   - [ ] 알림 설정 UI
   - [ ] 성능 최적화

4. **공개 페이지 완성** (2일)
   - [ ] FAQ 추가
   - [ ] 성공 사례 추가
   - [ ] SEO 최적화

**예상 완료**: 2025-12-28

---

### Phase 2: 단기 (2-4주) 🟡

**목표**: 사용자 경험 향상

1. **알림 시스템 확장** (1주)
   - [ ] 이메일 알림
   - [ ] 웹 푸시 (PWA)

2. **고급 분석 도구** (1주)
   - [ ] 포트폴리오 분석
   - [ ] 위험도 계산

3. **모바일 최적화** (2주)
   - [ ] PWA 변환
   - [ ] 앱 아이콘/매니페스트

**예상 완료**: 2026-01-25

---

### Phase 3: 중기 (1-3개월) 🟢

**목표**: 플랫폼 확장

1. **소셜 기능** (2주)
2. **API 마켓플레이스** (3주)
3. **전략 마켓플레이스** (3주)
4. **멀티 거래소** (4주)

**예상 완료**: 2026-03-31

---

## 📊 요약 통계

### 구현 현황

| 카테고리 | 완료 | 진행중 | 미구현 | 진행률 |
|----------|------|--------|--------|--------|
| **인증/회원** | 8 | 0 | 0 | 100% ✅ |
| **거래 시스템** | 9 | 0 | 1 | 90% ✅ |
| **포트폴리오** | 4 | 0 | 0 | 100% ✅ |
| **급등 예측** | 5 | 1 | 1 | 71% 🟡 |
| **결제/구독** | 6 | 0 | 0 | 100% ✅ |
| **관리자** | 8 | 0 | 0 | 100% ✅ |
| **알림** | 0 | 1 | 3 | 20% 🔴 |
| **소셜** | 0 | 0 | 4 | 0% 🔴 |
| **고급 기능** | 0 | 0 | 8 | 0% 🔴 |
| **총계** | **40** | **2** | **17** | **68%** 🟡 |

### 요금제 연동 현황

| 기능 그룹 | 연동 완료 | 연동 필요 | 진행률 |
|-----------|-----------|-----------|--------|
| **핵심 기능** | 1/7 | 6/7 | 14% 🔴 |
| **데이터 제한** | 0/5 | 5/5 | 0% 🔴 |
| **총계** | **1/12** | **11/12** | **8%** 🔴 |

---

## 🎯 핵심 액션 아이템

### 이번 주 (Week 1)
1. ✅ **완료**: 급등 예측 MVP 배포
2. 🔴 **진행**: 요금제 연동 Middleware 개발
3. 🔴 **진행**: 텔레그램 봇 활성화
4. 🟡 **준비**: 대시보드 급등 위젯 설계

### 다음 주 (Week 2)
1. 대시보드 UI 개선
2. 공개 페이지 완성
3. FAQ 및 가이드 작성
4. 베타 테스터 모집 시작

---

## 📞 문의 및 지원

- **프로덕션 URL**: https://coinpulse.sinsi.ai
- **관리자 대시보드**: https://coinpulse.sinsi.ai/admin.html
- **API 문서**: (준비 중)
- **지원 이메일**: (설정 필요)

---

**최종 업데이트**: 2025-12-14
**작성자**: Claude Code Assistant
**버전**: 1.0.0
