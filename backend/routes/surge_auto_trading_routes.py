# -*- coding: utf-8 -*-
"""
Surge Auto Trading Routes
급등 알림 자동매매 설정 및 포지션 관리 API

참고 문서: docs/features/SURGE_ALERT_SYSTEM.md v2.0
"""

from flask import Blueprint, request, jsonify
import logging

from backend.database.connection import get_db_session
from backend.utils.auth_utils import require_auth
from backend.models.surge_alert_models import SurgeAutoTradingSettings, SurgeAlert
from backend.models.plan_features import get_user_features

logger = logging.getLogger(__name__)

# Create Blueprint
surge_auto_trading_bp = Blueprint('surge_auto_trading', __name__, url_prefix='/api/surge/auto-trading')


@surge_auto_trading_bp.route('/settings', methods=['GET'])
@require_auth
def get_settings(current_user):
    """
    Get surge auto-trading settings

    Returns:
        JSON response with settings
    """
    try:
        session = get_db_session()

        # Get or create settings
        settings = session.query(SurgeAutoTradingSettings)\
            .filter(SurgeAutoTradingSettings.user_id == current_user.id)\
            .first()

        # Create default settings if none exist
        if not settings:
            settings = SurgeAutoTradingSettings(user_id=current_user.id)
            session.add(settings)
            session.commit()
            logger.info(f"[AutoTrading] Created default settings for user {current_user.id}")

        # Get plan features
        plan = current_user.plan or 'free'
        features = get_user_features(plan)

        # Check if user can use auto-trading
        can_use = features.get('surge_auto_trading', False)
        max_budget = features.get('max_surge_budget', 0)

        return jsonify({
            'success': True,
            'settings': settings.to_dict(),
            'plan_limits': {
                'can_use': can_use,
                'max_budget': max_budget,
                'max_alerts_per_week': features.get('max_alerts_per_week', 0),
                'plan': plan
            }
        }), 200

    except Exception as e:
        logger.error(f"[AutoTrading] Error getting settings for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get settings'
        }), 500


@surge_auto_trading_bp.route('/settings', methods=['PUT'])
@require_auth
def update_settings(current_user):
    """
    Update surge auto-trading settings

    Request body:
        {
            "enabled": true,
            "total_budget": 1000000,
            "amount_per_trade": 100000,
            "risk_level": "moderate",
            "stop_loss_enabled": true,
            "stop_loss_percent": -5.0,
            "take_profit_enabled": true,
            "take_profit_percent": 10.0,
            "min_confidence": 80.0,
            "max_positions": 5,
            "excluded_coins": ["DOGE", "SHIB"],
            "telegram_enabled": true,
            "position_strategy": "single",
            "max_amount_per_coin": 500000,
            "allow_duplicate_positions": false
        }

    Returns:
        JSON response with updated settings
    """
    try:
        session = get_db_session()
        data = request.get_json()

        # Check user's plan
        plan = current_user.plan or 'free'
        features = get_user_features(plan)

        # Check if plan allows auto-trading
        if not features.get('surge_auto_trading', False):
            return jsonify({
                'success': False,
                'error': 'Your plan does not support auto-trading. Please upgrade to Basic or Pro plan.'
            }), 403

        # Get or create settings
        settings = session.query(SurgeAutoTradingSettings)\
            .filter(SurgeAutoTradingSettings.user_id == current_user.id)\
            .first()

        if not settings:
            settings = SurgeAutoTradingSettings(user_id=current_user.id)
            session.add(settings)

        # Validate budget limit
        max_budget = features.get('max_surge_budget', 0)
        requested_budget = data.get('total_budget', settings.total_budget)

        if max_budget > 0 and requested_budget > max_budget:
            return jsonify({
                'success': False,
                'error': f'Budget exceeds plan limit of {max_budget:,} KRW'
            }), 400

        # Update settings
        if 'enabled' in data:
            settings.enabled = data['enabled']
        if 'total_budget' in data:
            settings.total_budget = data['total_budget']
        if 'amount_per_trade' in data:
            settings.amount_per_trade = data['amount_per_trade']
        if 'risk_level' in data:
            if data['risk_level'] not in ['conservative', 'moderate', 'aggressive']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid risk level'
                }), 400
            settings.risk_level = data['risk_level']
        if 'stop_loss_enabled' in data:
            settings.stop_loss_enabled = data['stop_loss_enabled']
        if 'stop_loss_percent' in data:
            settings.stop_loss_percent = data['stop_loss_percent']
        if 'take_profit_enabled' in data:
            settings.take_profit_enabled = data['take_profit_enabled']
        if 'take_profit_percent' in data:
            settings.take_profit_percent = data['take_profit_percent']
        if 'min_confidence' in data:
            settings.min_confidence = data['min_confidence']
        if 'max_positions' in data:
            settings.max_positions = data['max_positions']
        if 'excluded_coins' in data:
            settings.excluded_coins = data['excluded_coins']
        if 'telegram_enabled' in data:
            settings.telegram_enabled = data['telegram_enabled']

        # Position strategy fields (NEW)
        if 'position_strategy' in data:
            if data['position_strategy'] not in ['single', 'multiple']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid position strategy. Must be "single" or "multiple"'
                }), 400
            settings.position_strategy = data['position_strategy']
        if 'max_amount_per_coin' in data:
            settings.max_amount_per_coin = data['max_amount_per_coin']
        if 'allow_duplicate_positions' in data:
            settings.allow_duplicate_positions = data['allow_duplicate_positions']

        session.commit()

        logger.info(f"[AutoTrading] Settings updated for user {current_user.id}")

        return jsonify({
            'success': True,
            'settings': settings.to_dict(),
            'message': 'Settings updated successfully'
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"[AutoTrading] Error updating settings for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update settings'
        }), 500


