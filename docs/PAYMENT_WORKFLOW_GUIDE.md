# CoinPulse 결제 시스템 가이드
**버전**: v2.0  
**업데이트**: 2025-12-10  
**방식**: 계좌이체 + 관리자 승인

---

## 🏦 결제 방식: 계좌이체

### **왜 계좌이체인가?**
- ⚠️ **Toss Payments 제약**: 암호화폐 거래 관련 서비스는 PG사 승인 제한
- ✅ **안전한 대안**: 은행 계좌이체 + 관리자 수동 승인
- ✅ **투명한 관리**: Admin Dashboard를 통한 체계적 승인 프로세스

---

## 💳 사용자 결제 프로세스

### **Step 1: 플랜 선택**
**위치**: `/dashboard.html` 또는 `/checkout.html`

**사용 가능 플랜**:
```
1. Free Plan (₩0/월)
   - 기본 차트 조회
   - 제한적 기능

2. Premium Plan (₩19,900/월)
   - 실시간 자동매매
   - 기술적 지표
   - 포트폴리오 추적

3. Pro Plan (₩49,900/월)
   - Premium 모든 기능
   - 고급 전략
   - 우선 지원
```

### **Step 2: 결제 요청 생성**
**API**: `POST /api/payment-requests`

**필수 정보**:
```json
{
  "plan_code": "premium",
  "duration_days": 30,
  "bank_info": "국민은행 123-456-789 홍길동"
}
```

**자동 생성**:
- `payment_code`: 고유 결제 코드 (예: PAY-20251210-ABCD1234)
- `amount`: 플랜별 금액 자동 계산
- `status`: "pending" (대기 중)

### **Step 3: 계좌이체 실행**
**입금 계좌**:
```
은행: 국민은행
계좌번호: 123-456-789012
예금주: (주)신시AI
입금자명: [결제코드] 또는 [이메일]
```

**입금액**:
- Premium: ₩19,900
- Pro: ₩49,900

**입금 시 필수**:
- 입금자명에 결제코드 또는 이메일 포함
- 정확한 금액 입금

### **Step 4: 결제 확인 대기**
**소요 시간**: 영업일 기준 1-2일
**확인 방법**: 
- 이메일 알림 (승인 시)
- Dashboard에서 구독 상태 확인

---

## 👨‍💼 관리자 승인 프로세스

### **Admin Dashboard 접근**
**URL**: https://coinpulse.sinsi.ai/admin.html  
**토큰**: `coinpulse_admin_2024_secure_token`

### **승인 워크플로우**

#### **1단계: 결제 요청 확인**
```
Payments 탭 → Pending 필터
- 사용자 이메일 확인
- 결제 코드 확인
- 플랜 및 금액 확인
- 입금자 정보 확인
```

#### **2단계: 은행 계좌 확인**
```
실제 은행 계좌에 입금 확인:
- 입금자명에 결제코드 또는 이메일 포함 여부
- 입금 금액 일치 여부
- 입금 날짜 확인
```

#### **3단계: 승인 처리**
**API**: `POST /api/admin/payment-requests/{id}/approve`

**승인 시 자동 처리**:
```
1. payment_requests 테이블
   - status: pending → approved
   - approved_at: 현재 시각
   - approved_by: 관리자 ID/이메일

2. user_subscriptions 테이블
   - 새 구독 레코드 생성
   - plan_code: 선택한 플랜
   - status: active
   - started_at: 승인 시각
   - expires_at: started_at + duration_days

3. 사용자에게 이메일 발송 (향후 구현)
   - 승인 완료 알림
   - 구독 활성화 안내
```

#### **4단계: 거절 처리 (필요시)**
**API**: `POST /api/admin/payment-requests/{id}/reject`

**거절 사유**:
- 입금 확인 불가
- 금액 불일치
- 입금자 정보 불명확

**거절 시 처리**:
```
1. payment_requests 테이블
   - status: pending → rejected
   - notes: 거절 사유 기록

2. 사용자에게 이메일 발송 (권장)
   - 거절 사유 설명
   - 재신청 안내
```

---

## 🔄 구독 관리

### **구독 활성화**
**테이블**: `user_subscriptions`

**필드**:
```sql
- plan_code: free/premium/pro
- status: active/cancelled/expired
- started_at: 시작일
- expires_at: 만료일
- auto_renew: false (수동 갱신)
```

### **구독 갱신**
**방식**: 수동 갱신 (자동 결제 없음)

**프로세스**:
1. 만료 7일 전 이메일 알림
2. 사용자가 새 결제 요청 생성
3. 계좌이체 실행
4. 관리자 승인 → 구독 연장

### **구독 취소**
**사용자 요청 시**:
```
1. 관리자에게 취소 요청 이메일
2. 관리자가 user_subscriptions 업데이트
   - status: cancelled
   - 만료일까지는 서비스 이용 가능
```

---

## 📊 데이터베이스 스키마

