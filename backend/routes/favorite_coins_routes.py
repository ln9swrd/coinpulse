# -*- coding: utf-8 -*-
"""
Favorite Coins Routes
사용자 관심 코인 관리 API

참고 문서: docs/features/SURGE_ALERT_SYSTEM.md
"""

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
import logging

from backend.database.connection import get_db_session
from backend.utils.auth_utils import require_auth
from backend.models.surge_alert_models import UserFavoriteCoin
from backend.models.plan_features import get_user_features

logger = logging.getLogger(__name__)

# Create Blueprint
favorite_coins_bp = Blueprint('favorite_coins', __name__, url_prefix='/api/user/favorite-coins')


@favorite_coins_bp.route('', methods=['GET'])
@require_auth
def get_favorite_coins(current_user):
    """
    Get user's favorite coins

    Returns:
        JSON response with favorite coins list
    """
    try:
        session = get_db_session()

        # Get user's favorite coins
        favorites = session.query(UserFavoriteCoin)\
            .filter(UserFavoriteCoin.user_id == current_user.id)\
            .order_by(UserFavoriteCoin.created_at.asc())\
            .all()

        logger.info(f"[FavoriteCoins] User {current_user.id} has {len(favorites)} favorite coins")

        return jsonify({
            'success': True,
            'favorites': [fav.to_dict() for fav in favorites],
            'count': len(favorites),
            'max_favorites': 5
        }), 200

    except Exception as e:
        logger.error(f"[FavoriteCoins] Error getting favorites for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get favorite coins'
        }), 500


