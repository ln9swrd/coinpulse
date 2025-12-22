# 이메일 통합 시스템 완료 보고서

## 개요

CoinPulse 전체 시스템을 이메일 중심으로 통합했습니다.

**완료일**: 2025-12-23

---

## ✅ 완료된 작업

### 1. 회원가입: 이메일 필수 입력

**파일**: `backend/routes/auth_routes.py`

**현재 상태**: ✅ **이미 구현됨** (line 121)

```python
if not email or not username or not password:
    return jsonify({'error': 'Email, username, and password are required'}), 400
```

**기능**:
- 이메일, 사용자명, 비밀번호 모두 필수
- 이메일 형식 유효성 검사
- 중복 이메일 확인
- 이메일 인증 시스템 (verification token)

**관련 엔드포인트**:
- `POST /api/auth/register` - 회원가입
- `POST /api/auth/verify-email` - 이메일 인증
- `POST /api/auth/resend-verification` - 인증 이메일 재전송

---

### 2. 계좌이체: 이메일 기입 필수

**파일**: `backend/routes/payment_confirmation.py`

**현재 상태**: ✅ **이미 구현됨** (line 51, 201)

```python
class PaymentConfirmation(Base):
    user_email = Column(String(255), nullable=False)  # 필수 필드
```

**기능**:
- 계좌이체 확인 요청 시 이메일 자동 포함
- JWT 토큰에서 이메일 자동 추출
- 관리자 확인 후 이메일로 결과 통보

**관련 엔드포인트**:
- `POST /api/payment-confirm/submit` - 계좌이체 확인 요청
- `GET /api/payment-confirm/my-confirmations` - 내 확인 요청 목록
- `GET /api/payment-confirm/status/<id>` - 확인 상태 조회

---

### 3. 텔레그램: 이메일 연동

**파일**: `backend/routes/telegram_link_routes.py`

**현재 상태**: ✅ **이미 구현됨** (line 189)

```python
return jsonify({
    'user': {
        'username': user.username,
        'email': user.email,  # 이메일 포함
        'telegram_username': telegram_username
    }
})
```

**기능**:
- 텔레그램 계정 연동 시 이메일 자동 저장
- User 모델에 `telegram_chat_id`, `telegram_username` 필드
- 연동 코드 (6자리 숫자) 생성 및 검증
- 15분 만료 시간

**관련 엔드포인트**:
- `POST /api/telegram/link/generate` - 연동 코드 생성
- `POST /api/telegram/link/verify` - 연동 코드 검증
- `POST /api/telegram/link/unlink` - 연동 해제

---

### 4. 요금제: 이메일 알림 혜택 추가

**파일**: `backend/models/plan_config.py`

**변경사항**: ✅ **신규 추가** (line 56-62)

#### 추가된 데이터베이스 컬럼

```python
# 기능 제한 - 알림 (Email Notifications) ✉️
email_notifications_enabled = Column(Boolean, default=False, nullable=False)
daily_email_limit = Column(Integer, default=0, nullable=False)  # 0 = 무제한
signal_notifications = Column(Boolean, default=False, nullable=False)
portfolio_notifications = Column(Boolean, default=False, nullable=False)
trade_notifications = Column(Boolean, default=False, nullable=False)
system_notifications = Column(Boolean, default=False, nullable=False)
```

#### 플랜별 이메일 알림 혜택

| 플랜 | 이메일 활성화 | 일일 한도 | 시그널 | 포트폴리오 | 거래 | 시스템 |
|------|--------------|----------|--------|-----------|------|--------|
| **Free** | ❌ | 0 | ❌ | ❌ | ❌ | ❌ |
| **Basic** | ✅ | 10건/일 | ✅ | ❌ | ❌ | ✅ |
| **Pro/Premium** | ✅ | 50건/일 | ✅ | ✅ | ✅ | ✅ |
| **Enterprise** | ✅ | 무제한 | ✅ | ✅ | ✅ | ✅ |

---

## 🎯 이메일 알림 종류

### 1. 시그널 알림 (Signal Notifications)

**발송 조건**:
- Surge 예측 시스템이 급등 신호 감지
- 사용자가 "시그널 알림" 활성화
- 플랜에서 `signal_notifications: true`

**이메일 내용**:
```
제목: [CoinPulse] BTC 급등 시그널 감지!

내용:
- 코인: KRW-BTC
- 현재가: 55,000,000원
- 변동률: +8.5%
- 시간: 2025-12-23 14:30:00
- 지표: RSI 72.5, MACD Bullish
```

### 2. 포트폴리오 알림 (Portfolio Notifications)

**발송 조건**:
- 목표 수익률 달성
- 손실 임계값 초과
- 포지션 변동
- 플랜에서 `portfolio_notifications: true`

