"""
Subscription & Plan Check Middleware

사용자의 요금제를 확인하고 기능 접근을 제어합니다.
"""
from functools import wraps
from flask import request, jsonify
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# 플랜별 제한 설정 (2025.12.25 업데이트: 4개 플랜)
PLAN_LIMITS = {
    'free': {
        'manual_trading': False,  # 수동 거래 불가 (조회만)
        'auto_trading_strategies': 0,  # 자동매매 불가
        'surge_monitoring': False,  # 급등 모니터링 불가
        'monitoring_coins': 1,  # 모니터링 코인 1개
        'chart_history_days': 7,  # 차트 데이터 7일
        'backtest_runs_per_day': 0,  # 백테스트 불가
        'api_requests_per_hour': 100,  # API 호출 제한
        'features': {
            'manual_trading': False,  # 조회만
            'auto_trading': False,
            'surge_alerts': False,
            'telegram_alerts': False,  # 텔레그램 없음
            'advanced_indicators': False,  # 기본 지표만
            'data_export': False,
            'priority_support': False
        }
    },
    'basic': {
        'manual_trading': True,  # 수동 거래 가능
        'auto_trading_strategies': 0,  # 자동매매 불가
        'surge_monitoring': False,  # 급등 모니터링 불가
        'monitoring_coins': 5,  # 모니터링 코인 5개
        'chart_history_days': 90,  # 90일
        'backtest_runs_per_day': 0,  # 백테스트 불가
        'api_requests_per_hour': 500,
        'features': {
            'manual_trading': True,  # 수동 거래만
            'auto_trading': False,
            'surge_alerts': False,  # 급등 신호 없음
            'telegram_alerts': False,  # 텔레그램 없음
            'advanced_indicators': False,  # 기본 지표만 (MA, RSI, MACD)
            'data_export': False,
            'priority_support': False
        }
    },
    'pro': {
        'manual_trading': True,  # 수동 거래 가능
        'auto_trading_strategies': 0,  # 자동매매 불가
        'surge_monitoring': False,  # 급등 모니터링 불가
        'monitoring_coins': 10,  # 모니터링 코인 10개
        'chart_history_days': 180,  # 180일
        'backtest_runs_per_day': 0,  # 백테스트 불가
        'api_requests_per_hour': 1000,
        'features': {
            'manual_trading': True,  # 수동 거래
            'auto_trading': False,
            'surge_alerts': False,  # 급등 신호 없음
            'telegram_alerts': False,  # 텔레그램 없음
            'advanced_indicators': True,  # 고급 지표 (Ichimoku, SuperTrend)
            'data_export': True,  # CSV 내보내기
            'priority_support': True  # 우선 지원
        }
    },
    'enterprise': {
        'manual_trading': True,  # 수동 거래 가능
        'auto_trading_strategies': -1,  # 자동매매 무제한
        'surge_monitoring': True,  # 급등 모니터링 가능
        'monitoring_coins': -1,  # 모니터링 무제한
        'chart_history_days': -1,  # 무제한
        'backtest_runs_per_day': -1,  # 백테스트 무제한
        'api_requests_per_hour': -1,  # 무제한
        'features': {
            'manual_trading': True,  # 수동 거래
            'auto_trading': True,  # 자동매매
            'surge_alerts': True,  # 급등 신호
            'telegram_alerts': True,  # 텔레그램 급등 알림
            'advanced_indicators': True,  # 고급 지표
            'data_export': True,  # CSV 내보내기
            'priority_support': True,  # 최우선 지원
            'api_access': True
        }
    },
    # 하위 호환성 (기존 코드)
    'FREE': {
        'manual_trading': False,
        'features': {'manual_trading': False, 'telegram_alerts': False}
    },
    'PREMIUM': {
        'manual_trading': True,
        'features': {'manual_trading': True, 'telegram_alerts': False}
    }
}


def get_user_plan(user_id: str = None, email: str = None) -> Dict[str, Any]:
    """
    사용자의 현재 플랜 조회

    Args:
        user_id: 사용자 ID
        email: 이메일 (user_id 대신 사용 가능)

    Returns:
        {
            'plan_code': 'FREE' | 'PREMIUM',
            'plan_name': '무료' | '프리미엄',
            'limits': {...},
            'features': {...}
        }
    """
    try:
        from backend.database import get_db_session
        from backend.models.subscription_models import UserSubscription
        from backend.models.auth_models import User

        session = get_db_session()

        # 사용자 조회
        if email:
            user = session.query(User).filter_by(email=email).first()
            if not user:
                logger.warning(f"[SubscriptionCheck] User not found: {email}")
                return get_default_plan()
            user_id = user.id

        if not user_id:
            logger.warning("[SubscriptionCheck] No user_id provided")
            return get_default_plan()

        # 구독 조회
        subscription = session.query(UserSubscription).filter_by(
            user_id=user_id,
            status='active'
        ).first()

        if not subscription:
            logger.info(f"[SubscriptionCheck] No active subscription for user {user_id}, using FREE plan")
            return get_plan_info('FREE')

        plan_code = subscription.plan_code
        logger.info(f"[SubscriptionCheck] User {user_id} has plan: {plan_code}")

        return get_plan_info(plan_code)

    except Exception as e:
        logger.error(f"[SubscriptionCheck] Error getting user plan: {e}")
        return get_default_plan()


