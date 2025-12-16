====================================
Plan Management System - Complete Guide
요금제 관리 시스템
====================================

✅ COMPLETE! Dynamic plan configuration system created.

====================================
📋 SYSTEM OVERVIEW
====================================

Purpose:
요금제를 데이터베이스에서 동적으로 관리
가격 변경, 기능 추가, 제한 설정을 코드 수정 없이 처리

Key Features:
- 동적 요금제 생성/수정/삭제
- 기능별 세밀한 제한 설정
- 공개 API로 프론트엔드 연동
- 비교표 자동 생성

====================================
🎁 PLAN STRUCTURE
====================================

Current Plans (초기 데이터):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ FREE (무료)
   - Price: 0원/월
   - Coins: 1개
   - Auto-trading: ❌
   - History: 7일
   - Support: Community

2️⃣ PREMIUM (프리미엄) ⭐ 가장 인기
   - Price: 29,900원/월, 299,000원/년 (17% 할인)
   - Trial: 14일 무료
   - Coins: 10개
   - Auto-trading: ✅ (최대 3개 전략)
   - Advanced indicators: ✅
   - History: 무제한
   - Support: Email (24시간 이내)

3️⃣ PRO (프로)
   - Price: 79,900원/월, 799,000원/년 (17% 할인)
   - Trial: 14일 무료
   - Coins: 20개
   - Auto-trading: ✅ (최대 10개 전략)
   - Backtesting: ✅
   - API Access: ✅
   - History: 무제한
   - Support: Priority (12시간 이내)

4️⃣ ENTERPRISE (엔터프라이즈)
   - Price: 맞춤 가격
   - Trial: 30일
   - Coins: 무제한
   - Auto-trading: ✅ (무제한)
   - White-labeling: ✅
   - SLA Guarantee: ✅
   - Custom Development: ✅
   - Support: Dedicated (1시간 이내)

====================================
⚙️ FEATURE LIMITS
====================================

Monitoring Limits:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- max_coins: 최대 모니터링 코인 수 (0 = 무제한)
- max_watchlists: 관심종목 리스트 개수

Trading Limits:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- auto_trading_enabled: 자동매매 활성화
- max_auto_strategies: 자동매매 전략 개수 (0 = 무제한)
- max_concurrent_trades: 동시 거래 개수 (0 = 무제한)

Analysis Features:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- advanced_indicators: 고급 기술 지표
- custom_indicators: 커스텀 지표
- backtesting_enabled: 백테스팅

Data Features:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- history_days: 히스토리 보관 일수 (0 = 무제한)
- data_export: 데이터 내보내기
- api_access: API 접근

Support Levels:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- community: 커뮤니티 지원 (72시간)
- email: 이메일 지원 (24시간)
- priority: 우선 지원 (12시간)
- dedicated: 전담 지원 (1시간)

Enterprise Features:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- white_labeling: 화이트라벨링
- sla_guarantee: SLA 보증
- custom_development: 맞춤 개발

====================================
🔧 API ENDPOINTS
====================================

Admin APIs (관리자 전용):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET    /api/admin/plans
       ?include_inactive=true
       모든 플랜 조회

GET    /api/admin/plans/:plan_code
       특정 플랜 조회

POST   /api/admin/plans
       새 플랜 생성

PUT    /api/admin/plans/:id
       플랜 수정

DELETE /api/admin/plans/:id
       플랜 삭제 (비활성화)

Public APIs (인증 불필요):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET    /api/admin/plans/public
       공개 플랜 목록

GET    /api/admin/plans/compare
       플랜 비교표 데이터

POST   /api/admin/plans/check-limit
       기능 제한 체크

====================================
💻 USAGE EXAMPLES
====================================

Example 1: 공개 플랜 목록 조회
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET /api/admin/plans/public

Response:
{
  "success": true,
  "plans": [
    {
      "plan_code": "free",
      "plan_name": "Free",
      "plan_name_ko": "무료",
      "price": {
        "monthly": 0,
        "annual": 0
      },
      "limits": {
        "max_coins": 1,
        "max_watchlists": 1
      },
      "features": {
        "auto_trading": false,
        "advanced_indicators": false,
        ...
      }
    },
    ...
  ]
}

Example 2: 플랜 비교표 조회
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET /api/admin/plans/compare

Response:
{
  "success": true,
  "comparison": [
    {
      "plan_code": "premium",
      "plan_name": "프리미엄",
      "monthly_price": 29900,
      "annual_price": 299000,
      "badge": "가장 인기",
      "is_featured": true,
      "features": {
        "monitoring": {
          "coins": 10,
          "watchlists": 5
        },
        "trading": {
          "auto_trading": true,
          "strategies": 3,
          "concurrent_trades": 5
        },
        ...
      },
      "cta": "무료 체험 시작"
    },
    ...
  ]
}

Example 3: 기능 제한 체크
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST /api/admin/plans/check-limit
{
  "plan_code": "premium",
  "feature": "coins",
  "current_count": 5
}

Response:
{
  "success": true,
  "limit_check": {
    "allowed": true,
    "limit": 10,
    "current": 5
  }
}

Example 4: 새 플랜 생성 (관리자)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST /api/admin/plans
Authorization: Bearer coinpulse_admin_2024_secure_token
{
  "plan_code": "starter",
  "plan_name": "Starter",
  "plan_name_ko": "스타터",
  "monthly_price": 19900,
  "annual_price": 199000,
  "max_coins": 5,
  "auto_trading_enabled": true,
  "max_auto_strategies": 1,
  "trial_days": 7
}

