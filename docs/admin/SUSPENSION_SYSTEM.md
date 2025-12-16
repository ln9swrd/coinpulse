====================================
User Suspension System - Complete Guide
사용자 이용 정지 관리 시스템
====================================

✅ COMPLETE! User suspension management system created.

====================================
📋 SYSTEM OVERVIEW
====================================

Purpose:
사용자의 서비스 이용을 제한하거나 차단하는 시스템

Use Cases:
- 약관 위반 사용자 차단
- 부정 행위 방지
- 결제 문제 사용자 제한
- 보안 이슈 대응
- 임시/영구 정지

====================================
🚫 SUSPENSION TYPES
====================================

1️⃣ account - 계정 완전 차단
   - 로그인 불가
   - 모든 기능 차단
   - 가장 강력한 제재

2️⃣ trading - 자동매매 차단
   - 로그인은 가능
   - 거래 기능만 차단
   - 조회/설정은 가능

3️⃣ payment - 결제 차단
   - 새로운 결제 불가
   - 구독 갱신 차단
   - 환불 요청 대기

4️⃣ withdrawal - 출금 차단
   - 보안 이슈 시
   - 자금 이동 제한
   - 입금은 가능

5️⃣ feature - 특정 기능 차단
   - 일부 기능만 제한
   - 나머지는 정상 사용

====================================
⚖️ SEVERITY LEVELS
====================================

warning - 경고
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 첫 위반 시
- 경고 메시지만 표시
- 기능 제한 없음

temporary - 일시 정지
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 기간 제한 (7일, 30일 등)
- 기간 만료 시 자동 해제
- 2차 위반 시

permanent - 영구 정지
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 해제 불가 (관리자만 가능)
- 중대한 위반 시
- 반복 위반자

====================================
📝 SUSPENSION REASONS
====================================

abuse - 서비스 악용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- API 과도한 호출
- 시스템 부하 유발
- 자동화 남용

fraud - 부정 행위
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 허위 정보 제공
- 불법 거래
- 조작 시도

violation - 약관 위반
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 이용약관 위반
- 정책 무시
- 금지된 행위

security - 보안 이슈
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 계정 해킹 의심
- 비정상 접근 패턴
- 보안 위협

payment_issue - 결제 문제
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 결제 실패 반복
- 환불 요청 중
- 분쟁 발생

manual - 관리자 수동 조치
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 특별한 사유
- 고객 요청
- 기타

====================================
🔧 API ENDPOINTS
====================================

Basic CRUD:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET    /api/admin/suspensions
       ?status=active
       &email=user@example.com
       &type=trading

POST   /api/admin/suspensions
       (Create suspension)

PUT    /api/admin/suspensions/:id
       (Update suspension info)

DELETE /api/admin/suspensions/:id
       (Delete suspension record)

Suspension Management:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST   /api/admin/suspensions/:id/lift
       (Lift/remove suspension)

POST   /api/admin/suspensions/check
       (Check if user is suspended)

User Specific:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET    /api/admin/suspensions/user/:email
       (Get all suspensions for user)

Utilities:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST   /api/admin/suspensions/expire
       (Auto-expire temporary suspensions)

GET    /api/admin/suspensions/stats
       (Get statistics)

====================================
💻 USAGE EXAMPLES
====================================

Example 1: 계정 일시 정지 (7일)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST /api/admin/suspensions
{
  "email": "violator@example.com",
  "suspension_type": "account",
  "severity": "temporary",
  "reason": "violation",
  "description": "약관 위반 - 부적절한 거래",
  "duration_days": 7,
  "suspended_by": "admin1"
}

Response:
{
  "success": true,
  "suspension": {
    "id": 1,
    "email": "violator@example.com",
    "suspension_type": "account",
    "severity": "temporary",
    "reason": "violation",
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-01-08T00:00:00Z",
    "status": "active"
  }
}

Example 2: 자동매매 영구 차단
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST /api/admin/suspensions
{
  "email": "abuser@example.com",
  "suspension_type": "trading",
  "severity": "permanent",
  "reason": "abuse",
  "description": "과도한 API 호출로 시스템 부하 유발",
  "suspended_by": "admin2"
}

Example 3: 정지 해제
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST /api/admin/suspensions/1/lift
{
  "lifted_by": "admin1"
}

Response:
{
  "success": true,
  "suspension": {
    "id": 1,
    "status": "lifted",
    "lifted_by": "admin1",
    "lifted_at": "2025-01-05T00:00:00Z"
  }
}

Example 4: 사용자 정지 여부 확인
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST /api/admin/suspensions/check
{
  "email": "user@example.com",
  "feature": "trading"
}

