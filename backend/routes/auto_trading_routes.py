"""
Auto Trading API Routes (USER-SPECIFIC)

Provides API endpoints for auto-trading policy management and execution.

IMPORTANT: All routes use user-specific Upbit API keys from database.
Each user has their own trading engine instance.
"""

import sys
import os
from flask import Blueprint, request, jsonify, g
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.database import get_db_session, UserConfig, SwingTradingLog
from backend.services.enhanced_auto_trading_engine import EnhancedAutoTradingEngine
from backend.middleware.auth_middleware import require_auth
from backend.middleware.user_api_keys import get_user_upbit_api, get_user_from_token


# Create blueprint
auto_trading_bp = Blueprint('auto_trading', __name__)


@auto_trading_bp.route('/auto-trading/status/<int:user_id>', methods=['GET'])
@require_auth
def get_auto_trading_status(user_id):
    """
    Get auto-trading status for a user (USER-SPECIFIC)

    Returns:
        {
            "auto_trading_enabled": true/false,
            "open_positions_count": 3,
            "statistics": {...}
        }
    """
    try:
        # Verify user authorization
        current_user_id = g.user_id
        if current_user_id != user_id:
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 403

        session = get_db_session()
        try:
            # Get user config
            config = session.query(UserConfig).filter_by(user_id=user_id).first()

            if not config:
                return jsonify({
                    "success": True,
                    "auto_trading_enabled": False,
                    "open_positions_count": 0,
                    "statistics": {
                        "total_trades": 0,
                        "win_rate": 0,
                        "total_profit": 0
                    }
                })

            # Get statistics from trading logs
            logs = session.query(SwingTradingLog).filter_by(user_id=user_id).all()

            total_trades = len(logs)
            winning_trades = [log for log in logs if log.profit_loss and log.profit_loss > 0]
            win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
            total_profit = sum([log.profit_loss for log in logs if log.profit_loss]) if logs else 0

            # Count open positions
            open_positions = [log for log in logs if log.status == 'active']

            print(f"[AutoTrading] User {user_id}: {len(open_positions)} open positions, win_rate={win_rate:.1f}%")

            return jsonify({
                "success": True,
                "auto_trading_enabled": config.auto_trading_enabled,
                "open_positions_count": len(open_positions),
                "statistics": {
                    "total_trades": total_trades,
                    "win_rate": win_rate,
                    "total_profit": total_profit
                },
                "last_check": datetime.now().isoformat()
            })

        finally:
            session.close()

    except Exception as e:
        print(f"[AutoTrading] Error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@auto_trading_bp.route('/auto-trading/config/<int:user_id>', methods=['GET'])
@require_auth
def get_user_config(user_id):
    """
    Get auto-trading configuration for a user (USER-SPECIFIC)
    """
    try:
        # Verify user authorization
        current_user_id = g.user_id
        if current_user_id != user_id:
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 403

        session = get_db_session()
        try:
            config = session.query(UserConfig).filter_by(user_id=user_id).first()

            if not config:
                # Return default config
                return jsonify({
                    "success": True,
                    "config": {
                        "auto_trading_enabled": False,
                        "total_budget_krw": 1000000,
                        "budget_per_position_krw": 100000,
                        "max_concurrent_positions": 3,
                        "monitored_coins": [],
                        "stop_loss_min": 0.03,
                        "take_profit_min": 0.08,
                        "emergency_stop_loss": 0.03,
                        "holding_period_days": 3,
                        "force_sell_after_period": False
                    }
                })

            return jsonify({
                "success": True,
                "config": config.to_dict()
            })

        finally:
            session.close()

    except Exception as e:
        print(f"[AutoTrading] Error getting config: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@auto_trading_bp.route('/auto-trading/config/<int:user_id>', methods=['POST', 'PUT'])
@require_auth
def save_user_config(user_id):
    """
    Save or update auto-trading configuration (USER-SPECIFIC)
    """
    try:
        # Verify user authorization
        current_user_id = g.user_id
        if current_user_id != user_id:
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 403

        data = request.get_json()

        session = get_db_session()
        try:
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
                config.monitored_coins = ','.join(data['monitored_coins']) if isinstance(data['monitored_coins'], list) else data['monitored_coins']
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

            config.updated_at = datetime.now()

            session.commit()

            print(f"[AutoTrading] User {user_id}: Config saved")

            return jsonify({
                "success": True,
                "message": "Configuration saved successfully",
                "config": config.to_dict()
            })

        finally:
            session.close()

    except Exception as e:
        print(f"[AutoTrading] Error saving config: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@auto_trading_bp.route('/auto-trading/execute/<int:user_id>', methods=['POST'])
@require_auth
def execute_auto_trading(user_id):
    """
    Execute auto-trading cycle for a user (USER-SPECIFIC)

    This creates a trading engine instance with user's API keys and runs one cycle.
    """
    try:
        # Verify user authorization
        current_user_id = g.user_id
        if current_user_id != user_id:
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 403

        # Get user-specific Upbit API
        user_upbit_api = get_user_upbit_api()

        if not user_upbit_api:
            return jsonify({
                "success": False,
                "error": "Upbit API keys not configured. Please add your API keys in Settings.",
                "error_code": "NO_API_KEYS"
            }), 400

        # Get user config
        session = get_db_session()
        try:
            config = session.query(UserConfig).filter_by(user_id=user_id).first()

            if not config or not config.auto_trading_enabled:
                return jsonify({
                    "success": False,
                    "error": "Auto-trading is not enabled"
                }), 400

            # Create user-specific trading engine
            trading_engine = EnhancedAutoTradingEngine(user_upbit_api)

            # Execute one trading cycle
            result = trading_engine.run_cycle(config)

            print(f"[AutoTrading] User {user_id}: Cycle executed - {result}")

            return jsonify({
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })

        finally:
            session.close()

    except Exception as e:
        print(f"[AutoTrading] Error executing: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@auto_trading_bp.route('/auto-trading/positions/<int:user_id>', methods=['GET'])
@require_auth
def get_open_positions(user_id):
    """
    Get all open positions for a user (USER-SPECIFIC)
    """
    try:
        # Verify user authorization
        current_user_id = g.user_id
        if current_user_id != user_id:
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 403

        session = get_db_session()
        try:
            positions = session.query(SwingTradingLog).filter_by(
                user_id=user_id,
                status='active'
            ).all()

            positions_data = []
            for pos in positions:
                positions_data.append({
                    'id': pos.id,
                    'market': pos.market,
                    'entry_price': float(pos.entry_price) if pos.entry_price else 0,
                    'quantity': float(pos.quantity) if pos.quantity else 0,
                    'current_value': float(pos.current_value) if pos.current_value else 0,
                    'profit_loss': float(pos.profit_loss) if pos.profit_loss else 0,
                    'profit_rate': float(pos.profit_rate) if pos.profit_rate else 0,
                    'entry_date': pos.entry_date.isoformat() if pos.entry_date else None,
                    'holding_days': (datetime.now() - pos.entry_date).days if pos.entry_date else 0
                })

            print(f"[AutoTrading] User {user_id}: {len(positions_data)} open positions")

            return jsonify({
                "success": True,
                "positions": positions_data,
                "count": len(positions_data)
            })

        finally:
            session.close()

    except Exception as e:
        print(f"[AutoTrading] Error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@auto_trading_bp.route('/auto-trading/history/<int:user_id>', methods=['GET'])
@require_auth
def get_trading_history(user_id):
    """
    Get trading history for a user (USER-SPECIFIC)
    """
    try:
        # Verify user authorization
        current_user_id = g.user_id
        if current_user_id != user_id:
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 403

        limit = request.args.get('limit', 50, type=int)

        session = get_db_session()
        try:
            logs = session.query(SwingTradingLog).filter_by(
                user_id=user_id
            ).order_by(SwingTradingLog.entry_date.desc()).limit(limit).all()

            history_data = []
            for log in logs:
                history_data.append({
                    'id': log.id,
                    'market': log.market,
                    'status': log.status,
                    'entry_price': float(log.entry_price) if log.entry_price else 0,
                    'exit_price': float(log.exit_price) if log.exit_price else 0,
                    'quantity': float(log.quantity) if log.quantity else 0,
                    'profit_loss': float(log.profit_loss) if log.profit_loss else 0,
                    'profit_rate': float(log.profit_rate) if log.profit_rate else 0,
                    'entry_date': log.entry_date.isoformat() if log.entry_date else None,
                    'exit_date': log.exit_date.isoformat() if log.exit_date else None
                })

            print(f"[AutoTrading] User {user_id}: {len(history_data)} history records")

            return jsonify({
                "success": True,
                "history": history_data,
                "count": len(history_data)
            })

        finally:
            session.close()

    except Exception as e:
        print(f"[AutoTrading] Error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# NOTE: init_auto_trading() is NO LONGER needed
# Each user gets their own trading engine instance per request
