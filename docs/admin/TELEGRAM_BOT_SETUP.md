# 텔레그램 봇 자동 입금 알림 설정 가이드

## 📋 개요

기업은행 계좌(169-176889-01-012)에 입금되면 텔레그램으로 즉시 알림을 받고, 자동으로 구독을 활성화하는 시스템입니다.

**자동화 흐름**:
```
1. 사용자가 기업은행 계좌로 입금
   ↓
2. 기업은행에서 SMS 문자 발송
   ↓
3. IFTTT/Zapier가 SMS를 텔레그램 봇으로 전달
   ↓
4. CoinPulse 웹훅이 입금 정보 파싱
   ↓
5. payment_confirmations 테이블에서 자동 매칭
   ↓
6. 매칭 성공 시 자동 승인 → 구독 활성화
   ↓
7. 관리자에게 텔레그램 알림 전송
```

---

## 🤖 Step 1: 텔레그램 봇 생성

### 1.1 BotFather와 대화 시작

1. 텔레그램 앱에서 [@BotFather](https://t.me/BotFather) 검색
2. `/start` 명령어 입력
3. `/newbot` 명령어 입력

### 1.2 봇 정보 입력

```
BotFather: Alright, a new bot. How are we going to call it? Please choose a name for your bot.
You: CoinPulse Payment Bot

BotFather: Good. Now let's choose a username for your bot. It must end in `bot`. Like this, for example: TetrisBot or tetris_bot.
You: coinpulse_payment_bot

BotFather: Done! Congratulations on your new bot. You will find it at t.me/coinpulse_payment_bot. You can now add a description...

Here is your token: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 1.3 봇 토큰 저장

**중요**: 이 토큰을 안전하게 저장하세요. 나중에 환경 변수로 사용합니다.

```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

---

## 💬 Step 2: 관리자 Chat ID 확인

### 2.1 봇과 대화 시작

1. 텔레그램에서 방금 만든 봇 검색 (`@coinpulse_payment_bot`)
2. `/start` 명령어 입력
3. "안녕하세요" 메시지 전송

### 2.2 Chat ID 확인

브라우저에서 다음 URL 접속:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

**예시**:
```
https://api.telegram.org/bot1234567890:ABCdefGHIjklMNOpqrsTUVwxyz/getUpdates
```

**응답 예시**:
```json
{
  "ok": true,
  "result": [
    {
      "update_id": 123456789,
      "message": {
        "message_id": 1,
        "from": {
          "id": 987654321,  ← 이 숫자가 Chat ID
          "first_name": "Your Name"
        },
        "chat": {
          "id": 987654321,  ← 이 숫자가 Chat ID
          "first_name": "Your Name",
          "type": "private"
        },
        "date": 1639123456,
        "text": "안녕하세요"
      }
    }
  ]
}
```

### 2.3 Chat ID 저장

```
TELEGRAM_ADMIN_CHAT_ID=987654321
```

---

## 📱 Step 3: SMS 자동 전달 설정 (IFTTT 사용)

### 3.1 IFTTT 앱 설치

- **iOS**: App Store에서 "IFTTT" 검색
- **Android**: Google Play에서 "IFTTT" 검색

### 3.2 IFTTT 계정 생성

1. IFTTT 앱 실행
2. 이메일로 회원가입
3. 권한 허용 (SMS 읽기 권한 필수)

### 3.3 Applet 생성

#### Trigger 설정 (IF)

1. "Create" 버튼 클릭
2. "If This" 클릭
3. "Android SMS" 검색 및 선택
4. "New SMS received matches search" 선택
5. Search filter 입력:
   ```
   from:기업은행
   ```
   또는
   ```
   from:15881661
   ```
   (기업은행 SMS 발신 번호)

#### Action 설정 (THEN)

1. "Then That" 클릭
2. "Webhooks" 검색 및 선택
3. "Make a web request" 선택
4. 다음 정보 입력:

**URL**:
```
https://coinpulse.sinsi.ai/api/telegram/webhook
```

**Method**: `POST`

**Content Type**: `application/json`

**Body**:
```json
{
  "message": {
    "chat": {
      "id": "{{TELEGRAM_ADMIN_CHAT_ID}}"
    },
    "text": "{{Text}}"
  }
}
```

**예시** (실제 Chat ID 사용):
```json
{
  "message": {
    "chat": {
      "id": "987654321"
    },
    "text": "{{Text}}"
  }
}
```

5. "Create action" 클릭
6. "Continue" 클릭
7. Applet 이름: "기업은행 입금 알림"
8. "Finish" 클릭

---

## 🔧 Step 4: 환경 변수 설정

### 4.1 로컬 환경 (.env 파일)

`D:\Claude\Projects\Active\coinpulse\.env` 파일에 추가:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ADMIN_CHAT_ID=987654321
```

### 4.2 프로덕션 환경 (Vultr 서버)

SSH 접속 후:

```bash
ssh root@158.247.222.216

# .env 파일 편집
cd /opt/coinpulse
nano .env

# 다음 줄 추가
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ADMIN_CHAT_ID=987654321

# 저장: Ctrl+O, Enter, Ctrl+X

# 서비스 재시작
sudo systemctl restart coinpulse
sudo systemctl status coinpulse
```

---

## 🧪 Step 5: 테스트

### 5.1 파싱 테스트

먼저 SMS 파싱이 제대로 되는지 테스트:

```bash
curl -X POST https://coinpulse.sinsi.ai/api/telegram/test-parse \
  -H "Content-Type: application/json" \
  -d '{
    "text": "[기업은행] 입금\n169176889\n홍길동\n99,000원\n12/20 14:30"
  }'
