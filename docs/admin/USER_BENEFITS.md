====================================
User Benefits System - Complete Guide
범용 사용자 혜택 관리 시스템
====================================

✅ COMPLETE! Enhanced benefit system created.

====================================
📋 SYSTEM OVERVIEW
====================================

BetaTester (베타 테스터):
- 초기 베타 테스터 전용
- 간단한 관리
- 레거시 호환성

UserBenefit (범용 혜택):
- 모든 종류의 혜택 관리
- 쿠폰, 프로모션, 이벤트, VIP 등
- 중복 적용, 우선순위, 사용 제한
- ⭐ 베타 이후에도 계속 사용 가능

====================================
💡 BENEFIT CATEGORIES
====================================

1️⃣ beta_tester - 베타 테스터 특전
   - 초기 사용자 혜택
   - 장기 무료 사용권

2️⃣ promotion - 프로모션
   - 런칭 이벤트
   - 시즌 할인
   - 마케팅 캠페인

3️⃣ coupon - 쿠폰
   - 개별 발급 코드
   - 1회/다회 사용
   - 추천인 리워드

4️⃣ event - 이벤트 보상
   - 특정 이벤트 참여자
   - 임시 혜택

5️⃣ vip - VIP 멤버십
   - 특별 회원 전용
   - 프리미엄 기능 해제

6️⃣ referral - 추천인 리워드
   - 친구 초대 보상
   - 양방향 혜택

====================================
🎁 BENEFIT TYPES
====================================

free_trial:
- 무료 체험 기간 연장
- value = 일수 (30, 60, 90...)

discount:
- 결제 할인
- value = 퍼센트 (10, 20, 50, 100)
- stackable = true면 중복 적용 가능

credit:
- 크레딧 지급
- value = 금액 (원)

upgrade:
- 플랜 업그레이드
- Free → Premium → Pro

feature_unlock:
- 특정 기능 해제
- applicable_to에 기능 명시

====================================
🔧 API ENDPOINTS
====================================

Basic CRUD:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET    /api/admin/benefits
       ?category=promotion
       &status=active
       &email=user@example.com

POST   /api/admin/benefits
PUT    /api/admin/benefits/:id
DELETE /api/admin/benefits/:id

Advanced Features:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST   /api/admin/benefits/bulk
       대량 혜택 생성

POST   /api/admin/benefits/expire
       만료된 혜택 일괄 처리

GET    /api/admin/benefits/stats
       통계 조회

GET    /api/admin/benefits/user/:email
       사용자별 혜택 조회

====================================
💻 USAGE EXAMPLES
====================================

Example 1: 베타 테스터에게 90일 무료
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST /api/admin/benefits
{
  "email": "beta@example.com",
  "category": "beta_tester",
  "code": "BETA2024",
  "benefit_type": "free_trial",
  "benefit_value": 90,
  "applicable_to": "all",
  "title": "Beta Tester - 90 Days Free",
  "stackable": false,
  "priority": 10
}

Example 2: 런칭 프로모션 50% 할인
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST /api/admin/benefits
{
  "email": "customer@example.com",
  "category": "promotion",
  "code": "LAUNCH50",
  "benefit_type": "discount",
  "benefit_value": 50,
  "applicable_to": "all",
  "title": "Launch Promotion - 50% OFF",
  "duration_days": 30,
  "usage_limit": 1,
  "stackable": true,
  "priority": 20
}

Example 3: 100명에게 쿠폰 대량 발급
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST /api/admin/benefits/bulk
{
  "emails": ["user1@ex.com", "user2@ex.com", ...],
  "category": "coupon",
  "generate_codes": true,
  "code_prefix": "SUMMER",
  "benefit_type": "discount",
  "benefit_value": 30,
  "applicable_to": "premium",
  "duration_days": 60,
  "usage_limit": 1,
  "title": "Summer Sale - 30% OFF Premium"
}

Example 4: VIP 회원에게 Pro 업그레이드
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST /api/admin/benefits
{
  "email": "vip@example.com",
  "category": "vip",
  "benefit_type": "upgrade",
  "applicable_to": "pro",
  "title": "VIP Membership - Pro Access",
  "description": "Exclusive VIP access to Pro features",
  "duration_days": 365,
  "stackable": false,
  "priority": 5
}