@surge_auto_trading_bp.route('/positions', methods=['GET'])
@require_auth
def get_positions(current_user):
    """
    Get current open positions from auto-trading

    Returns:
        JSON response with open positions
    """
    try:
        session = get_db_session()

        # Get open positions (auto-traded alerts that are still open)
        positions = session.query(SurgeAlert)\
            .filter(
                SurgeAlert.user_id == current_user.id,
                SurgeAlert.auto_traded == True,
                SurgeAlert.status.in_(['pending', 'executed'])
            )\
            .order_by(SurgeAlert.sent_at.desc())\
            .all()

        # Calculate total invested and P&L
        total_invested = sum(pos.trade_amount or 0 for pos in positions)
        total_pl = sum(pos.profit_loss or 0 for pos in positions)

        logger.info(f"[AutoTrading] User {current_user.id} has {len(positions)} open positions")

        return jsonify({
            'success': True,
            'positions': [pos.to_dict() for pos in positions],
            'count': len(positions),
            'total_invested': total_invested,
            'total_profit_loss': total_pl
        }), 200

    except Exception as e:
        logger.error(f"[AutoTrading] Error getting positions for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get positions'
        }), 500


@surge_auto_trading_bp.route('/history', methods=['GET'])
@require_auth
def get_history(current_user):
    """
    Get auto-trading history

    Query parameters:
        - limit: Maximum number of records (default: 50)
        - status: Filter by status (pending/executed/stopped/completed)

    Returns:
        JSON response with trade history
    """
    try:
        session = get_db_session()

        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        status_filter = request.args.get('status', None)

        # Build query
        query = session.query(SurgeAlert)\
            .filter(
                SurgeAlert.user_id == current_user.id,
                SurgeAlert.auto_traded == True
            )

        # Apply status filter
        if status_filter:
            query = query.filter(SurgeAlert.status == status_filter)

        # Get history
        history = query.order_by(SurgeAlert.sent_at.desc())\
            .limit(limit)\
            .all()

        # Get settings for statistics
        settings = session.query(SurgeAutoTradingSettings)\
            .filter(SurgeAutoTradingSettings.user_id == current_user.id)\
            .first()

        # Calculate statistics
        stats = {
            'total_trades': settings.total_trades if settings else 0,
            'successful_trades': settings.successful_trades if settings else 0,
            'total_profit_loss': settings.total_profit_loss if settings else 0,
            'success_rate': (settings.successful_trades / settings.total_trades * 100) if settings and settings.total_trades > 0 else 0
        }

        logger.info(f"[AutoTrading] Retrieved {len(history)} history records for user {current_user.id}")

        return jsonify({
            'success': True,
            'history': [record.to_dict() for record in history],
            'count': len(history),
            'stats': stats
        }), 200

    except Exception as e:
        logger.error(f"[AutoTrading] Error getting history for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get history'
        }), 500


@surge_auto_trading_bp.route('/positions/<int:alert_id>/close', methods=['POST'])
@require_auth
def close_position(current_user, alert_id):
    """
    Manually close a position

    Request body:
        {
            "reason": "manual_close"
        }

    Returns:
        JSON response confirming position closed
    """
    try:
        session = get_db_session()
        data = request.get_json() or {}

        # Find position
        position = session.query(SurgeAlert)\
            .filter(
                SurgeAlert.id == alert_id,
                SurgeAlert.user_id == current_user.id,
                SurgeAlert.auto_traded == True,
                SurgeAlert.status.in_(['pending', 'executed'])
            )\
            .first()

        if not position:
            return jsonify({
                'success': False,
                'error': 'Position not found or already closed'
            }), 404

        # Update status
        from datetime import datetime
        position.status = 'completed'
        position.closed_at = datetime.utcnow()

        # TODO: Calculate actual P&L from current price
        # For now, just mark as closed

        session.commit()

        logger.info(f"[AutoTrading] Position {alert_id} closed manually by user {current_user.id}")

        return jsonify({
            'success': True,
            'message': 'Position closed',
            'position': position.to_dict()
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"[AutoTrading] Error closing position for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to close position'
        }), 500