Response:
{
  "success": true,
  "email": "user@example.com",
  "feature": "trading",
  "is_suspended": true,
  "can_access": false,
  "active_suspensions": [...]
}

Example 5: 사용자의 모든 정지 내역
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET /api/admin/suspensions/user/user@example.com

Response:
{
  "success": true,
  "email": "user@example.com",
  "all_suspensions": [...],
  "active_suspensions": [...],
  "count": {
    "total": 3,
    "active": 1
  },
  "can_access": {
    "account": true,
    "trading": false,
    "payment": true,
    "withdrawal": true
  }
}

====================================
🔍 CODE INTEGRATION
====================================

로그인 시 체크:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from backend.models import UserSuspension

def login(email, password):
    # 계정 정지 확인
    if UserSuspension.is_suspended(email, 'account'):
        suspensions = UserSuspension.get_active_suspensions(email)
        suspension = suspensions[0]
        
        return {
            'success': False,
            'error': 'Account suspended',
            'reason': suspension.reason,
            'end_date': suspension.end_date
        }
    
    # 정상 로그인 처리
    ...

거래 실행 전 체크:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def execute_trade(user_email, trade_data):
    # 거래 권한 확인
    if not UserSuspension.can_access(user_email, 'trading'):
        return {
            'success': False,
            'error': 'Trading suspended'
        }
    
    # 거래 실행
    ...

결제 처리 전 체크:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def process_payment(user_email, amount):
    # 결제 권한 확인
    if not UserSuspension.can_access(user_email, 'payment'):
        return {
            'success': False,
            'error': 'Payment suspended',
            'message': '결제가 제한되었습니다. 고객센터에 문의하세요.'
        }
    
    # 결제 처리
    ...

전체 기능 접근 확인:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def check_user_access(user_email):
    return {
        'account': UserSuspension.can_access(user_email, 'account'),
        'trading': UserSuspension.can_access(user_email, 'trading'),
        'payment': UserSuspension.can_access(user_email, 'payment'),
        'withdrawal': UserSuspension.can_access(user_email, 'withdrawal')
    }

====================================
⚙️ AUTO EXPIRATION
====================================

자동 만료 처리:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cron job으로 매일 실행
POST /api/admin/suspensions/expire

# 또는 Python으로:
from backend.database import db
result = db.session.execute(
    db.text("SELECT expire_user_suspensions()")
)
expired_count = result.scalar()
print(f"{expired_count} suspensions expired")

====================================
📊 STATISTICS & MONITORING
====================================

전체 통계:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET /api/admin/suspensions/stats

Returns:
{
  "total": 50,
  "active": 20,
  "lifted": 25,
  "expired": 5,
  "by_type": {
    "account": 10,
    "trading": 30,
    "payment": 10
  },
  "by_reason": {
    "abuse": 15,
    "violation": 20,
    "fraud": 15
  },
  "by_severity": {
    "warning": 10,
    "temporary": 30,
    "permanent": 10
  }
}

====================================
🔒 SECURITY & BEST PRACTICES
====================================

✅ Admin token required for all endpoints
✅ Automatic expiration of temporary suspensions
✅ Audit trail (suspended_by, lifted_by)
✅ Status tracking (active, lifted, expired)
✅ Soft delete (lift instead of delete)

Best Practices:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Always document reason clearly
2. Use lift instead of delete
3. Start with warning before temporary
4. Reserve permanent for serious violations
5. Review suspensions regularly
6. Auto-expire temporary suspensions daily

====================================
📦 INSTALLATION
====================================

Files uploaded:
✅ backend/models/user_suspension.py
✅ backend/routes/suspension_admin.py
✅ backend/migrations/004_add_user_suspensions.sql

Run migration:
ssh root@158.247.222.216
cd /opt/coinpulse
psql -U postgres -d coinpulse -f backend/migrations/004_add_user_suspensions.sql

Restart service:
systemctl restart coinpulse

Test:
curl -H "Authorization: Bearer coinpulse_admin_2024_secure_token" \
     http://coinpulse.sinsi.ai/api/admin/suspensions/stats

====================================
✅ SUMMARY
====================================

Created: Complete user suspension system
Purpose: Service access control and moderation
Types: 5 suspension types (account, trading, payment, withdrawal, feature)
Severity: 3 levels (warning, temporary, permanent)
Reasons: 6 categories (abuse, fraud, violation, security, payment, manual)
API: 10 endpoints with full management
Integration: Simple can_access() checks
Security: Admin-only with audit trail

🚀 System ready for deployment!

Run: upload_complete_admin.bat

====================================