**이메일 내용**:
```
제목: [CoinPulse] 포트폴리오 목표 수익률 달성!

내용:
- 현재 수익률: +15%
- 목표 수익률: +10%
- 총 평가액: 5,500,000원
- 수익금: +750,000원
```

### 3. 거래 실행 알림 (Trade Notifications)

**발송 조건**:
- 자동매매 실행 (매수/매도)
- 수동 주문 체결
- 주문 취소/실패
- 플랜에서 `trade_notifications: true`

**이메일 내용**:
```
제목: [CoinPulse] 자동 매수 주문 체결

내용:
- 전략: 급등 추세 매매
- 코인: KRW-ETH
- 매수가: 2,100,000원
- 수량: 2.5 ETH
- 총액: 5,250,000원
```

### 4. 시스템 알림 (System Notifications)

**발송 조건**:
- 계정 보안 (로그인, 비밀번호 변경)
- 구독 갱신/만료
- 시스템 유지보수
- 플랜에서 `system_notifications: true`

**이메일 내용**:
```
제목: [CoinPulse] Pro 플랜 갱신 완료

내용:
- 플랜: Pro (월간)
- 결제 금액: 29,000원
- 다음 결제일: 2025-01-23
- 결제 방법: 계좌이체
```

---

## 📧 AWS SES 통합

### 발신 이메일 주소

```
noreply@sinsi.ai      - 시스템 알림 (발신 전용)
alerts@sinsi.ai       - 거래 시그널 알림
support@sinsi.ai      - 고객 지원
admin@sinsi.ai        - 관리자 알림
billing@sinsi.ai      - 결제/구독 알림
```

### 설정 정보

**SMTP 서버**:
```
Host: email-smtp.ap-northeast-2.amazonaws.com
Port: 587 (TLS)
Authentication: Required (SMTP credentials)
```

**환경 변수** (.env):
```bash
SMTP_HOST=email-smtp.ap-northeast-2.amazonaws.com
SMTP_PORT=587
SMTP_USER=AKIA[...]
SMTP_PASSWORD=[...]
SMTP_FROM_EMAIL=noreply@sinsi.ai
SMTP_FROM_NAME=CoinPulse
```

### 발송 한도

**Current Status** (Production 모드):
- 일일 발송 한도: **50,000건**
- 초당 발송 속도: **14건**
- 수신자 제한: **없음**

**비용**:
- 월 62,000건까지: **무료** (AWS 프리티어)
- 초과분: $0.10 / 1,000건

---

## 🛠️ 설치 및 마이그레이션

### Step 1: 데이터베이스 마이그레이션

**스크립트 실행**:
```bash
cd D:\Claude\Projects\Active\coinpulse
python scripts/add_email_notifications_to_plans.py
```

**작업 내용**:
1. `plan_configs` 테이블에 6개 컬럼 추가
2. 기존 플랜에 이메일 알림 기능 설정
3. 플랜 비교표 출력

### Step 2: 서버 재시작

**로컬 환경**:
```bash
python app.py
```

**프로덕션 환경**:
```bash
ssh root@158.247.222.216
cd /opt/coinpulse
sudo systemctl restart coinpulse
sudo systemctl status coinpulse
```

### Step 3: 동작 확인

**테스트 이메일 발송**:
```bash
python scripts/test_email.py
```

**API 테스트**:
```bash
# 플랜 목록 조회 (이메일 알림 정보 포함)
curl https://coinpulse.sinsi.ai/api/plans
```

---

## 📊 API 응답 예시

### GET /api/plans

```json
{
  "success": true,
  "plans": [
    {
      "plan_code": "pro",
      "plan_name": "Pro",
      "price": {
        "monthly": 29000,
        "annual": 290000
      },
      "notifications": {
        "email_enabled": true,
        "daily_email_limit": 50,
        "signal_notifications": true,
        "portfolio_notifications": true,
        "trade_notifications": true,
        "system_notifications": true
      },
      "features": {
        "auto_trading": true,
        "advanced_indicators": true,
        "backtesting": true
      }
    }
  ]
}
```

---

## 🎨 프론트엔드 통합 (향후 작업)

### 대시보드 설정 → 알림 탭