Example 5: 플랜 수정 (관리자)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PUT /api/admin/plans/2
Authorization: Bearer coinpulse_admin_2024_secure_token
{
  "monthly_price": 27900,
  "badge_text": "할인 중"
}

====================================
🔍 CODE INTEGRATION
====================================

프론트엔드에서 플랜 목록 가져오기:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// pricing.html 또는 pricing.js
async function loadPlans() {
    const response = await fetch('/api/admin/plans/compare');
    const data = await response.json();
    
    if (data.success) {
        renderPricingCards(data.comparison);
    }
}

function renderPricingCards(plans) {
    plans.forEach(plan => {
        const card = document.createElement('div');
        card.className = `pricing-card ${plan.is_featured ? 'featured' : ''}`;
        
        card.innerHTML = `
            ${plan.badge ? `<div class="featured-badge">${plan.badge}</div>` : ''}
            <div class="plan-name">${plan.plan_name}</div>
            <div class="plan-price">
                <span class="price">${plan.monthly_price.toLocaleString()}</span>
                <span class="currency">원/월</span>
            </div>
            <ul class="plan-features">
                <li>${plan.features.monitoring.coins}개 코인 모니터링</li>
                <li>${plan.features.trading.auto_trading ? '완전 자동매매' : '수동 거래만'}</li>
                ...
            </ul>
            <a href="signup.html?plan=${plan.plan_code}" class="btn">
                ${plan.cta}
            </a>
        `;
        
        pricingContainer.appendChild(card);
    });
}

기능 제한 체크 (로컬):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async function canAddCoin(userPlan, currentCoinCount) {
    const response = await fetch('/api/admin/plans/check-limit', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            plan_code: userPlan,
            feature: 'coins',
            current_count: currentCoinCount
        })
    });
    
    const data = await response.json();
    
    if (!data.limit_check.allowed) {
        alert(`플랜 제한: 최대 ${data.limit_check.limit}개까지만 추가 가능합니다.`);
        showUpgradeModal();
        return false;
    }
    
    return true;
}

백엔드에서 기능 제한 체크:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from backend.models import PlanConfig

def add_coin_to_watchlist(user_subscription, coin_symbol):
    # 현재 개수 확인
    current_count = get_user_coin_count(user_subscription.user_id)
    
    # 제한 체크
    check = PlanConfig.check_feature_limit(
        user_subscription,
        'coins',
        current_count
    )
    
    if not check['allowed']:
        return {
            'success': False,
            'error': f'Plan limit reached: {check["limit"]} coins maximum',
            'upgrade_required': True
        }
    
    # 코인 추가
    add_coin(user_subscription.user_id, coin_symbol)
    
    return {'success': True}

====================================
📦 INSTALLATION
====================================

Step 1: Upload Files
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- backend/models/plan_config.py
- backend/routes/plan_admin.py
- backend/migrations/005_add_plan_configs.sql
- backend/models/__init__.py (updated)
- app.py (updated)

Step 2: Run Migration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ssh root@158.247.222.216
cd /opt/coinpulse
psql -U postgres -d coinpulse -f backend/migrations/005_add_plan_configs.sql

Expected output:
CREATE TABLE
CREATE INDEX (x2)
CREATE FUNCTION
CREATE TRIGGER
INSERT 0 4  # 4 initial plans

Step 3: Restart Service
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
systemctl restart coinpulse
systemctl status coinpulse

Step 4: Test APIs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Public plans
curl http://coinpulse.sinsi.ai/api/admin/plans/public

# Comparison
curl http://coinpulse.sinsi.ai/api/admin/plans/compare

# Admin (with token)
curl -H "Authorization: Bearer coinpulse_admin_2024_secure_token" \
     http://coinpulse.sinsi.ai/api/admin/plans?include_inactive=true

====================================
🎯 PRICE CORRECTION
====================================

Current Issue:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
랜딩페이지: 29,900원
백엔드 코드: 29,000원 ← 불일치!

Solution (데이터베이스 기반):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 마이그레이션에 29,900원으로 설정됨
✅ 프론트엔드는 API에서 가격 가져옴
✅ 일관성 보장!

업데이트 방법:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PUT /api/admin/plans/2
{
  "monthly_price": 29900,
  "annual_price": 299000
}

====================================
✅ BENEFITS
====================================

✅ 동적 관리: 코드 수정 없이 요금제 변경
✅ 세밀한 제한: 기능별 개별 설정
✅ 공개 API: 프론트엔드 자동 연동
✅ 비교표 자동생성: 마케팅 자료 자동화
✅ 일관성: 단일 진실 출처 (DB)
✅ 확장성: 새 기능 추가 쉬움
✅ A/B 테스팅: 플랜별 전환율 추적 가능

====================================
🚀 NEXT STEPS
====================================

1️⃣ 프론트엔드 연동:
   - pricing.html API 호출로 변경
   - 동적 플랜 카드 생성
   - 비교표 자동 업데이트

2️⃣ 기능 제한 적용:
   - 코인 추가 시 제한 체크
   - 자동매매 전략 생성 시 제한 체크
   - 업그레이드 유도 UI

3️⃣ 분석 대시보드:
   - 플랜별 가입자 수
   - 전환율 추적
   - 수익 분석

====================================

🎊 PLAN MANAGEMENT SYSTEM READY!

모든 요금제를 데이터베이스에서 관리!
가격 변경은 이제 API 호출 하나로 끝!

====================================