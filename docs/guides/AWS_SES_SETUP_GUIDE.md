# AWS SES 이메일 발송 설정 가이드

## 개요

CoinPulse 이메일 알림 시스템을 위한 AWS SES (Simple Email Service) 설정 가이드입니다.

**비용**: $0.10 / 1,000건 (월 62,000건까지 무료 티어)

---

## 설정 단계

### ✅ Step 1: AWS SES 도메인 추가 (완료)

- AWS SES Console에서 sinsi.ai 도메인 추가 완료

### ✅ Step 2: DNS 레코드 설정 (완료)

hosting.kr DNS 관리자에서 다음 레코드 추가 완료:

#### DKIM 인증 (3개 CNAME 레코드)
```
1. w6326ii2g7aiihgh2qczgh5og5zaccdzs._domainkey.sinsi.ai
   → w6326ii2g7aiihgh2qczgh5og5zaccdzs.dkim.amazonses.com

2. h6abqdcz0popfrentfrvaldotgz5owz2it._domainkey.sinsi.ai
   → h6abqdcz0popfrentfrvaldotgz5owz2it.dkim.amazonses.com

3. z3xewb2y2bpsuji5qglhxvvxu6gphm6d._domainkey.sinsi.ai
   → z3xewb2y2bpsuji5qglhxvvxu6gphm6d.dkim.amazonses.com
```

#### MAIL FROM 설정
```
MX: mail.sinsi.ai → 10 feedback-smtp.ap-northeast-2.amazonses.com
TXT: mail.sinsi.ai → v=spf1 include:amazonses.com ~all
```

#### DMARC 정책
```
TXT: _dmarc.sinsi.ai → v=DMARC1; p=none;
```

### ⏳ Step 3: DNS 전파 대기 (현재 단계)

**소요 시간**: 10-30분

**확인 방법**:
```cmd
nslookup -type=CNAME w6326ii2g7aiihgh2qczgh5og5zaccdzs._domainkey.sinsi.ai
```

**확인 위치**:
- AWS SES Console → Verified identities → sinsi.ai
- Status: "Pending" → "Verified" (전파 완료 시)

---

### ⏸️ Step 4: 이메일 주소 인증 (DNS 전파 후)

#### 4-1. AWS SES에서 이메일 주소 추가

AWS SES Console → Verified identities → Create identity → Email address

**인증할 이메일 주소** (5개):
```
1. noreply@sinsi.ai    - 시스템 알림용 (발신 전용)
2. alerts@sinsi.ai     - 거래 시그널 알림
3. support@sinsi.ai    - 고객 지원
4. admin@sinsi.ai      - 관리자 알림
5. billing@sinsi.ai    - 결제/구독 관련
```

#### 4-2. 이메일 수신 설정

**방법 1: Catch-All 포워딩 (권장)**

hosting.kr 메일 관리에서 설정:
```
*@sinsi.ai → your-main-email@gmail.com
```

**장점**:
- 5개 주소 모두 한 곳에서 관리
- 추가 비용 없음
- 설정 간단

**방법 2: 개별 메일박스 생성**

각 주소별로 메일박스 생성 (hosting.kr 유료 플랜 필요)

#### 4-3. 인증 링크 클릭

각 이메일 주소로 AWS에서 발송한 인증 링크 클릭
- 제목: "Amazon SES Email Address Verification Request"
- 유효 기간: 24시간

---

### ⏸️ Step 5: Production Access 신청 (이메일 인증 후)

#### 5-1. Sandbox 모드 제한사항

**현재 제한** (Sandbox):
- 일일 발송 한도: 200건
- 초당 발송 속도: 1건
- 수신자: 인증된 이메일만 가능

**Production 모드**:
- 일일 발송 한도: 50,000건 (이후 증가 가능)
- 초당 발송 속도: 14건
- 수신자: 모든 이메일 주소 가능

#### 5-2. Production Access 신청