**표시할 정보**:
```html
<div class="notification-settings">
  <h3>이메일 알림 설정</h3>

  <!-- 플랜 제한 표시 -->
  <div class="plan-limit">
    <p>현재 플랜: Pro</p>
    <p>일일 한도: 50건 (오늘 사용: 12건)</p>
  </div>

  <!-- 알림 타입 선택 -->
  <div class="notification-types">
    <label>
      <input type="checkbox" name="signal" checked disabled={!plan.signal_notifications}>
      시그널 알림 ✅
    </label>

    <label>
      <input type="checkbox" name="portfolio" checked disabled={!plan.portfolio_notifications}>
      포트폴리오 알림 ✅
    </label>

    <label>
      <input type="checkbox" name="trade" checked disabled={!plan.trade_notifications}>
      거래 실행 알림 ✅
    </label>

    <label>
      <input type="checkbox" name="system" checked>
      시스템 알림 ✅
    </label>
  </div>

  <!-- 이메일 주소 -->
  <div class="email-address">
    <label>알림 받을 이메일</label>
    <input type="email" value="user@example.com" readonly>
    <small>회원가입 시 등록한 이메일로 발송됩니다</small>
  </div>

  <!-- 플랜 업그레이드 -->
  <div class="upgrade-prompt" *ngIf="plan.plan_code === 'free'">
    <p>⚠️ Free 플랜은 이메일 알림을 사용할 수 없습니다</p>
    <button>Pro 플랜으로 업그레이드</button>
  </div>
</div>
```

---

## 🔐 보안 및 스팸 방지

### 1. 일일 발송 한도

**구현 방법**:
```python
def check_email_limit(user_id, plan_code):
    """Check if user has reached daily email limit"""
    plan = session.query(PlanConfig).filter(
        PlanConfig.plan_code == plan_code
    ).first()

    if plan.daily_email_limit == 0:
        return True  # 무제한

    # 오늘 발송한 이메일 수 확인
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    sent_today = session.query(EmailLog).filter(
        EmailLog.user_id == user_id,
        EmailLog.sent_at >= today_start
    ).count()

    return sent_today < plan.daily_email_limit
```

### 2. 사용자 알림 설정 저장

**데이터베이스 테이블** (신규):
```sql
CREATE TABLE user_notification_settings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    signal_notifications_enabled BOOLEAN DEFAULT TRUE,
    portfolio_notifications_enabled BOOLEAN DEFAULT TRUE,
    trade_notifications_enabled BOOLEAN DEFAULT TRUE,
    system_notifications_enabled BOOLEAN DEFAULT TRUE,
    notification_email VARCHAR(255),  -- 기본값: user.email
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 3. 이메일 발송 로그

**데이터베이스 테이블** (신규):
```sql
CREATE TABLE email_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    recipient_email VARCHAR(255) NOT NULL,
    email_type VARCHAR(50) NOT NULL,  -- 'signal', 'portfolio', 'trade', 'system'
    subject VARCHAR(255) NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'sent',  -- 'sent', 'failed', 'bounced'
    error_message TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 🎯 다음 단계 (선택사항)

### 1. 프론트엔드 UI 구현
- [ ] 대시보드 설정 → 알림 탭 개발
- [ ] 플랜별 기능 제한 표시
- [ ] 알림 설정 저장 API 통합

### 2. 이메일 템플릿 개선
- [ ] HTML 디자인 향상
- [ ] 차트 이미지 추가
- [ ] 브랜드 로고 삽입

### 3. 고급 기능
- [ ] 이메일 발송 로그 조회
- [ ] 일일 한도 사용량 표시
- [ ] 알림 히스토리 페이지

### 4. 모니터링
- [ ] AWS SES 대시보드 확인
- [ ] Bounce/Complaint rate 모니터링
- [ ] 발송 한도 사용량 추적

---

## 📝 변경 파일 목록

| 파일 | 변경 내용 | 상태 |
|------|----------|------|
| `backend/routes/auth_routes.py` | 이메일 필수 입력 (기존) | ✅ 확인 |
| `backend/routes/payment_confirmation.py` | 이메일 필수 입력 (기존) | ✅ 확인 |
| `backend/routes/telegram_link_routes.py` | 이메일 연동 (기존) | ✅ 확인 |
| `backend/models/plan_config.py` | 이메일 알림 컬럼 추가 | ✅ 수정 |
| `scripts/add_email_notifications_to_plans.py` | 마이그레이션 스크립트 | ✅ 신규 |
| `docs/guides/EMAIL_INTEGRATION_SUMMARY.md` | 요약 문서 | ✅ 신규 |

---

## ✅ 체크리스트

### 백엔드
- [x] 회원가입 이메일 필수 확인
- [x] 계좌이체 이메일 필수 확인
- [x] 텔레그램 이메일 연동 확인
- [x] 플랜 설정 이메일 알림 추가
- [x] 데이터베이스 마이그레이션 스크립트 작성

### 인프라
- [x] AWS SES 도메인 인증
- [x] AWS SES Production Access 승인
- [x] SMTP 자격증명 생성
- [x] 서버 환경 변수 설정
- [x] 테스트 이메일 발송 성공

### 문서
- [x] 이메일 통합 요약 문서
- [x] 플랜별 혜택 비교표
- [x] API 응답 예시
- [x] 마이그레이션 가이드

---

**작성일**: 2025-12-23
**작성자**: Claude Code
**버전**: 1.0
