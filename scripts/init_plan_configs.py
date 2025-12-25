#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Plan Configuration Initialization Script
플랜 설정 초기화 스크립트 - 최신 가격 반영
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.database.connection import get_db_session
from backend.models.plan_config import PlanConfig
from datetime import datetime

def init_plans():
    """Initialize or update plan configurations with latest pricing"""
    session = get_db_session()

    try:
        # 최신 플랜 정보 (2025.12.25 기준)
        plans_data = [
            {
                'plan_code': 'free',
                'plan_name': 'Free',
                'plan_name_ko': '무료',
                'description': '대시보드 조회 및 포트폴리오 추적',
                'display_order': 1,
                'monthly_price': 0,
                'annual_price': 0,
                'is_visible': True,
                'is_featured': False,
                'badge_text': None
            },
            {
                'plan_code': 'basic',
                'plan_name': 'Basic',
                'plan_name_ko': '베이직',
                'description': '입문 트레이더를 위한 기본 기능',
                'display_order': 2,
                'monthly_price': 29000,
                'annual_price': 290000,
                'is_visible': True,
                'is_featured': True,
                'badge_text': '인기'
            },
            {
                'plan_code': 'pro',
                'plan_name': 'Pro',
                'plan_name_ko': '프로',
                'description': '전문 트레이더를 위한 고급 기능',
                'display_order': 3,
                'monthly_price': 59000,
                'annual_price': 590000,
                'is_visible': True,
                'is_featured': False,
                'badge_text': None
            },
            {
                'plan_code': 'enterprise',
                'plan_name': 'Enterprise',
                'plan_name_ko': '엔터프라이즈',
                'description': '기관 투자자 및 전문가를 위한 맞춤형 솔루션',
                'display_order': 4,
                'monthly_price': 149000,
                'annual_price': 1490000,
                'is_visible': True,
                'is_featured': False,
                'badge_text': '프리미엄'
            }
        ]

        print("=" * 60)
        print("플랜 설정 초기화 시작")
        print("=" * 60)

        for plan_data in plans_data:
            plan_code = plan_data['plan_code']

            # 기존 플랜 확인
            existing = session.query(PlanConfig).filter(
                PlanConfig.plan_code == plan_code
            ).first()

            if existing:
                # 기존 플랜 업데이트
                print(f"\n[업데이트] {plan_code.upper()} 플랜")
                print(f"  이전 가격: {existing.monthly_price:,}원/월")
                print(f"  새 가격: {plan_data['monthly_price']:,}원/월")

                existing.plan_name = plan_data['plan_name']
                existing.plan_name_ko = plan_data['plan_name_ko']
                existing.description = plan_data['description']
                existing.display_order = plan_data['display_order']
                existing.monthly_price = plan_data['monthly_price']
                existing.annual_price = plan_data['annual_price']
                existing.is_visible = plan_data['is_visible']
                existing.is_featured = plan_data['is_featured']
                existing.badge_text = plan_data['badge_text']
                existing.updated_at = datetime.utcnow()

            else:
                # 새 플랜 생성
                print(f"\n[생성] {plan_code.upper()} 플랜")
                print(f"  가격: {plan_data['monthly_price']:,}원/월")

                new_plan = PlanConfig(
                    plan_code=plan_code,
                    plan_name=plan_data['plan_name'],
                    plan_name_ko=plan_data['plan_name_ko'],
                    description=plan_data['description'],
                    display_order=plan_data['display_order'],
                    monthly_price=plan_data['monthly_price'],
                    annual_price=plan_data['annual_price'],
                    is_visible=plan_data['is_visible'],
                    is_featured=plan_data['is_featured'],
                    badge_text=plan_data['badge_text']
                )
                session.add(new_plan)

        session.commit()

        print("\n" + "=" * 60)
        print("플랜 설정 초기화 완료")
        print("=" * 60)

        # 최종 확인
        all_plans = session.query(PlanConfig).order_by(PlanConfig.display_order).all()
        print(f"\n현재 등록된 플랜: {len(all_plans)}개")
        for plan in all_plans:
            visible = "O" if plan.is_visible else "X"
            featured = "*" if plan.is_featured else " "
            print(f"  {featured} [{visible}] {plan.plan_code.upper():12} - {plan.plan_name_ko:8} - {plan.monthly_price:>7,}원/월")

        return True

    except Exception as e:
        session.rollback()
        print(f"\n에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        session.close()

if __name__ == '__main__':
    print("CoinPulse - Plan Configuration Initialization")
    print("Updating with latest pricing...\n")

    success = init_plans()

    if success:
        print("\nScript completed successfully!")
        sys.exit(0)
    else:
        print("\nScript failed")
        sys.exit(1)