====================================
🔍 CODE INTEGRATION
====================================

결제 시 혜택 적용:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from backend.models import UserBenefit

def calculate_price(user_email, plan_type, base_price):
    # 활성 혜택 조회
    benefits = UserBenefit.get_active_benefits(user_email)
    
    # 무료 체험 확인
    for benefit in benefits:
        if benefit.benefit_type == 'free_trial':
            return 0  # 무료!
    
    # 할인 계산 (중복 가능)
    total_discount = UserBenefit.calculate_total_discount(
        user_email, 
        plan_type
    )
    
    # 최종 가격
    final_price = base_price * (100 - total_discount) / 100
    
    return final_price

사용자 혜택 확인:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def check_user_benefits(user_email):
    active_benefits = UserBenefit.get_active_benefits(user_email)
    
    has_free_trial = any(
        b.benefit_type == 'free_trial' 
        for b in active_benefits
    )
    
    has_discount = any(
        b.benefit_type == 'discount' 
        for b in active_benefits
    )
    
    return {
        'has_benefits': len(active_benefits) > 0,
        'free_trial': has_free_trial,
        'discount': has_discount,
        'benefits': [b.to_dict() for b in active_benefits]
    }

혜택 사용 처리:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def apply_benefit(user_email, benefit_id):
    success = UserBenefit.apply_benefit(user_email, benefit_id)
    
    if success:
        # 혜택 적용 성공
        # 사용 횟수 자동 증가
        # 사용 제한 도달 시 자동 'used' 상태로 변경
        return True
    else:
        # 혜택 사용 불가 (이미 사용/만료/권한 없음)
        return False

====================================
🗓️ AUTO EXPIRATION
====================================

만료 자동 처리:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cron job으로 매일 실행
POST /api/admin/benefits/expire

# 또는 Python으로:
from backend.database import db
result = db.session.execute(
    db.text("SELECT expire_user_benefits()")
)
expired_count = result.scalar()

====================================
📊 STATISTICS & MONITORING
====================================

전체 통계:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET /api/admin/benefits/stats

Returns:
{
  "total": 150,
  "active": 100,
  "used": 30,
  "expired": 20,
  "by_category": {
    "beta_tester": 10,
    "promotion": 80,
    "coupon": 40,
    "vip": 20
  },
  "by_type": {
    "free_trial": 30,
    "discount": 100,
    "upgrade": 20
  }
}

사용자별 조회:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET /api/admin/benefits/user/user@example.com

Returns:
{
  "email": "user@example.com",
  "all_benefits": [...],
  "active_benefits": [...],
  "total_discount": 50,  // %
  "count": {
    "total": 5,
    "active": 2
  }
}

====================================
🔐 SECURITY
====================================

✅ Admin token required for all endpoints
✅ User email validation
✅ SQL injection prevention (SQLAlchemy)
✅ Automatic status management
✅ Usage limit enforcement
✅ End date validation

====================================
📦 INSTALLATION STEPS
====================================

1. Upload new files:
   - backend/models/user_benefit.py
   - backend/routes/benefits_admin.py
   - backend/migrations/003_add_user_benefits.sql
   - backend/models/__init__.py (updated)
   - app.py (updated)

2. Run migration:
   ssh root@158.247.222.216
   cd /opt/coinpulse
   psql -U postgres -d coinpulse -f backend/migrations/003_add_user_benefits.sql

3. Restart service:
   systemctl restart coinpulse

4. Test API:
   curl -H "Authorization: Bearer coinpulse_admin_2024_secure_token" \
        http://coinpulse.sinsi.ai/api/admin/benefits/stats

====================================
✅ BENEFITS SUMMARY
====================================

✅ 베타 테스터 → 계속 사용 가능한 범용 시스템
✅ 다양한 혜택 타입 (무료, 할인, 업그레이드...)
✅ 카테고리별 관리 (프로모션, 쿠폰, VIP...)
✅ 중복 적용 가능 (stackable)
✅ 우선순위 시스템
✅ 사용 횟수 제한
✅ 자동 만료 처리
✅ 대량 발급 기능
✅ 통계 및 모니터링
✅ 간단한 API 통합

====================================

🚀 이제 베타 이후에도 계속 사용할 수 있는
   완전한 혜택 관리 시스템이 준비되었습니다!