"""
Auto Trading API Routes

Provides API endpoints for auto-trading policy management and execution.
"""

import sys
import os
from flask import Blueprint, request, jsonify, g
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.database import get_db_session, UserConfig, SwingTradingLog
from backend.common import load_api_keys, UpbitAPI
from backend.services.enhanced_auto_trading_engine import EnhancedAutoTradingEngine
from backend.middleware.auth_middleware import require_auth


# Create blueprint
auto_trading_bp = Blueprint('auto_trading', __name__)

# Global instances
upbit_api = None
trading_engine = None


def init_auto_trading():
    """Initialize auto trading engine."""
    global upbit_api, trading_engine

    try:
        access_key, secret_key = load_api_keys()
        if access_key and secret_key:
            upbit_api = UpbitAPI(access_key, secret_key)
            trading_engine = EnhancedAutoTradingEngine(upbit_api)
            print("[AutoTradingRoutes] Auto trading engine initialized")
        else:
            print("[AutoTradingRoutes] WARNING: API keys not configured")
    except Exception as e:
        print(f"[AutoTradingRoutes] ERROR initializing: {e}")


@auto_trading_bp.route('/api/auto-trading/config/<int:user_id>', methods=['GET'])
def get_user_config(user_id):
    """
    Get auto-trading configuration for a user.

    Args:
        user_id: User ID

    Returns:
        JSON with user configuration
    """
    try:
        session = get_db_session()
        try:
            config = session.query(UserConfig).filter_by(user_id=user_id).first()

            if not config:
                return jsonify({
                    "status": "error",
                    "message": "User configuration not found"
                }), 404

            return jsonify({
                "status": "success",
                "config": config.to_dict()
            })

        finally:
            session.close()

    except Exception as e:
        print(f"[AutoTradingRoutes] ERROR getting config: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@auto_trading_bp.route('/api/auto-trading/config/<int:user_id>', methods=['POST'])
def save_user_config(user_id):
    """
    Save or update auto-trading configuration for a user.

    Request body:
    {
        "auto_trading_enabled": true,
        "total_budget_krw": 100000,
        "budget_per_position_krw": 10000,
        "max_concurrent_positions": 3,
        "monitored_coins": ["KRW-BTC", "KRW-ETH"],
        "stop_loss_min": 0.03,
        "take_profit_min": 0.08,
        "emergency_stop_loss": 0.03,
        "holding_period_days": 3,
        "force_sell_after_period": false
    }

    Returns:
        JSON with save result
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400

        session = get_db_session()
        try:
            # Get or create config
            config = session.query(UserConfig).filter_by(user_id=user_id).first()

            if not config:
                # Create new config
                config = UserConfig(user_id=user_id)
                session.add(config)

            # Update fields
            if 'auto_trading_enabled' in data:
                config.auto_trading_enabled = data['auto_trading_enabled']
            if 'total_budget_krw' in data:
                config.total_budget_krw = data['total_budget_krw']
            if 'budget_per_position_krw' in data:
                config.budget_per_position_krw = data['budget_per_position_krw']
            if 'max_concurrent_positions' in data:
                config.max_concurrent_positions = data['max_concurrent_positions']
            if 'monitored_coins' in data:
                config.monitored_coins = data['monitored_coins']
            if 'stop_loss_min' in data:
                config.stop_loss_min = data['stop_loss_min']
            if 'take_profit_min' in data:
                config.take_profit_min = data['take_profit_min']
            if 'emergency_stop_loss' in data:
                config.emergency_stop_loss = data['emergency_stop_loss']
            if 'holding_period_days' in data:
                config.holding_period_days = data['holding_period_days']
            if 'force_sell_after_period' in data:
                config.force_sell_after_period = data['force_sell_after_period']

            config.updated_at = datetime.utcnow()

            session.commit()

            return jsonify({
                "status": "success",
                "message": "Configuration saved",
                "config": config.to_dict()
            })

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    except Exception as e:
        print(f"[AutoTradingRoutes] ERROR saving config: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@auto_trading_bp.route('/api/auto-trading/status', methods=['GET'])
@require_auth
def get_current_user_trading_status():
    """
    Get current authenticated user's auto-trading status.

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        JSON with status information
    """
    user_id = g.user_id
    return _get_trading_status_impl(user_id)


def _get_trading_status_impl(user_id):
    """
    Internal implementation for getting trading status.

    Args:
        user_id: User ID

    Returns:
        JSON response with status information
    """
    try:
        if not trading_engine:
            return jsonify({
                "success": False,
                "error": "Trading engine not initialized",
                "auto_trading_enabled": False,
                "open_positions_count": 0,
                "statistics": {}
            }), 200  # Return 200 with disabled status instead of 503

        # Get user config
        config = trading_engine.get_user_config(user_id)
        if not config:
            # User exists but no config yet - return default disabled state
            return jsonify({
                "success": True,
                "auto_trading_enabled": False,
                "open_positions_count": 0,
                "open_positions": [],
                "statistics": {
                    "total_trades": 0,
                    "profitable_trades": 0,
                    "win_rate": 0,
                    "total_profit": 0
                },
                "last_check": datetime.utcnow().isoformat()
            }), 200

        # Get open positions
        open_positions = trading_engine.position_tracker.get_open_positions(user_id)

        # Get statistics
        stats = trading_engine.get_user_statistics(user_id)

        return jsonify({
            "success": True,
            "auto_trading_enabled": config.get('auto_trading_enabled', False),
            "open_positions_count": len(open_positions),
            "open_positions": open_positions,
            "statistics": stats,
            "last_check": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        print(f"[AutoTradingRoutes] ERROR getting status: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "auto_trading_enabled": False,
            "open_positions_count": 0,
            "statistics": {}
        }), 500


@auto_trading_bp.route('/api/auto-trading/status/<int:user_id>', methods=['GET'])
def get_trading_status(user_id):
    """
    Get current auto-trading status for a user (legacy endpoint).

    Args:
        user_id: User ID

    Returns:
        JSON with status information
    """
    return _get_trading_status_impl(user_id)


@auto_trading_bp.route('/api/auto-trading/start/<int:user_id>', methods=['POST'])
def start_auto_trading(user_id):
    """
    Start auto-trading for a user (enable flag).

    Returns:
        JSON with result
    """
    try:
        session = get_db_session()
        try:
            config = session.query(UserConfig).filter_by(user_id=user_id).first()

            if not config:
                return jsonify({
                    "status": "error",
                    "message": "User configuration not found"
                }), 404

            config.auto_trading_enabled = True
            config.updated_at = datetime.utcnow()
            session.commit()

            return jsonify({
                "status": "success",
                "message": "Auto-trading started",
                "user_id": user_id
            })

        finally:
            session.close()

    except Exception as e:
        print(f"[AutoTradingRoutes] ERROR starting auto-trading: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@auto_trading_bp.route('/api/auto-trading/stop/<int:user_id>', methods=['POST'])
def stop_auto_trading(user_id):
    """
    Stop auto-trading for a user (disable flag).

    Returns:
        JSON with result
    """
    try:
        session = get_db_session()
        try:
            config = session.query(UserConfig).filter_by(user_id=user_id).first()

            if not config:
                return jsonify({
                    "status": "error",
                    "message": "User configuration not found"
                }), 404

            config.auto_trading_enabled = False
            config.updated_at = datetime.utcnow()
            session.commit()

            return jsonify({
                "status": "success",
                "message": "Auto-trading stopped",
                "user_id": user_id
            })

        finally:
            session.close()

    except Exception as e:
        print(f"[AutoTradingRoutes] ERROR stopping auto-trading: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@auto_trading_bp.route('/api/auto-trading/run-cycle/<int:user_id>', methods=['POST'])
def run_trading_cycle(user_id):
    """
    Manually trigger one auto-trading cycle for a user.

    Returns:
        JSON with cycle results
    """
    try:
        if not trading_engine:
            return jsonify({
                "status": "error",
                "message": "Trading engine not initialized"
            }), 503

        # Run cycle
        result = trading_engine.run_auto_trading_cycle(user_id)

        return jsonify(result)

    except Exception as e:
        print(f"[AutoTradingRoutes] ERROR running cycle: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@auto_trading_bp.route('/api/auto-trading/logs/<int:user_id>', methods=['GET'])
def get_trading_logs(user_id):
    """
    Get trading logs for a user.

    Query parameters:
        - limit: Maximum number of logs (default: 50)
        - offset: Offset for pagination (default: 0)

    Returns:
        JSON with logs
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        session = get_db_session()
        try:
            logs = session.query(SwingTradingLog).filter_by(user_id=user_id)\
                .order_by(SwingTradingLog.log_time.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()

            total_count = session.query(SwingTradingLog).filter_by(user_id=user_id).count()

            return jsonify({
                "status": "success",
                "logs": [log.to_dict() for log in logs],
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            })

        finally:
            session.close()

    except Exception as e:
        print(f"[AutoTradingRoutes] ERROR getting logs: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@auto_trading_bp.route('/api/auto-trading/positions/<int:user_id>', methods=['GET'])
def get_user_positions(user_id):
    """
    Get all positions (open and closed) for a user.

    Returns:
        JSON with positions
    """
    try:
        if not trading_engine:
            return jsonify({
                "status": "error",
                "message": "Trading engine not initialized"
            }), 503

        open_positions = trading_engine.position_tracker.get_open_positions(user_id)
        statistics = trading_engine.position_tracker.get_statistics(user_id)

        return jsonify({
            "status": "success",
            "open_positions": open_positions,
            "statistics": statistics
        })

    except Exception as e:
        print(f"[AutoTradingRoutes] ERROR getting positions: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# Initialize when module is loaded
init_auto_trading()