```

**예상 응답**:
```json
{
  "success": true,
  "parsed": {
    "depositor_name": "홍길동",
    "amount": 99000,
    "transfer_date": "2025-12-20T14:30:00",
    "account_number": "169-176889-01-012"
  },
  "original_text": "[기업은행] 입금\n169176889\n홍길동\n99,000원\n12/20 14:30"
}
```

### 5.2 웹훅 테스트

실제 웹훅 동작 테스트:

```bash
curl -X POST https://coinpulse.sinsi.ai/api/telegram/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "chat": {
        "id": "987654321"
      },
      "text": "[기업은행] 입금\n169176889\n홍길동\n99,000원\n12/20 14:30"
    }
  }'
```

**예상 동작**:
1. API가 입금 정보를 파싱
2. payment_confirmations 테이블에서 매칭 시도
3. 매칭 성공 시 자동 승인 및 구독 활성화
4. 텔레그램으로 결과 알림 전송

### 5.3 실제 입금 테스트

1. 테스트 계정으로 로그인
2. 대시보드 → "프로로 업그레이드" 클릭
3. payment_guide.html에서 계좌 정보 확인
4. payment_confirm.html에서 입금 정보 제출
5. 실제 입금 (소액으로 테스트: 1,000원)
6. 기업은행 SMS → IFTTT → 텔레그램 봇 → 자동 처리
7. 텔레그램으로 알림 수신 확인

---

## 📊 Step 6: 모니터링

### 6.1 웹훅 헬스 체크

```bash
curl https://coinpulse.sinsi.ai/api/telegram/health
```

**예상 응답**:
```json
{
  "status": "healthy",
  "service": "telegram_webhook",
  "bot_configured": true,
  "admin_configured": true,
  "timestamp": "2025-12-20T15:30:00"
}
```

### 6.2 로그 확인

```bash
ssh root@158.247.222.216

# Flask 로그 확인
journalctl -u coinpulse -f

# 텔레그램 웹훅 관련 로그 필터링
journalctl -u coinpulse | grep "Telegram"
```

### 6.3 pending confirmations 확인

```bash
curl https://coinpulse.sinsi.ai/api/admin/payment-confirmations/pending \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🔍 문제 해결

### Q1: 텔레그램 알림이 안 와요

**확인 사항**:
1. `.env` 파일에 `TELEGRAM_BOT_TOKEN`과 `TELEGRAM_ADMIN_CHAT_ID` 설정되었는지 확인
2. 서비스 재시작했는지 확인 (`systemctl restart coinpulse`)
3. IFTTT Applet이 활성화되었는지 확인 (IFTTT 앱에서 확인)
4. 기업은행 SMS 수신 번호가 맞는지 확인 (15881661 또는 "기업은행")

### Q2: 파싱은 되는데 매칭이 안 돼요

**원인**:
- 입금자명이 payment_confirmations 테이블의 user_name과 일치하지 않음

**해결 방법**:
1. 관리자 페이지에서 pending confirmations 확인
2. 입금자명과 사용자명 비교
3. 수동으로 승인 처리

### Q3: 자동 승인이 너무 자주 실패해요

**개선 방법**:
- 입금자명 유사도 매칭 알고리즘 개선
- 사용자에게 입금자명을 정확히 입력하도록 안내
- payment_confirm.html에서 입금자명 자동 추천 기능 추가

---

## 🎯 다음 단계

### Phase 2: Toss Payments 가상계좌 통합

완전 자동화를 위해 Toss Payments 가상계좌를 연동할 수 있습니다.

**장점**:
- 사용자별 고유 가상계좌 발급
- 입금 즉시 웹훅 자동 호출
- 100% 정확한 매칭
- 환불/취소 처리 용이

**단점**:
- 수수료: 2.9% + VAT
- 사업자 등록 필요

구현 가이드: `docs/admin/TOSS_PAYMENTS_SETUP.md` (추후 작성)

---

## 📝 참고 자료

- [텔레그램 봇 API 문서](https://core.telegram.org/bots/api)
- [IFTTT Applets 가이드](https://ifttt.com/explore)
- [CoinPulse 결제 워크플로우 가이드](PAYMENT_WORKFLOW_GUIDE.md)
- [관리자 시스템 요약](ADMIN_SUMMARY.md)

---

## 🆘 지원

문제가 발생하면:
1. 로그 확인: `journalctl -u coinpulse -f`
2. Health check: `curl https://coinpulse.sinsi.ai/api/telegram/health`
3. GitHub Issues: https://github.com/ln9swrd/coinpulse/issues

관리자: ln9swrd@gmail.com