def get_plan_info(plan_code: str) -> Dict[str, Any]:
    """
    플랜 정보 조회

    Args:
        plan_code: 'free' | 'basic' | 'pro' | 'enterprise' (lowercase)

    Returns:
        플랜 정보 딕셔너리
    """
    # Normalize to lowercase
    plan_code = plan_code.lower() if plan_code else 'free'

    if plan_code not in PLAN_LIMITS:
        logger.warning(f"[SubscriptionCheck] Unknown plan code: {plan_code}, using free")
        plan_code = 'free'

    limits = PLAN_LIMITS[plan_code]

    # Plan name mapping
    plan_names = {
        'free': '무료',
        'basic': '베이직',
        'pro': '프로',
        'enterprise': '엔터프라이즈',
        'FREE': '무료',  # 하위 호환성
        'PREMIUM': '프리미엄'  # 하위 호환성
    }

    return {
        'plan_code': plan_code,
        'plan_name': plan_names.get(plan_code, '무료'),
        'limits': {k: v for k, v in limits.items() if k != 'features'},
        'features': limits.get('features', {})
    }


def get_default_plan() -> Dict[str, Any]:
    """
    기본 플랜 (FREE) 반환
    """
    return get_plan_info('FREE')


def check_feature_access(user_id: str, feature: str) -> bool:
    """
    특정 기능 접근 권한 체크

    Args:
        user_id: 사용자 ID
        feature: 기능명 (예: 'auto_trading', 'advanced_indicators')

    Returns:
        True if allowed, False otherwise
    """
    plan = get_user_plan(user_id=user_id)
    features = plan.get('features', {})

    has_access = features.get(feature, False)

    logger.info(f"[SubscriptionCheck] User {user_id} feature '{feature}' access: {has_access}")

    return has_access


def check_feature_limit(user_id: str, limit_name: str, current_count: int) -> Dict[str, Any]:
    """
    기능 사용량 제한 체크

    Args:
        user_id: 사용자 ID
        limit_name: 제한 항목명 (예: 'auto_trading_strategies')
        current_count: 현재 사용량

    Returns:
        {
            'allowed': bool,
            'current': int,
            'limit': int,
            'plan_code': str,
            'message': str
        }
    """
    plan = get_user_plan(user_id=user_id)
    limits = plan.get('limits', {})
    limit_value = limits.get(limit_name, 0)

    # -1은 무제한
    if limit_value == -1:
        return {
            'allowed': True,
            'current': current_count,
            'limit': -1,
            'plan_code': plan['plan_code'],
            'message': '무제한'
        }

    allowed = current_count < limit_value

    return {
        'allowed': allowed,
        'current': current_count,
        'limit': limit_value,
        'plan_code': plan['plan_code'],
        'message': f"{current_count}/{limit_value} 사용 중" if allowed else f"제한 초과 ({limit_value}개 최대)"
    }


def require_plan(*required_plans):
    """
    API 엔드포인트에 플랜 체크 적용하는 decorator

    Usage:
        @app.route('/api/auto-trading/start')
        @require_plan('PREMIUM')
        def start_auto_trading():
            ...

    Args:
        *required_plans: 허용할 플랜 코드 리스트 (예: 'PREMIUM')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 요청에서 user_id 추출
            user_id = request.args.get('user_id') or request.json.get('user_id') if request.is_json else None

            if not user_id:
                # URL path에서 user_id 추출 시도
                if 'user_id' in kwargs:
                    user_id = kwargs['user_id']
                else:
                    logger.warning("[SubscriptionCheck] No user_id in request")
                    return jsonify({
                        'success': False,
                        'error': 'user_id required',
                        'upgrade_required': True
                    }), 401

            # 사용자 플랜 확인
            plan = get_user_plan(user_id=user_id)
            plan_code = plan['plan_code']

            # 플랜 체크
            if plan_code not in required_plans:
                logger.warning(f"[SubscriptionCheck] User {user_id} plan '{plan_code}' not in required plans: {required_plans}")
                return jsonify({
                    'success': False,
                    'error': f'{required_plans[0]} 플랜이 필요합니다',
                    'current_plan': plan_code,
                    'required_plan': required_plans[0],
                    'upgrade_required': True,
                    'upgrade_url': '/checkout.html?plan=PREMIUM'
                }), 403

            # 플랜 정보를 kwargs에 추가 (선택)
            kwargs['user_plan'] = plan

            return f(*args, **kwargs)

        return decorated_function
    return decorator


def require_feature(feature: str):
    """
    특정 기능 접근 권한 체크 decorator

    Usage:
        @app.route('/api/backtest')
        @require_feature('auto_trading')
        def run_backtest():
            ...

    Args:
        feature: 기능명
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = request.args.get('user_id') or request.json.get('user_id') if request.is_json else None

            if not user_id and 'user_id' in kwargs:
                user_id = kwargs['user_id']

            if not user_id:
                return jsonify({
                    'success': False,
                    'error': 'user_id required'
                }), 401

            # 기능 접근 권한 체크
            has_access = check_feature_access(user_id, feature)

            if not has_access:
                plan = get_user_plan(user_id=user_id)
                return jsonify({
                    'success': False,
                    'error': f'{feature} 기능은 PREMIUM 플랜에서만 사용 가능합니다',
                    'current_plan': plan['plan_code'],
                    'upgrade_required': True,
                    'upgrade_url': '/checkout.html?plan=PREMIUM'
                }), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator
