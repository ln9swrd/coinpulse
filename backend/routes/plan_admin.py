"""
Plan Configuration Admin API Routes
요금제 설정 관리 API
"""
from flask import Blueprint, request, jsonify
from backend.database.connection import get_db_session
from backend.models.plan_config import PlanConfig
from backend.middleware.auth import admin_required

plan_admin_bp = Blueprint('plan_admin', __name__, url_prefix='/api/admin/plans')

@plan_admin_bp.route('', methods=['GET'])
@admin_required
def get_plans():
    """모든 플랜 조회 (관리자)"""
    session = get_db_session()
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

        if include_inactive:
            plans = session.query(PlanConfig).order_by(PlanConfig.display_order.asc()).all()
        else:
            plans = PlanConfig.get_active_plans(session)

        return jsonify({
            'success': True,
            'plans': [p.to_dict() for p in plans],
            'count': len(plans)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@plan_admin_bp.route('/<plan_code>', methods=['GET'])
def get_plan(plan_code):
    """특정 플랜 조회 (공개 - 인증 불필요)"""
    session = get_db_session()
    try:
        plan = PlanConfig.get_plan_by_code(plan_code, session)

        if not plan:
            return jsonify({'success': False, 'error': 'Plan not found'}), 404

        if not plan.is_visible:
            return jsonify({'success': False, 'error': 'Plan not available'}), 403

        return jsonify({
            'success': True,
            'plan': plan.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@plan_admin_bp.route('', methods=['POST'])
@admin_required
def create_plan():
    """새 플랜 생성"""
    session = get_db_session()
    try:
        data = request.json

        # 필수 필드 체크
        if 'plan_code' not in data or 'plan_name' not in data:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        # 중복 체크
        existing = PlanConfig.get_plan_by_code(data['plan_code'], session)
        if existing:
            return jsonify({'success': False, 'error': 'Plan code already exists'}), 400

        # 플랜 생성
        plan = PlanConfig(
            plan_code=data['plan_code'],
            plan_name=data['plan_name'],
            plan_name_ko=data.get('plan_name_ko'),
            description=data.get('description'),
            display_order=data.get('display_order', 0),
            monthly_price=data.get('monthly_price', 0),
            annual_price=data.get('annual_price', 0),
            setup_fee=data.get('setup_fee', 0),
            annual_discount_rate=data.get('annual_discount_rate', 0),
            trial_days=data.get('trial_days', 0),
            max_coins=data.get('max_coins', 1),
            max_watchlists=data.get('max_watchlists', 1),
            auto_trading_enabled=data.get('auto_trading_enabled', False),
            max_auto_strategies=data.get('max_auto_strategies', 0),
            max_concurrent_trades=data.get('max_concurrent_trades', 0),
            advanced_indicators=data.get('advanced_indicators', False),
            custom_indicators=data.get('custom_indicators', False),
            backtesting_enabled=data.get('backtesting_enabled', False),
            history_days=data.get('history_days', 7),
            data_export=data.get('data_export', False),
            api_access=data.get('api_access', False),
            support_level=data.get('support_level', 'community'),
            response_time_hours=data.get('response_time_hours', 72),
            white_labeling=data.get('white_labeling', False),
            sla_guarantee=data.get('sla_guarantee', False),
            custom_development=data.get('custom_development', False),
            is_active=data.get('is_active', True),
            is_featured=data.get('is_featured', False),
            is_visible=data.get('is_visible', True),
            badge_text=data.get('badge_text'),
            cta_text=data.get('cta_text')
        )

        session.add(plan)
        session.commit()

        return jsonify({
            'success': True,
            'plan': plan.to_dict(),
            'message': 'Plan created successfully'
        }), 201
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@plan_admin_bp.route('/<int:plan_id>', methods=['PUT'])
@admin_required
def update_plan(plan_id):
    """플랜 수정"""
    session = get_db_session()
    try:
        plan = session.query(PlanConfig).filter_by(id=plan_id).first()
        if not plan:
            return jsonify({'success': False, 'error': 'Plan not found'}), 404

        data = request.json

        # 업데이트 가능한 필드
        updatable_fields = [
            'plan_name', 'plan_name_ko', 'description', 'display_order',
            'monthly_price', 'annual_price', 'setup_fee', 'annual_discount_rate', 'trial_days',
            'max_coins', 'max_watchlists',
            'auto_trading_enabled', 'max_auto_strategies', 'max_concurrent_trades',
            'advanced_indicators', 'custom_indicators', 'backtesting_enabled',
            'history_days', 'data_export', 'api_access',
            'support_level', 'response_time_hours',
            'white_labeling', 'sla_guarantee', 'custom_development',
            'is_active', 'is_featured', 'is_visible', 'badge_text', 'cta_text'
        ]

        for field in updatable_fields:
            if field in data:
                setattr(plan, field, data[field])

        session.commit()

        return jsonify({
            'success': True,
            'plan': plan.to_dict(),
            'message': 'Plan updated successfully'
        })
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@plan_admin_bp.route('/<int:plan_id>', methods=['DELETE'])
@admin_required
def delete_plan(plan_id):
    """플랜 삭제 (실제로는 비활성화)"""
    session = get_db_session()
    try:
        plan = session.query(PlanConfig).filter_by(id=plan_id).first()
        if not plan:
            return jsonify({'success': False, 'error': 'Plan not found'}), 404

        # 소프트 삭제 (비활성화)
        plan.is_active = False
        plan.is_visible = False
        session.commit()

        return jsonify({
            'success': True,
            'message': 'Plan deactivated successfully'
        })
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@plan_admin_bp.route('/public', methods=['GET'])
def get_public_plans():
    """공개 플랜 목록 (인증 불필요)"""
    session = get_db_session()
    try:
        plans = PlanConfig.get_active_plans(session)

        return jsonify({
            'success': True,
            'plans': [p.to_dict() for p in plans],
            'count': len(plans)
        })
    except Exception as e:
        # If table doesn't exist, return empty list instead of 500
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"[Plans] Error fetching public plans (table may not exist yet): {str(e)}")
        return jsonify({
            'success': True,
            'plans': [],
            'count': 0,
            'message': 'Plan configuration not initialized yet'
        }), 200
    finally:
        session.close()

@plan_admin_bp.route('/compare', methods=['GET'])
def compare_plans():
    """플랜 비교표 데이터 (인증 불필요)"""
    session = get_db_session()
    try:
        try:
            plans = PlanConfig.get_active_plans(session)
        except Exception:
            # If table doesn't exist, return empty comparison
            return jsonify({
                'success': True,
                'comparison': [],
                'message': 'Plan configuration not initialized yet'
            }), 200

        # 비교표용 데이터 구조
        comparison = []
        for plan in plans:
            plan_data = plan.to_dict()
            comparison.append({
                'plan_code': plan.plan_code,
                'plan_name': plan.plan_name_ko or plan.plan_name,
                'monthly_price': plan.monthly_price,
                'annual_price': plan.annual_price,
                'badge': plan.badge_text,
                'is_featured': plan.is_featured,
                'features': {
                    'monitoring': {
                        'coins': plan.max_coins if plan.max_coins > 0 else '무제한',
                        'watchlists': plan.max_watchlists
                    },
                    'trading': {
                        'auto_trading': plan.auto_trading_enabled,
                        'strategies': plan.max_auto_strategies if plan.max_auto_strategies > 0 else '무제한' if plan.auto_trading_enabled else 0,
                        'concurrent_trades': plan.max_concurrent_trades if plan.max_concurrent_trades > 0 else '무제한' if plan.auto_trading_enabled else 0
                    },
                    'analysis': {
                        'advanced_indicators': plan.advanced_indicators,
                        'custom_indicators': plan.custom_indicators,
                        'backtesting': plan.backtesting_enabled
                    },
                    'data': {
                        'history_days': plan.history_days if plan.history_days > 0 else '무제한',
                        'export': plan.data_export,
                        'api': plan.api_access
                    },
                    'support': {
                        'level': plan.support_level,
                        'response_hours': plan.response_time_hours
                    },
                    'enterprise': {
                        'white_labeling': plan.white_labeling,
                        'sla': plan.sla_guarantee,
                        'custom_dev': plan.custom_development
                    }
                },
                'cta': plan.cta_text
            })

        return jsonify({
            'success': True,
            'comparison': comparison
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@plan_admin_bp.route('/check-limit', methods=['POST'])
def check_feature_limit():
    """기능 제한 체크 (사용자용)"""
    session = get_db_session()
    try:
        data = request.json
        plan_code = data.get('plan_code')
        feature = data.get('feature')  # 'coins', 'strategies', 'trades', 'watchlists'
        current_count = data.get('current_count', 0)

        if not plan_code or not feature:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        plan = PlanConfig.get_plan_by_code(plan_code, session)
        if not plan:
            return jsonify({'success': False, 'error': 'Plan not found'}), 404

        # Mock subscription object
        class MockSubscription:
            def __init__(self, plan_code):
                self.plan = plan_code

        result = PlanConfig.check_feature_limit(
            MockSubscription(plan_code),
            feature,
            current_count,
            session
        )

        return jsonify({
            'success': True,
            'limit_check': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()
