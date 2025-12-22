# -*- coding: utf-8 -*-
"""
Investment Advisory Coins Routes
투자조언 알림 코인 관리 API

참고 문서: docs/features/SURGE_ALERT_SYSTEM.md v2.0
"""

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
import logging

from backend.database.connection import get_db_session
from backend.utils.auth_utils import require_auth
from backend.models.surge_alert_models import UserAdvisoryCoin
from backend.models.plan_features import get_user_features

logger = logging.getLogger(__name__)

# Create Blueprint
advisory_coins_bp = Blueprint('advisory_coins', __name__, url_prefix='/api/user/advisory-coins')


@advisory_coins_bp.route('', methods=['GET'])
@require_auth
def get_advisory_coins(current_user):
    """
    Get user's investment advisory coins

    Returns:
        JSON response with advisory coins list
    """
    try:
        session = get_db_session()

        # Get user's advisory coins
        advisory_coins = session.query(UserAdvisoryCoin)\
            .filter(UserAdvisoryCoin.user_id == current_user.id)\
            .order_by(UserAdvisoryCoin.created_at.asc())\
            .all()

        # Get user's plan features
        plan = current_user.plan or 'free'
        features = get_user_features(plan)
        max_coins = features.get('max_advisory_coins', 0)

        logger.info(f"[AdvisoryCoins] User {current_user.id} has {len(advisory_coins)}/{max_coins} advisory coins")

        return jsonify({
            'success': True,
            'advisory_coins': [coin.to_dict() for coin in advisory_coins],
            'count': len(advisory_coins),
            'max_coins': max_coins
        }), 200

    except Exception as e:
        logger.error(f"[AdvisoryCoins] Error getting advisory coins for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get advisory coins'
        }), 500


@advisory_coins_bp.route('', methods=['POST'])
@require_auth
def add_advisory_coin(current_user):
    """
    Add a coin to user's advisory list

    Request body:
        {
            "coin": "BTC"
        }

    Returns:
        JSON response with created advisory coin
    """
    try:
        session = get_db_session()
        data = request.get_json()

        # Validate required fields
        if not data or 'coin' not in data:
            return jsonify({
                'success': False,
                'error': 'Coin symbol is required'
            }), 400

        coin = data['coin'].upper()

        # Check if user's plan allows advisory coins
        plan = current_user.plan or 'free'
        features = get_user_features(plan)

        if not features.get('advisory_coins', False):
            return jsonify({
                'success': False,
                'error': 'Your plan does not support advisory coins. Please upgrade to Basic or Pro plan.'
            }), 403

        # Check max coins limit
        max_coins = features.get('max_advisory_coins', 0)
        existing_count = session.query(UserAdvisoryCoin)\
            .filter(UserAdvisoryCoin.user_id == current_user.id)\
            .count()

        if existing_count >= max_coins:
            return jsonify({
                'success': False,
                'error': f'Maximum {max_coins} advisory coins allowed for {plan} plan'
            }), 400

        # Check if coin already exists
        existing = session.query(UserAdvisoryCoin)\
            .filter(
                UserAdvisoryCoin.user_id == current_user.id,
                UserAdvisoryCoin.coin == coin
            )\
            .first()

        if existing:
            return jsonify({
                'success': False,
                'error': f'{coin} is already in your advisory list'
            }), 400

        # Create new advisory coin
        advisory_coin = UserAdvisoryCoin(
            user_id=current_user.id,
            coin=coin,
            market=UserAdvisoryCoin.coin_to_market(coin),
            alert_enabled=True
        )

        session.add(advisory_coin)
        session.commit()

        logger.info(f"[AdvisoryCoins] User {current_user.id} added {coin} to advisory list")

        return jsonify({
            'success': True,
            'advisory_coin': advisory_coin.to_dict(),
            'message': f'{coin} added to advisory list'
        }), 201

    except IntegrityError:
        session.rollback()
        return jsonify({
            'success': False,
            'error': 'This coin is already in your advisory list'
        }), 400

    except Exception as e:
        session.rollback()
        logger.error(f"[AdvisoryCoins] Error adding advisory coin for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to add advisory coin'
        }), 500


@advisory_coins_bp.route('/<coin>', methods=['DELETE'])
@require_auth
def delete_advisory_coin(current_user, coin):
    """
    Remove coin from user's advisory list

    Returns:
        JSON response confirming deletion
    """
    try:
        session = get_db_session()
        coin = coin.upper()

        # Find and delete advisory coin
        advisory_coin = session.query(UserAdvisoryCoin)\
            .filter(
                UserAdvisoryCoin.user_id == current_user.id,
                UserAdvisoryCoin.coin == coin
            )\
            .first()

        if not advisory_coin:
            return jsonify({
                'success': False,
                'error': f'{coin} not found in your advisory list'
            }), 404

        session.delete(advisory_coin)
        session.commit()

        logger.info(f"[AdvisoryCoins] User {current_user.id} removed {coin} from advisory list")

        return jsonify({
            'success': True,
            'message': f'{coin} removed from advisory list'
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"[AdvisoryCoins] Error deleting advisory coin for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to remove advisory coin'
        }), 500
