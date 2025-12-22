# Cloudflare DNS 설정 가이드

## 개요

hosting.kr DNS 제한 문제로 인해 Cloudflare로 DNS 관리를 이전합니다.

**소요 시간**: 초기 설정 30분 + DNS 전파 1-24시간

---

## Step 1: Cloudflare 계정 생성 (5분)

### 1-1. 회원가입

1. **브라우저에서 접속**: https://dash.cloudflare.com/sign-up
2. **이메일 주소** 입력
3. **비밀번호** 설정 (8자 이상)
4. **Create Account** 클릭
5. 이메일 인증 링크 클릭

### 1-2. 로그인

- 계정 생성 후 자동 로그인됨
- 대시보드 화면 표시

---

## Step 2: 도메인 추가 (10분)

### 2-1. 사이트 추가

1. Cloudflare 대시보드 홈 화면
2. **Add a Site** 버튼 클릭
3. 도메인 입력: `sinsi.ai`
4. **Add site** 클릭

### 2-2. 플랜 선택

1. **Free** 플랜 선택 (무료)
2. **Continue** 클릭

### 2-3. DNS 레코드 스캔

- Cloudflare가 자동으로 기존 DNS 레코드 스캔 (1-2분)
- 스캔 완료 후 기존 레코드 목록 표시

### 2-4. DNS 레코드 확인

**자동 스캔된 레코드 확인**:
- A 레코드: @ → 216.198.79.1
- A 레코드: admin → 158.247.222.216
- A 레코드: coinpulse → 158.247.222.216
- CNAME: www → eefa174e264dc16d.vercel-dns-017.com
- MX: mail → feedback-smtp.ap-northeast-2.amazonses.com

**누락된 레코드는 Step 3에서 수동 추가합니다.**

**Continue** 클릭

---

## Step 3: 네임서버 정보 확인 (2분)

### 3-1. Cloudflare 네임서버 확인

Cloudflare가 2개의 네임서버를 제공합니다:

**예시** (실제 값은 다를 수 있음):
```
alice.ns.cloudflare.com
bob.ns.cloudflare.com
```

⚠️ **중요**: 이 값을 **메모장에 복사**하세요! (다음 단계에서 사용)

**화면은 그대로 두고** hosting.kr 사이트로 이동

---

## Step 4: hosting.kr 네임서버 변경 (5분)

### 4-1. hosting.kr 로그인

1. https://www.hosting.kr 접속
2. 로그인

### 4-2. 도메인 관리

1. **도메인 관리** 메뉴 클릭
2. **sinsi.ai** 선택
3. **네임서버 설정** 또는 **DNS 관리** 클릭

### 4-3. 네임서버 변경

**현재 네임서버**:
```
ns1.hosting.co.kr
ns2.hosting.co.kr
```

**Cloudflare 네임서버로 변경**:
```
alice.ns.cloudflare.com  (예시 - 실제 값 사용)
bob.ns.cloudflare.com    (예시 - 실제 값 사용)
```

### 4-4. 저장

- **저장** 또는 **변경** 버튼 클릭
- 확인 메시지: "네임서버가 변경되었습니다"

⚠️ **DNS 전파 시작**: 1-24시간 소요 (보통 1-4시간)

---

## Step 5: Cloudflare로 돌아가기 (1분)

### 5-1. 네임서버 변경 확인

1. Cloudflare 화면으로 돌아가기
2. "네임서버 변경을 완료했습니다" 체크
3. **Done, check nameservers** 클릭

### 5-2. 대기 화면

- Cloudflare가 네임서버 변경 확인 중
- 상태: "Pending Nameserver Update"
- 이메일로 완료 알림 발송 (1-24시간 내)

⚠️ **이 단계에서는 기다리지 말고 Step 6으로 진행하세요!**

---

## Step 6: DNS 레코드 추가 (중요!) (10분)

네임서버 전파를 기다리는 동안 DNS 레코드를 미리 설정합니다.

### 6-1. DNS 관리 화면 이동

1. Cloudflare 대시보드 → **sinsi.ai** 선택
2. 왼쪽 메뉴 → **DNS** → **Records** 클릭