### **payment_requests 테이블**
```sql
CREATE TABLE payment_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    email VARCHAR(255) NOT NULL,
    payment_code VARCHAR(50) UNIQUE NOT NULL,
    plan_code VARCHAR(20) NOT NULL,
    amount INTEGER NOT NULL,
    duration_days INTEGER DEFAULT 30,
    status VARCHAR(20) DEFAULT 'pending',
    bank_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by VARCHAR(255),
    notes TEXT
);
```

### **user_subscriptions 테이블**
```sql
CREATE TABLE user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    plan_code VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    started_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    auto_renew BOOLEAN DEFAULT FALSE,
    payment_method VARCHAR(50) DEFAULT 'bank_transfer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔐 보안 고려사항

### **결제 코드 생성**
```python
# 예시: PAY-20251210-ABCD1234
import secrets
payment_code = f"PAY-{datetime.now():%Y%m%d}-{secrets.token_hex(4).upper()}"
```

### **승인 권한**
- Admin 토큰 필수: `ADMIN_TOKEN` 환경 변수
- HTTPS 통신 필수
- 로그 기록 (승인/거절 이력)

### **사용자 데이터 보호**
- 은행 계좌 정보는 암호화 저장 (권장)
- 결제 코드로 개인정보 노출 최소화

---

## 📧 이메일 알림 시스템 (향후 구현)

### **필요한 이메일**
1. **결제 요청 생성 시**
   - 제목: [CoinPulse] 결제 요청이 생성되었습니다
   - 내용: 결제 코드, 입금 계좌, 입금액

2. **승인 완료 시**
   - 제목: [CoinPulse] 구독이 활성화되었습니다
   - 내용: 플랜, 시작일, 만료일

3. **만료 예정 알림**
   - 제목: [CoinPulse] 구독이 곧 만료됩니다
   - 내용: 만료일, 갱신 방법

4. **거절 시**
   - 제목: [CoinPulse] 결제 요청이 거절되었습니다
   - 내용: 거절 사유, 재신청 방법

### **이메일 서비스 추천**
- SendGrid
- AWS SES
- Mailgun

---

## 🔧 API 엔드포인트 요약

### **사용자용 API**
```
POST   /api/payment-requests          - 결제 요청 생성
GET    /api/payment-requests/my       - 내 결제 요청 조회
GET    /api/subscription/status       - 구독 상태 조회
```

### **관리자용 API**
```
GET    /api/admin/payment-requests    - 전체 결제 요청 조회
GET    /api/admin/payment-requests?status=pending  - 대기 중 조회
POST   /api/admin/payment-requests/{id}/approve   - 승인
POST   /api/admin/payment-requests/{id}/reject    - 거절
GET    /api/admin/users               - 사용자 조회
PUT    /api/admin/users/{id}/subscription        - 구독 수정
```

---

## 📋 체크리스트

### **초기 설정**
- [x] payment_requests 테이블 생성
- [x] user_subscriptions 테이블 생성
- [x] Admin Dashboard 구현
- [x] 승인/거절 API 구현
- [ ] 이메일 알림 시스템 (선택)

### **운영 준비**
- [ ] 실제 은행 계좌 개설
- [ ] 입금 확인 프로세스 수립
- [ ] 관리자 교육 (승인 절차)
- [ ] 고객 안내 페이지 작성

### **법적 준비**
- [ ] 이용약관 작성
- [ ] 환불 정책 수립
- [ ] 개인정보 처리방침
- [ ] 결제 대행 신고 (필요시)

---

## 🚀 향후 개선 방향

### **Phase 1: 현재 (수동 승인)**
- ✅ 계좌이체 + 관리자 수동 승인
- ✅ Admin Dashboard 관리

### **Phase 2: 반자동화 (3개월 후)**
- [ ] 이메일 알림 자동화
- [ ] 입금 확인 반자동화 (오픈뱅킹 API)
- [ ] 구독 만료 자동 알림

### **Phase 3: 완전 자동화 (6개월 후)**
- [ ] PG사 승인 재시도
- [ ] 자동 정기결제
- [ ] 완전 무인 운영

---

## 💡 FAQ

### Q1. 토스페이먼츠는 왜 안 되나요?
**A**: 암호화폐 거래 관련 서비스는 대부분의 한국 PG사가 승인을 제한합니다. 계좌이체 방식이 현재 가장 안전한 대안입니다.

### Q2. 자동 결제는 불가능한가요?
**A**: 현재는 수동 갱신만 가능합니다. 향후 오픈뱅킹 API 또는 암호화폐 친화적 PG사를 통해 자동화를 검토 중입니다.

### Q3. 환불은 어떻게 하나요?
**A**: 서비스 시작 7일 이내 전액 환불 가능 (이용약관에 명시 필요). 관리자에게 이메일로 요청하세요.

### Q4. 영수증은 어떻게 받나요?
**A**: 승인 완료 시 이메일로 영수증 발송 (향후 자동화). 필요시 관리자에게 별도 요청하세요.

---

**문서 버전**: 2.0  
**최종 수정**: 2025-12-10  
**작성자**: Claude (Mari)  
**검토**: 필요 (마스터 확인 필요)