# Google Workspace SMTP 설정 가이드

## 📧 Google Workspace에서 앱 비밀번호 생성하기

코인펄스에서 이메일을 발송하려면 Google Workspace의 **앱 비밀번호**가 필요합니다.

---

## 🔐 Step 1: 2단계 인증 활성화

앱 비밀번호를 생성하려면 먼저 2단계 인증이 활성화되어 있어야 합니다.

### 1.1 Google Account 설정
1. Google Account 페이지 접속: https://myaccount.google.com
2. **보안** 메뉴 클릭
3. **Google에 로그인** 섹션에서 **2단계 인증** 클릭
4. 화면 안내에 따라 2단계 인증 설정

---

## 🔑 Step 2: 앱 비밀번호 생성

### 2.1 앱 비밀번호 페이지 접속
1. Google Account 보안 페이지: https://myaccount.google.com/security
2. **Google에 로그인** 섹션
3. **앱 비밀번호** 클릭 (2단계 인증 활성화 후 나타남)

### 2.2 앱 비밀번호 생성
1. **앱 선택**: "메일" 선택
2. **기기 선택**: "기타(맞춤 이름)" 선택
3. **이름 입력**: "CoinPulse Production Server" 입력
4. **생성** 버튼 클릭

### 2.3 비밀번호 복사
- 16자리 앱 비밀번호가 표시됩니다 (예: `abcd efgh ijkl mnop`)
- **공백 제거**: `abcdefghijklmnop`
- 이 비밀번호를 안전한 곳에 복사해둡니다

⚠️ **주의**: 이 비밀번호는 한 번만 표시되므로 반드시 복사해두세요!

---

## 🌐 Step 3: Vultr 서버에 환경 변수 설정

### 3.1 SSH 접속
```bash
ssh root@158.247.222.216
```

### 3.2 .env 파일 수정
```bash
cd /opt/coinpulse
nano .env
```

### 3.3 SMTP 설정 추가
```bash
# Email Service
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@sinsi.ai
SMTP_PASSWORD=abcdefghijklmnop  # 방금 생성한 앱 비밀번호
FROM_EMAIL=noreply@sinsi.ai
FROM_NAME=코인펄스
ENVIRONMENT=production
BASE_URL=https://coinpulse.sinsi.ai
```

### 3.4 저장 및 종료
- `Ctrl + O` (저장)
- `Enter` (확인)
- `Ctrl + X` (종료)

---

## 🔄 Step 4: 서버 재시작

```bash
sudo systemctl restart coinpulse
sudo systemctl status coinpulse
```

### 로그 확인
```bash
journalctl -u coinpulse -f
```

---

## ✅ Step 5: 이메일 발송 테스트

### 5.1 Python 테스트 스크립트
```python
# test_email.py
import os
from backend.services.email_service import email_service

# 테스트 이메일 발송
success = email_service.send_verification_email(
    to_email="your-email@example.com",
    username="테스트유저",
    token="test-token-123"
)

if success:
    print("✅ 이메일 발송 성공!")
else:
    print("❌ 이메일 발송 실패")
```

### 5.2 실행
```bash
cd /opt/coinpulse
python test_email.py
```

---

## 🛠️ 문제 해결

### 문제 1: "Username and Password not accepted"
**원인**: 앱 비밀번호가 잘못되었거나 2단계 인증이 비활성화됨

**해결**:
1. 2단계 인증 활성화 확인
2. 앱 비밀번호 재생성
3. .env 파일의 `SMTP_PASSWORD` 재확인

### 문제 2: "SMTP Authentication Error"
**원인**: SMTP 사용자명이 잘못됨

**해결**:
- `SMTP_USER`가 `noreply@sinsi.ai` (전체 이메일 주소)인지 확인

### 문제 3: "Connection timeout"
**원인**: 방화벽이 SMTP 포트 차단

**해결**:
```bash
# 방화벽 규칙 확인
sudo ufw status

# SMTP 포트 허용
sudo ufw allow 587/tcp
```

---

## 📋 체크리스트

설정 완료 전 아래 항목을 확인하세요:

```
□ Google Workspace에 2단계 인증 활성화
□ 앱 비밀번호 생성 (16자리)
□ 앱 비밀번호를 공백 제거하여 복사
□ Vultr 서버 .env 파일에 SMTP 설정 추가
□ SMTP_USER = noreply@sinsi.ai (전체 주소)
□ SMTP_PASSWORD = 앱 비밀번호 (공백 제거)
□ ENVIRONMENT = production
□ coinpulse 서비스 재시작
□ 테스트 이메일 발송 성공 확인
```

---

## 🎯 다음 단계

이메일 설정이 완료되면 다음 기능을 구현할 수 있습니다:

1. ✅ 회원가입 인증 메일
2. ✅ 비밀번호 재설정 메일
3. ✅ 거래 알림 메일
4. ✅ 급등 예측 알림
5. ✅ 주간 포트폴리오 보고서

---

## 📞 지원

문제가 발생하면:
- 이메일: support@sinsi.ai
- 전화: 010-9575-4890

---

**작성일**: 2025-12-17
**최종 수정**: 2025-12-17
