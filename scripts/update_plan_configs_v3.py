#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Plan Configs Update Script v3.0
5단계 플랜 구조로 업데이트 (Free/Basic/Pro/Expert/Enterprise)

Changes:
1. Free: history_days 7 → 14일
2. Premium → Basic: 가격 49,000 → 39,000원, 연간 할인 17%
3. Pro (신규): 79,000원/월, 10개 코인, 5개 전략
4. Expert (기존 Pro 이름 변경): 99,000원/월, 30개 코인, 10개 전략
5. Enterprise: "가격 문의" 명시
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_db_session
from backend.models.plan_config import PlanConfig
from sqlalchemy import text

def update_plan_configs():
    """Update plan configurations for v3.0 (5-tier structure)"""

    print("="*60)
    print("Plan Configs Update Script v3.0")
    print("5단계 플랜 구조 (Free/Basic/Pro/Expert/Enterprise)")
    print("="*60)

    session = get_db_session()

    try:
        # 1. Update Free plan
        print("\n[1] Updating Free plan...")
        free_plan = session.query(PlanConfig).filter_by(plan_code='free').first()
        if free_plan:
            free_plan.history_days = 14  # 7 → 14
            free_plan.description = "급등 예측 상위 3개 조회, 14일 히스토리"
            print(f"   ✅ Free: history_days updated to 14 days")
        else:
            print(f"   ⚠️  Free plan not found")

        # 2. Update Premium → Basic
        print("\n[2] Updating Premium → Basic...")
        basic_plan = session.query(PlanConfig).filter_by(plan_code='premium').first()
        if basic_plan:
            # Change plan code premium → basic (주의: FK 제약 조건 확인 필요)
            # 대신 plan_name과 가격만 변경
            basic_plan.plan_name = 'Basic'
            basic_plan.plan_name_ko = '베이직'
            basic_plan.monthly_price = 39000  # 49,000 → 39,000
            basic_plan.annual_price = 390000  # 10개월 가격 (17% 할인)
            basic_plan.annual_discount_rate = 17  # 2개월 무료
            basic_plan.description = "소액으로 시작하는 AI 자동매매 - 5개 코인, 3개 전략"
            basic_plan.badge_text = "가장 인기"
            basic_plan.max_coins = 5
            basic_plan.max_auto_strategies = 3
            basic_plan.max_concurrent_trades = 3
            print(f"   ✅ Premium→Basic: 39,000원/월, 연간 17% 할인")
        else:
            print(f"   ⚠️  Premium plan not found")

        # 3. Update existing Pro → Expert
        print("\n[3] Updating Pro → Expert...")
        expert_plan = session.query(PlanConfig).filter_by(plan_code='pro').first()
        if expert_plan:
            expert_plan.plan_name = 'Expert'
            expert_plan.plan_name_ko = '전문가'
            expert_plan.monthly_price = 99000  # 유지
            expert_plan.annual_price = 990000  # 10개월 가격 (17% 할인)
            expert_plan.annual_discount_rate = 17
            expert_plan.description = "무제한 전략, 최고 수익률 - 30개 코인, 10개 전략"
            expert_plan.badge_text = None
            expert_plan.max_coins = 30  # 20 → 30
            expert_plan.max_auto_strategies = 10  # 유지
            expert_plan.max_concurrent_trades = 10
            expert_plan.history_days = 0  # Unlimited
            expert_plan.display_order = 3  # Basic(1), Pro(2), Expert(3)
            print(f"   ✅ Pro→Expert: 99,000원/월, 30개 코인")
        else:
            print(f"   ⚠️  Pro plan not found")

        # 4. Insert new Pro plan
        print("\n[4] Creating new Pro plan...")
        existing_pro = session.query(PlanConfig).filter_by(plan_code='pro_new').first()
        if not existing_pro:
            new_pro = PlanConfig(
                plan_code='pro_new',  # 임시 코드 (나중에 expert를 다른 코드로 변경 후 pro로 rename)
                plan_name='Pro',
                plan_name_ko='프로',
                description='본격적인 포트폴리오 관리 - 10개 코인, 5개 전략',
                display_order=2,

                # 가격
                monthly_price=79000,
                annual_price=790000,  # 10개월 가격 (17% 할인)
                setup_fee=0,
                annual_discount_rate=17,
                trial_days=7,

                # 기능 제한 - 모니터링
                max_coins=10,
                max_watchlists=10,

                # 기능 제한 - 자동매매
                auto_trading_enabled=True,
                max_auto_strategies=5,
                max_concurrent_trades=5,

                # 기능 제한 - 분석
                advanced_indicators=True,
                custom_indicators=True,
                backtesting_enabled=True,

                # 기능 제한 - 데이터
                history_days=180,
                data_export=True,
                api_access=False,

                # 기능 제한 - 알림
                email_notifications_enabled=True,
                daily_email_limit=50,
                signal_notifications=True,
                portfolio_notifications=True,
                trade_notifications=True,
                system_notifications=True,

                # 지원
                support_level='email',
                response_time_hours=24,

                # 기타
                white_labeling=False,
                sla_guarantee=False,
                custom_development=False,

                # 표시 설정
                is_active=True,
                is_featured=False,
                is_visible=True,
                badge_text=None,
                cta_text='지금 시작하기'
            )
            session.add(new_pro)
            print(f"   ✅ New Pro plan created: 79,000원/월")
        else:
            print(f"   ⚠️  Pro plan already exists")

        # 5. Update Enterprise
        print("\n[5] Updating Enterprise plan...")
        enterprise_plan = session.query(PlanConfig).filter_by(plan_code='enterprise').first()
        if enterprise_plan:
            enterprise_plan.description = "전담 매니저 + 맞춤형 커스터마이징"
            enterprise_plan.cta_text = "가격 문의"
            enterprise_plan.badge_text = None
            enterprise_plan.monthly_price = 0  # 맞춤형
            enterprise_plan.annual_price = 0
            enterprise_plan.display_order = 4
            print(f"   ✅ Enterprise: '가격 문의' 설정")
        else:
            print(f"   ⚠️  Enterprise plan not found")

        # Commit changes
        session.commit()

        print("\n" + "="*60)
        print("✅ All plans updated successfully!")
        print("="*60)

        # Display current plans
        print("\n📋 Current Plan Configuration:")
        print("-"*60)
        plans = session.query(PlanConfig).order_by(PlanConfig.display_order).all()
        for plan in plans:
            print(f"{plan.display_order}. {plan.plan_name_ko} ({plan.plan_code})")
            print(f"   Price: {plan.monthly_price:,}원/월, {plan.annual_price:,}원/년 ({plan.annual_discount_rate}% 할인)")
            print(f"   Coins: {plan.max_coins if plan.max_coins > 0 else 'Unlimited'}")
            print(f"   Strategies: {plan.max_auto_strategies if plan.max_auto_strategies > 0 else 'Unlimited'}")
            print(f"   History: {plan.history_days if plan.history_days > 0 else 'Unlimited'} days")
            print(f"   Badge: {plan.badge_text or 'None'}")
            print()

        return True

    except Exception as e:
        print(f"\n❌ Error updating plans: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return False

    finally:
        session.close()


if __name__ == '__main__':
    print("\n⚠️  WARNING: This will update plan configurations in the database!")
    print("   Make sure you have a backup before proceeding.\n")

    response = input("Continue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        success = update_plan_configs()
        sys.exit(0 if success else 1)
    else:
        print("\n❌ Aborted by user")
        sys.exit(1)