@favorite_coins_bp.route('', methods=['POST'])
@require_auth
def add_favorite_coin(current_user):
    """
    Add a coin to user's favorites

    Request body:
        {
            "coin": "BTC",
            "alert_enabled": true,
            "risk_level": "moderate",
            "stop_loss_enabled": false
        }

    Returns:
        JSON response with created favorite coin
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

        # Check if user's plan allows favorite coins
        plan = current_user.plan or 'free'
        features = get_user_features(plan)

        if not features.get('favorite_coins', False):
            return jsonify({
                'success': False,
                'error': 'Your plan does not support favorite coins. Please upgrade to Basic or Pro plan.'
            }), 403

        # Check if user already has 5 favorites (maximum)
        existing_count = session.query(UserFavoriteCoin)\
            .filter(UserFavoriteCoin.user_id == current_user.id)\
            .count()

        if existing_count >= 5:
            return jsonify({
                'success': False,
                'error': 'Maximum 5 favorite coins allowed'
            }), 400

        # Check if coin already exists
        existing = session.query(UserFavoriteCoin)\
            .filter(
                UserFavoriteCoin.user_id == current_user.id,
                UserFavoriteCoin.coin == coin
            )\
            .first()

        if existing:
            return jsonify({
                'success': False,
                'error': f'{coin} is already in your favorites'
            }), 400

        # Create new favorite coin
        favorite = UserFavoriteCoin(
            user_id=current_user.id,
            coin=coin,
            market=UserFavoriteCoin.coin_to_market(coin),
            alert_enabled=data.get('alert_enabled', True),
            auto_trading_enabled=data.get('auto_trading_enabled', False),
            risk_level=data.get('risk_level', 'moderate'),
            stop_loss_enabled=data.get('stop_loss_enabled', False)
        )

        session.add(favorite)
        session.commit()

        logger.info(f"[FavoriteCoins] User {current_user.id} added {coin} to favorites")

        return jsonify({
            'success': True,
            'favorite': favorite.to_dict(),
            'message': f'{coin} added to favorites'
        }), 201

    except IntegrityError:
        session.rollback()
        return jsonify({
            'success': False,
            'error': 'This coin is already in your favorites'
        }), 400

    except Exception as e:
        session.rollback()
        logger.error(f"[FavoriteCoins] Error adding favorite for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to add favorite coin'
        }), 500


@favorite_coins_bp.route('/<coin>', methods=['PUT'])
@require_auth
def update_favorite_coin(current_user, coin):
    """
    Update favorite coin settings

    Request body:
        {
            "alert_enabled": true,
            "risk_level": "aggressive",
            "stop_loss_enabled": true
        }

    Returns:
        JSON response with updated favorite coin
    """
    try:
        session = get_db_session()
        data = request.get_json()

        coin = coin.upper()

        # Find favorite coin
        favorite = session.query(UserFavoriteCoin)\
            .filter(
                UserFavoriteCoin.user_id == current_user.id,
                UserFavoriteCoin.coin == coin
            )\
            .first()

        if not favorite:
            return jsonify({
                'success': False,
                'error': f'{coin} not found in your favorites'
            }), 404

        # Update fields
        if 'alert_enabled' in data:
            favorite.alert_enabled = data['alert_enabled']

        if 'auto_trading_enabled' in data:
            # Check if Pro plan for auto trading
            plan = current_user.plan or 'free'
            if data['auto_trading_enabled'] and plan.lower() != 'pro':
                return jsonify({
                    'success': False,
                    'error': 'Auto trading requires Pro plan'
                }), 403
            favorite.auto_trading_enabled = data['auto_trading_enabled']

        if 'risk_level' in data:
            if data['risk_level'] not in ['conservative', 'moderate', 'aggressive']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid risk level. Must be: conservative, moderate, or aggressive'
                }), 400
            favorite.risk_level = data['risk_level']

        if 'stop_loss_enabled' in data:
            favorite.stop_loss_enabled = data['stop_loss_enabled']

        if 'min_confidence' in data:
            favorite.min_confidence = data['min_confidence']

        if 'max_position_size' in data:
            favorite.max_position_size = data['max_position_size']

        session.commit()

        logger.info(f"[FavoriteCoins] User {current_user.id} updated {coin} settings")

        return jsonify({
            'success': True,
            'favorite': favorite.to_dict(),
            'message': f'{coin} settings updated'
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"[FavoriteCoins] Error updating favorite for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update favorite coin'
        }), 500


@favorite_coins_bp.route('/<coin>', methods=['DELETE'])
@require_auth
def delete_favorite_coin(current_user, coin):
    """
    Remove coin from user's favorites

    Returns:
        JSON response confirming deletion
    """
    try:
        session = get_db_session()
        coin = coin.upper()

        # Find and delete favorite coin
        favorite = session.query(UserFavoriteCoin)\
            .filter(
                UserFavoriteCoin.user_id == current_user.id,
                UserFavoriteCoin.coin == coin
            )\
            .first()

        if not favorite:
            return jsonify({
                'success': False,
                'error': f'{coin} not found in your favorites'
            }), 404

        session.delete(favorite)
        session.commit()

        logger.info(f"[FavoriteCoins] User {current_user.id} removed {coin} from favorites")

        return jsonify({
            'success': True,
            'message': f'{coin} removed from favorites'
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"[FavoriteCoins] Error deleting favorite for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to remove favorite coin'
        }), 500


@favorite_coins_bp.route('/bulk', methods=['POST'])
@require_auth
def set_favorite_coins_bulk(current_user):
    """
    Set all favorite coins at once (replaces existing)

    Request body:
        {
            "coins": [
                {
                    "coin": "BTC",
                    "alert_enabled": true,
                    "risk_level": "moderate",
                    "stop_loss_enabled": false
                },
                ...
            ]
        }

    Returns:
        JSON response with all favorite coins
    """
    try:
        session = get_db_session()
        data = request.get_json()

        if not data or 'coins' not in data:
            return jsonify({
                'success': False,
                'error': 'coins array is required'
            }), 400

        coins_data = data['coins']

        # Validate count
        if len(coins_data) > 5:
            return jsonify({
                'success': False,
                'error': 'Maximum 5 favorite coins allowed'
            }), 400

        # Check plan
        plan = current_user.plan or 'free'
        features = get_user_features(plan)

        if not features.get('favorite_coins', False):
            return jsonify({
                'success': False,
                'error': 'Your plan does not support favorite coins'
            }), 403

        # Delete all existing favorites
        session.query(UserFavoriteCoin)\
            .filter(UserFavoriteCoin.user_id == current_user.id)\
            .delete()

        # Create new favorites
        favorites = []
        for coin_data in coins_data:
            coin = coin_data.get('coin', '').upper()
            if not coin:
                continue

            favorite = UserFavoriteCoin(
                user_id=current_user.id,
                coin=coin,
                market=UserFavoriteCoin.coin_to_market(coin),
                alert_enabled=coin_data.get('alert_enabled', True),
                auto_trading_enabled=coin_data.get('auto_trading_enabled', False),
                risk_level=coin_data.get('risk_level', 'moderate'),
                stop_loss_enabled=coin_data.get('stop_loss_enabled', False)
            )
            session.add(favorite)
            favorites.append(favorite)

        session.commit()

        logger.info(f"[FavoriteCoins] User {current_user.id} set {len(favorites)} favorite coins")

        return jsonify({
            'success': True,
            'favorites': [fav.to_dict() for fav in favorites],
            'count': len(favorites),
            'message': f'{len(favorites)} favorite coins set'
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"[FavoriteCoins] Error setting bulk favorites for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to set favorite coins'
        }), 500
