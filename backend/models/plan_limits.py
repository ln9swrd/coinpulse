# -*- coding: utf-8 -*-
"""
Plan Limits Model
요금제별 제한 관리 (약속 vs 실제 제공)
"""

from enum import Enum


class SignalAllocationStrategy(Enum):
    """시그널 분배 전략"""
    PROMISED = "promised"      # 약속한 횟수만
    OVER_DELIVER = "over_deliver"  # 약속보다 더 많이 (기본)
    UNLIMITED = "unlimited"    # 무제한


class PlanLimits:
    """
    요금제별 자동매매 알림 제한 관리

    핵심 전략: "Under-Promise, Over-Deliver"
    - 고객에게는 낮은 횟수 약속
    - 실제로는 더 많이 제공
    - 고객 만족도 극대화
    """

    # 공개 정보 (약속한 것)
    # 프론트엔드 가격 페이지에 표시
    PROMISED_LIMITS = {
        'free': 1,          # 약속: 월 1회 (체험)
        'basic': 3,         # 약속: 월 3회
        'pro': 15,          # 약속: 월 15회
        'enterprise': -1    # 무제한
    }

    # 실제 제공 (내부 정책)
    # 약속보다 50-100% 더 많이 제공
    ACTUAL_LIMITS = {
        'free': 2,          # 실제: 2회 (100% 보너스)
        'basic': 6,         # 실제: 6회 (100% 보너스)
        'pro': 25,          # 실제: 25회 (67% 보너스)
        'enterprise': -1    # 무제한 + 우선 배정
    }

    # 보너스 비율 (참고용)
    BONUS_RATIO = {
        'free': 1.0,        # 100%
        'basic': 1.0,       # 100%
        'pro': 0.67,        # 67%
        'enterprise': 0
    }

    @classmethod
    def get_promised_limit(cls, plan):
        """
        약속한 알림 횟수 (공개 정보)

        Args:
            plan (str): 플랜 이름 ('free', 'basic', 'pro', 'enterprise')

        Returns:
            int: 약속한 월간 알림 횟수 (-1은 무제한)
        """
        return cls.PROMISED_LIMITS.get(plan, 0)

    @classmethod
    def get_actual_limit(cls, plan):
        """
        실제 제공하는 알림 횟수 (내부 정책)

        Args:
            plan (str): 플랜 이름

        Returns:
            int: 실제 월간 알림 횟수 (-1은 무제한)
        """
        return cls.ACTUAL_LIMITS.get(plan, 0)

    @classmethod
    def get_bonus_count(cls, plan):
        """
        보너스 알림 횟수

        Args:
            plan (str): 플랜 이름

        Returns:
            int: 보너스 횟수
        """
        promised = cls.get_promised_limit(plan)
        actual = cls.get_actual_limit(plan)

        if promised == -1 or actual == -1:
            return 0  # 무제한은 보너스 개념 없음

        return actual - promised

    @classmethod
    def check_can_receive_signal(cls, plan, current_usage):
        """
        사용자가 알림을 받을 수 있는지 확인

        Args:
            plan (str): 플랜 이름
            current_usage (int): 이번 달 사용한 알림 횟수

        Returns:
            tuple: (bool: 받을 수 있는지, str: 이유 메시지)
        """
        actual_limit = cls.get_actual_limit(plan)

        # 무제한 플랜
        if actual_limit == -1:
            return True, "unlimited"

        # 실제 제한 확인
        if current_usage < actual_limit:
            remaining = actual_limit - current_usage
            return True, f"{remaining}회 남음"

        # 제한 초과
        promised = cls.get_promised_limit(plan)
        return False, f"{plan} 플랜은 월 {promised}회까지 약속드렸습니다 (보너스 포함 {actual_limit}회)"

    @classmethod
    def is_bonus_signal(cls, plan, current_usage):
        """
        현재 받는 알림이 보너스인지 확인

        Args:
            plan (str): 플랜 이름
            current_usage (int): 이번 달 사용한 알림 횟수

        Returns:
            bool: 보너스 알림인지 여부
        """
        promised = cls.get_promised_limit(plan)

        if promised == -1:
            return False  # 무제한은 보너스 개념 없음

        # 약속한 횟수를 초과했으면 보너스
        return current_usage >= promised

    @classmethod
    def get_usage_stats(cls, plan, current_usage):
        """
        사용량 통계 정보

        Args:
            plan (str): 플랜 이름
            current_usage (int): 이번 달 사용한 알림 횟수

        Returns:
            dict: 사용량 통계
        """
        promised = cls.get_promised_limit(plan)
        actual = cls.get_actual_limit(plan)
        bonus = cls.get_bonus_count(plan)

        # 무제한 플랜
        if actual == -1:
            return {
                'plan': plan,
                'promised': '무제한',
                'actual': '무제한',
                'used': current_usage,
                'remaining': '무제한',
                'is_bonus': False,
                'bonus_received': 0,
                'usage_percentage': 0
            }

        # 보너스 받은 횟수 계산
        bonus_received = max(0, current_usage - promised)

        # 사용률 계산 (실제 제한 기준)
        usage_percentage = int((current_usage / actual) * 100) if actual > 0 else 0

        return {
            'plan': plan,
            'promised': promised,           # 약속한 것
            'actual': actual,               # 실제 제한
            'used': current_usage,          # 사용한 것
            'remaining': max(0, actual - current_usage),  # 남은 것
            'is_bonus': cls.is_bonus_signal(plan, current_usage),
            'bonus_received': bonus_received,  # 보너스로 받은 것
            'total_bonus': bonus,           # 총 보너스
            'usage_percentage': usage_percentage
        }

    @classmethod
    def get_all_plan_info(cls):
        """
        전체 플랜 정보 요약

        Returns:
            dict: 플랜별 정보
        """
        plans = {}

        for plan in cls.PROMISED_LIMITS.keys():
            promised = cls.get_promised_limit(plan)
            actual = cls.get_actual_limit(plan)
            bonus = cls.get_bonus_count(plan)

            plans[plan] = {
                'promised': promised if promised != -1 else '무제한',
                'actual': actual if actual != -1 else '무제한',
                'bonus': bonus,
                'bonus_ratio': cls.BONUS_RATIO.get(plan, 0)
            }

        return plans


# Test function
if __name__ == "__main__":
    print("=" * 60)
    print("Plan Limits Test")
    print("=" * 60)

    # Test 1: 전체 플랜 정보
    print("\n[Test 1] All plan info:")
    all_plans = PlanLimits.get_all_plan_info()
    for plan, info in all_plans.items():
        print(f"\n{plan.upper()}:")
        print(f"  약속: {info['promised']}회/월")
        print(f"  실제: {info['actual']}회/월")
        print(f"  보너스: +{info['bonus']}회 ({int(info['bonus_ratio']*100)}%)")

    # Test 2: Basic 플랜 사용량 체크
    print("\n[Test 2] Basic plan usage check:")
    for usage in [0, 1, 3, 5, 6, 7]:
        can_receive, msg = PlanLimits.check_can_receive_signal('basic', usage)
        stats = PlanLimits.get_usage_stats('basic', usage)
        print(f"\n  Usage: {usage}회")
        print(f"    Can receive: {can_receive} ({msg})")
        print(f"    Is bonus: {stats['is_bonus']}")
        print(f"    Bonus received: {stats['bonus_received']}회")
        print(f"    Usage: {stats['usage_percentage']}%")