AWS SES Console → Account Dashboard → Request production access

**신청서 작성 내용**:

```
Use case description:
We are operating a cryptocurrency trading automation platform (CoinPulse)
that sends the following types of emails to our users:

1. Trading signal notifications (price surge alerts)
2. Portfolio status updates
3. Account security notifications
4. Subscription and billing emails
5. System maintenance announcements

Expected volume: 500-1,000 emails per day
Recipient opt-in method: Users explicitly enable notifications in dashboard settings
Bounce/complaint handling: Automated bounce processing + manual review system

Website: https://coinpulse.sinsi.ai
```

**심사 기간**: 24시간 (영업일 기준)

---

### ⏸️ Step 6: SMTP 자격증명 생성 (Production 승인 후)

#### 6-1. IAM SMTP 사용자 생성

AWS SES Console → SMTP Settings → Create SMTP credentials

**자격증명 정보**:
- SMTP Username: (자동 생성됨 - 20자)
- SMTP Password: (자동 생성됨 - 44자)

**⚠️ 주의**: 비밀번호는 생성 시 1회만 표시됨 (반드시 저장)

#### 6-2. SMTP 설정 정보

```
SMTP Host: email-smtp.ap-northeast-2.amazonaws.com
SMTP Port: 587 (TLS)
Authentication: Required
```

---

### ⏸️ Step 7: 서버 환경 변수 설정

#### 7-1. .env 파일 업데이트

**로컬 환경** (D:\Claude\Projects\Active\coinpulse\.env):
```bash
# AWS SES SMTP Configuration
SMTP_HOST=email-smtp.ap-northeast-2.amazonaws.com
SMTP_PORT=587
SMTP_USER=AKIAXXXXXXXXXXXXXXXXXX
SMTP_PASSWORD=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
SMTP_FROM_EMAIL=noreply@sinsi.ai
SMTP_FROM_NAME=CoinPulse
```

#### 7-2. 프로덕션 서버 업데이트

**SSH 접속**:
```bash
ssh root@158.247.222.216
```

**환경 변수 설정**:
```bash
cd /opt/coinpulse
nano .env
```

**.env 파일에 추가**:
```bash
# AWS SES SMTP Configuration
SMTP_HOST=email-smtp.ap-northeast-2.amazonaws.com
SMTP_PORT=587
SMTP_USER=AKIAXXXXXXXXXXXXXXXXXX
SMTP_PASSWORD=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
SMTP_FROM_EMAIL=noreply@sinsi.ai
SMTP_FROM_NAME=CoinPulse
```

**서비스 재시작**:
```bash
sudo systemctl restart coinpulse
sudo systemctl status coinpulse
```

---

### ⏸️ Step 8: 이메일 발송 테스트

#### 8-1. 테스트 스크립트 실행

**로컬 환경**:
```bash
cd D:\Claude\Projects\Active\coinpulse
python scripts/test_email.py
```

**옵션 선택**:
```
1. 간단한 텍스트 이메일 테스트
2. 시그널 알림 이메일 테스트 (HTML)
```

#### 8-2. 테스트 확인사항

- [ ] 이메일 발송 성공 (200 OK)
- [ ] 받은편지함에 도착 (스팸 폴더 확인)
- [ ] HTML 렌더링 정상
- [ ] 발신자 이름 표시: "CoinPulse <noreply@sinsi.ai>"
- [ ] 링크 클릭 가능

#### 8-3. 프로덕션 환경 테스트

**SSH 접속**:
```bash
ssh root@158.247.222.216
cd /opt/coinpulse
python scripts/test_email.py
```

---

## 모니터링 및 관리

### AWS SES 대시보드 확인

**확인 항목**:
- 일일 발송량 (Sending quota)
- Bounce rate (목표: <5%)
- Complaint rate (목표: <0.1%)
- 평판 점수 (Reputation metrics)

**접속 경로**:
AWS SES Console → Home → Account dashboard