### 6-2. 기존 레코드 확인

자동 스캔된 레코드가 표시됩니다.

### 6-3. AWS SES DKIM 레코드 추가 (3개)

**+ Add record** 버튼을 3번 클릭하여 추가:

#### DKIM 레코드 1
```
Type: CNAME
Name: h64gdqcz0popfrentfrvai4otg3owt2it._domainkey
Target: h64gdqcz0popfrentfrvai4otg3owt2it.dkim.amazonses.com
Proxy status: DNS only (회색 구름)
TTL: Auto
```

#### DKIM 레코드 2
```
Type: CNAME
Name: w6326ii2g7aihgh2qczgh3og5zacc4us._domainkey
Target: w6326ii2g7aihgh2qczgh3og5zacc4us.dkim.amazonses.com
Proxy status: DNS only (회색 구름)
TTL: Auto
```

#### DKIM 레코드 3
```
Type: CNAME
Name: z3xewb2y2bpsuji5qglhxvwxu6gzhm6d._domainkey
Target: z3xewb2y2bpsuji5qglhxvwxu6gzhm6d.dkim.amazonses.com
Proxy status: DNS only (회색 구름)
TTL: Auto
```

⚠️ **중요**: Proxy status를 **DNS only**로 설정 (회색 구름 아이콘)

### 6-4. SPF TXT 레코드 추가

```
Type: TXT
Name: mail.sinsi.ai
Content: v=spf1 include:amazonses.com ~all
TTL: Auto
```

### 6-5. DMARC TXT 레코드 추가

```
Type: TXT
Name: _dmarc
Content: v=DMARC1; p=none;
TTL: Auto
```

### 6-6. MX 레코드 확인/추가

스캔에서 누락되었으면 수동 추가:

```
Type: MX
Name: mail
Mail server: feedback-smtp.ap-northeast-2.amazonses.com
Priority: 10
TTL: Auto
```

### 6-7. 전체 DNS 레코드 확인

**총 10개 레코드가 있어야 합니다**:

| Type | Name | Target/Content |
|------|------|----------------|
| A | @ | 216.198.79.1 |
| A | admin | 158.247.222.216 |
| A | coinpulse | 158.247.222.216 |
| CNAME | www | eefa174e264dc16d.vercel-dns-017.com |
| CNAME | h64gdqcz0popfentfrvai4otg3owt2it._domainkey | h64gdqcz0popfrentfrvai4otg3owt2it.dkim.amazonses.com |
| CNAME | w6326ii2g7aihgh2qczgh3og5zacc4us._domainkey | w6326ii2g7aihgh2qczgh3og5zacc4us.dkim.amazonses.com |
| CNAME | z3xewb2y2bpsuji5qglhxvwxu6gzhm6d._domainkey | z3xewb2y2bpsuji5qglhxvwxu6gzhm6d.dkim.amazonses.com |
| MX | mail | feedback-smtp.ap-northeast-2.amazonses.com (10) |
| TXT | mail.sinsi.ai | v=spf1 include:amazonses.com ~all |
| TXT | _dmarc | v=DMARC1; p=none; |

---

## Step 7: 네임서버 전파 대기 (1-24시간)

### 7-1. 전파 확인 방법

**터미널에서 확인**:
```cmd
nslookup -type=NS sinsi.ai
```

**전파 전**:
```
Server: ns1.hosting.co.kr
```

**전파 후**:
```
Server: alice.ns.cloudflare.com
Server: bob.ns.cloudflare.com
```

### 7-2. Cloudflare 상태 확인

- Cloudflare 대시보드 → sinsi.ai
- 상태: "Pending" → "Active" (전파 완료 시)
- 이메일 알림: "sinsi.ai is now active on Cloudflare"

### 7-3. 전파 완료까지 예상 시간

- **최소**: 1시간
- **평균**: 4시간
- **최대**: 24시간

---

## Step 8: AWS SES 도메인 인증 확인 (전파 후)

### 8-1. DKIM 레코드 확인

**네임서버 전파 완료 후 테스트**:

```cmd
nslookup -type=CNAME h64gdqcz0popfrentfrvai4otg3owt2it._domainkey.sinsi.ai
nslookup -type=CNAME w6326ii2g7aihgh2qczgh3og5zacc4us._domainkey.sinsi.ai
nslookup -type=CNAME z3xewb2y2bpsuji5qglhxvwxu6gzhm6d._domainkey.sinsi.ai
```

**예상 결과**:
```
Name: h64gdqcz0popfrentfrvai4otg3owt2it._domainkey.sinsi.ai
Canonical name: h64gdqcz0popfrentfrvai4otg3owt2it.dkim.amazonses.com
```

### 8-2. AWS SES Console 확인

1. **AWS SES Console** 접속
2. **Verified identities** → **sinsi.ai** 클릭
3. **DKIM 상태 확인**:
   - Status: "Pending" → "Verified" ✅
   - 3개 CNAME 레코드 모두 초록색 체크

### 8-3. 도메인 인증 완료

- Identity status: "Verified" ✅
- DKIM: "Successful" ✅
- 이제 이메일 발송 가능!

---

## Step 9: 이메일 주소 인증 (AWS SES)

### 9-1. 이메일 주소 추가

AWS SES Console → **Verified identities** → **Create identity**

**Email address 선택** 후 5개 추가:
```
1. noreply@sinsi.ai
2. alerts@sinsi.ai
3. support@sinsi.ai
4. admin@sinsi.ai
5. billing@sinsi.ai
```

### 9-2. 인증 이메일 수신

각 주소로 AWS 인증 이메일 발송됨:
- 제목: "Amazon SES Email Address Verification Request"
- 링크 클릭하여 인증 완료

⚠️ **hosting.kr Catch-All 설정 필요** (모든 이메일을 Gmail로 포워딩)

---

## Step 10: Production Access 신청

### 10-1. 신청

AWS SES Console → **Account Dashboard** → **Request production access**

**Use case 작성**:
```
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

### 10-2. 심사 대기

- 심사 기간: 24시간 (영업일 기준)
- 결과 이메일 발송

---

## 트러블슈팅

### 문제 1: 네임서버 변경이 안 됨

**해결**:
1. hosting.kr 고객센터 전화 (1588-2120)
2. "Cloudflare 네임서버로 변경 요청"

### 문제 2: DNS 레코드가 조회 안 됨

**원인**: 네임서버 전파 미완료

**해결**:
1. `nslookup -type=NS sinsi.ai`로 전파 확인
2. Cloudflare 네임서버로 변경되었는지 확인

### 문제 3: DKIM 레코드 오류

**확인**:
- Cloudflare DNS 레코드에서 오타 확인
- Proxy status가 "DNS only"인지 확인
- Target 끝에 `.` 없는지 확인

---

## 체크리스트

### 초기 설정 (즉시)

- [ ] Cloudflare 계정 생성
- [ ] sinsi.ai 도메인 추가
- [ ] Cloudflare 네임서버 확인 (메모)
- [ ] hosting.kr 네임서버 변경
- [ ] Cloudflare DNS 레코드 추가 (10개)

### 전파 대기 (1-24시간)

- [ ] 네임서버 전파 확인 (nslookup)
- [ ] Cloudflare 상태 "Active" 확인
- [ ] DKIM 레코드 조회 테스트

### AWS SES 설정 (전파 후)

- [ ] AWS SES 도메인 인증 확인
- [ ] 5개 이메일 주소 인증
- [ ] Production Access 신청
- [ ] SMTP 자격증명 생성
- [ ] 서버 .env 파일 업데이트
- [ ] 테스트 이메일 발송

---

## 참고 링크

- [Cloudflare 시작하기](https://developers.cloudflare.com/dns/zone-setups/full-setup/)
- [Cloudflare DNS 관리](https://developers.cloudflare.com/dns/manage-dns-records/how-to/create-dns-records/)
- [AWS SES with Cloudflare](https://docs.aws.amazon.com/ses/latest/dg/dns-txt-records.html)

---

**작성일**: 2025-12-23
**목적**: hosting.kr DNS 제한 문제 해결
**예상 완료**: 24시간 이내