### Bounce/Complaint 처리

**자동 처리** (backend/services/email_service.py에 이미 구현됨):
```python
# SNS 토픽 설정으로 자동 처리
# - Bounce: 이메일 주소 무효화
# - Complaint: 발송 중지 + 관리자 알림
```

### 발송 한도 증가 요청

**필요 시점**:
- 일일 발송량이 한도의 80% 초과 시

**신청 방법**:
AWS SES Console → Account Dashboard → Request a sending quota increase

---

## 트러블슈팅

### 문제 1: 도메인 인증 실패

**증상**: Status가 계속 "Pending"

**해결**:
1. DNS 레코드 오타 확인 (복사-붙여넣기 권장)
2. DNS 전파 대기 (최대 48시간)
3. nslookup으로 수동 확인

### 문제 2: SMTP 인증 실패

**증상**: "535 Authentication Credentials Invalid"

**해결**:
1. SMTP_USER, SMTP_PASSWORD 확인
2. AWS IAM에서 SMTP 자격증명 재생성
3. .env 파일 업데이트 후 서버 재시작

### 문제 3: 이메일이 스팸으로 분류

**해결**:
1. SPF, DKIM, DMARC 레코드 확인
2. 발신자 평판 모니터링
3. "구독 취소" 링크 추가
4. 스팸 트리거 단어 제거

### 문제 4: Production Access 거부

**해결**:
1. Use case를 더 자세히 작성
2. Opt-in 방식 명확히 설명
3. Bounce/complaint 처리 방법 추가
4. 재신청 (24시간 후)

---

## 비용 예상

### AWS SES 요금

**이메일 발송**:
- $0.10 / 1,000건
- 월 62,000건까지 무료 (AWS 프리티어)

**예상 사용량** (100명 기준):
```
일일 발송: 500건
월간 발송: 15,000건
월 비용: $0 (프리티어 범위 내)

일일 발송: 1,000건
월간 발송: 30,000건
월 비용: $0 (프리티어 범위 내)

일일 발송: 3,000건 (사용자 증가 시)
월간 발송: 90,000건
월 비용: $2.80 (28,000건 초과분)
```

### 비교: 타 서비스

| 서비스 | 월 비용 (30,000건 기준) | 비고 |
|--------|------------------------|------|
| AWS SES | $0 (프리티어) | 최저 비용 |
| Resend | $20 | 50,000건 포함 |
| Brevo | €25 | 20,000건 포함 |
| Mailgun | $35 | 50,000건 포함 |

---

## 체크리스트

### DNS 전파 전 (현재)

- [x] AWS SES 도메인 추가
- [x] DNS 레코드 6개 설정
- [ ] DNS 전파 확인 (10-30분 대기)

### DNS 전파 후

- [ ] AWS SES에서 도메인 인증 확인
- [ ] 5개 이메일 주소 추가
- [ ] Catch-All 또는 개별 메일박스 설정
- [ ] 인증 이메일 링크 클릭

### Production Access

- [ ] Production Access 신청
- [ ] 승인 대기 (24시간)
- [ ] SMTP 자격증명 생성

### 서버 설정

- [ ] .env 파일 업데이트 (로컬)
- [ ] .env 파일 업데이트 (프로덕션)
- [ ] 서비스 재시작
- [ ] 테스트 이메일 발송
- [ ] 프로덕션 환경 테스트

---

## 참고 링크

- [AWS SES 시작하기](https://docs.aws.amazon.com/ses/latest/dg/setting-up.html)
- [SMTP 자격증명 얻기](https://docs.aws.amazon.com/ses/latest/dg/smtp-credentials.html)
- [Production Access 신청](https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html)
- [이메일 인증 방법](https://docs.aws.amazon.com/ses/latest/dg/verify-email-addresses.html)

---

**작성일**: 2025-12-23
**최종 수정**: DNS 전파 대기 단계 (Step 3)
