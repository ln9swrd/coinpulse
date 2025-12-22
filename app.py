"""
CoinPulse - Integrated Web Application Server
Combines all services into a single Flask application

Features:
- User Authentication (JWT)
- Trading Chart API
- Portfolio Management
- Auto Trading Engine
- Subscription Management
- Background Order Sync
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import backend common modules
from backend.common import UpbitAPI
from backend.services import ChartService, HoldingsService

# Import all route blueprints
from backend.routes.auth_routes import auth_bp
from backend.routes.user_routes import user_bp  # User API routes (plan, profile)
from backend.routes.user_signals_routes import user_signals_bp  # User signals history
from backend.routes.telegram_link_routes import telegram_link_bp  # Telegram account linking
from backend.routes.holdings_routes import holdings_bp
from backend.routes.auto_trading_routes import auto_trading_bp
from backend.routes.subscription_routes import subscription_bp  # ✅ Re-enabled
from backend.routes.payment import payment_bp  # Payment routes
from backend.routes.health_routes import health_bp
from backend.routes.admin import admin_bp  # Admin routes for beta tester management
from backend.routes.users_admin import users_admin_bp  # User admin routes
from backend.routes.benefits_admin import benefits_admin_bp  # ✅ Re-enabled - Universal benefits management
from backend.routes.suspension_admin import suspension_admin_bp  # ✅ Re-enabled - User suspension management
from backend.routes.plan_admin import plan_admin_bp  # Plan configuration management
from backend.routes.stats_routes import stats_bp  # Statistics API
from backend.routes.surge_routes import surge_bp  # Surge prediction MVP (81.25% accuracy)
from backend.routes.monitoring_routes import monitoring_bp  # Signal scheduler monitoring
from backend.routes.signal_admin_routes import signal_admin_bp  # Signal admin panel
from backend.routes.scheduler_admin import scheduler_admin_bp  # Subscription scheduler admin
from backend.routes.upbit_proxy_routes import upbit_proxy_bp  # Upbit API proxy for chart data
from backend.routes.subscription_admin import subscription_admin_bp  # Admin subscription management
from backend.routes.features_admin import features_admin_bp  # Admin feature customization
from backend.routes.payment_confirmation import payment_confirm_bp  # Payment confirmation (bank transfer)
from backend.routes.payment_confirmation_admin import payment_confirm_admin_bp  # Admin payment confirmation review
from backend.routes.telegram_webhook import telegram_webhook_bp  # Telegram bot webhook for auto payment processing
from backend.routes.referral_routes import referral_bp  # Referral system (friend invitation)
from backend.models.referral import ReferralCode, Referral  # Import models to register with SQLAlchemy

# Import WebSocket service (Phase 3)
from backend.services.websocket_service import init_websocket_service, setup_socketio_handlers


# ============================================================================
# Configuration Management
# ============================================================================

def load_config():
    """
    Load configuration from multiple sources with priority:
    1. Environment variables (highest priority)
    2. config.json file
    3. Default values (lowest priority)
    """
    # Try to load from config file
    config_file = os.getenv('CONFIG_FILE', 'config.json')
    default_config = {
        "server": {
            "name": "CoinPulse Web Service",
            "host": "0.0.0.0",
            "port": 8080,
            "debug": True
        },
        "api": {
            "upbit_base_url": "https://api.upbit.com",
            "request_timeout": 5,
            "max_retries": 3
        },
        "cache": {
            "default_ttl": 60,
            "enabled": True
        },
        "cors": {
            "origins": [
                "http://localhost:8080",
                "http://127.0.0.1:8080",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "*"
            ]
        },
        "database": {
            "url": os.getenv('DATABASE_URL', 'sqlite:///data/coinpulse.db')
        },
        "paths": {
            "frontend": "frontend",
            "static": "frontend",
            "logs": "logs"
        }
    }

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            file_config = json.load(f)
            # Merge with defaults
            default_config.update(file_config)
            print(f"[Config] Loaded from {config_file}")
    except FileNotFoundError:
        print(f"[Config] {config_file} not found, using defaults")

    # Override with environment variables
    if os.getenv('SERVER_PORT'):
        default_config['server']['port'] = int(os.getenv('SERVER_PORT'))
    if os.getenv('SERVER_HOST'):
        default_config['server']['host'] = os.getenv('SERVER_HOST')
    if os.getenv('DEBUG_MODE'):
        default_config['server']['debug'] = os.getenv('DEBUG_MODE').lower() == 'true'

    return default_config


# Load configuration
CONFIG = load_config()


# ============================================================================
# Logging Setup
# ============================================================================

# Import enhanced logging service
from backend.services.logging_service import setup_logging as setup_enhanced_logging

# Note: setup_enhanced_logging will be called after app creation
# to have access to app instance
logger = logging.getLogger(__name__)


# ============================================================================
# Flask Application Setup
# ============================================================================

app = Flask(__name__,
            static_folder=None,  # Disable Flask's built-in static file handler
            static_url_path=None)  # Use custom serve_static() function instead

# Secret key for session management
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# JSON configuration
app.config['JSON_AS_ASCII'] = False  # Support Korean characters
app.config['JSON_SORT_KEYS'] = False

# Database configuration
app.config['DATABASE_URL'] = CONFIG['database']['url']

# CORS setup
cors_origins = CONFIG['cors']['origins']
CORS(app, origins=cors_origins, supports_credentials=True)

# Enhanced logging setup (must be done after app creation)
setup_enhanced_logging(app)

# Performance middleware (gzip compression, caching, logging)
from backend.middleware.performance import setup_performance_middleware
setup_performance_middleware(app)

# Security middleware (rate limiting, security headers, input validation)
from backend.middleware.security import setup_security_middleware
setup_security_middleware(app)

# ============================================================================
# WebSocket (SocketIO) Setup - Phase 3
# ============================================================================

# Initialize SocketIO with the Flask app
socketio = SocketIO(
    app,
    cors_allowed_origins=cors_origins,
    async_mode='threading',  # Use threading mode for compatibility
    ping_interval=25,
    ping_timeout=60,
    max_http_buffer_size=1000000
)

logger.info("WebSocket (SocketIO) initialized")


# ============================================================================
# Blueprint Registration
# ============================================================================

def register_blueprints():
    """Register all route blueprints"""
    # NOTE: Holdings routes now use user-specific API keys from database (no global initialization needed)

    blueprints = [
        (auth_bp, '/api/auth'),
        (user_bp, None),  # User API routes (already has /api/user prefix)
        (user_signals_bp, None),  # User signals routes (already has /api/user/signals prefix)
        (telegram_link_bp, None),  # Telegram linking routes (already has /api/telegram prefix)
        (holdings_bp, None),  # Holdings routes (already has /api prefix in routes)
        (auto_trading_bp, '/api'),
        (payment_bp, '/api/payment'),  # Payment routes
        (subscription_bp, None),  # ✅ Re-enabled - Subscription routes (already has /api/subscription prefix)
        (health_bp, '/api'),  # Phase 5 - Health monitoring
        (admin_bp, None),  # Admin routes (already has /api/admin prefix)
        (users_admin_bp, None),  # User admin routes
        (benefits_admin_bp, None),  # ✅ Re-enabled - Benefits admin (already has /api/admin/benefits prefix)
        (suspension_admin_bp, None),  # ✅ Re-enabled - Suspension admin (already has /api/admin/suspensions prefix)
        (plan_admin_bp, None),  # Plan admin (already has /api/admin/plans prefix)
        (stats_bp, None),  # Statistics API (already has /api/stats prefix)
        (surge_bp, '/api'),  # Surge prediction API (81.25% backtest accuracy)
        (monitoring_bp, '/api/monitoring'),  # Signal scheduler monitoring
        (signal_admin_bp, None),  # Signal admin panel (already has /api/admin/signals prefix)
        (scheduler_admin_bp, '/api/admin'),  # Subscription renewal scheduler admin
        (upbit_proxy_bp, None),  # Upbit API proxy (already has /api/upbit prefix)
        (subscription_admin_bp, None),  # Admin subscription management (already has /api/admin/subscriptions prefix)
        (features_admin_bp, None),  # Admin feature customization (already has /api/admin/features prefix)
        (payment_confirm_bp, None),  # Payment confirmation (already has /api/payment-confirm prefix)
        (payment_confirm_admin_bp, None),  # Admin payment confirmation (already has /api/admin/payment-confirmations prefix)
        (telegram_webhook_bp, None),  # Telegram bot webhook for auto payment processing (already has /api/telegram prefix)
        (referral_bp, None)  # Referral system (already has /api/referral prefix)
    ]

    for blueprint, url_prefix in blueprints:
        # Check if blueprint already has url_prefix
        if hasattr(blueprint, 'url_prefix') and blueprint.url_prefix:
            app.register_blueprint(blueprint)
            logger.info(f"Registered blueprint: {blueprint.name} at {blueprint.url_prefix}")
        else:
            app.register_blueprint(blueprint, url_prefix=url_prefix)
            logger.info(f"Registered blueprint: {blueprint.name} at {url_prefix}")


register_blueprints()


# ============================================================================
# Static File Serving
# ============================================================================

@app.route('/')
def index():
    """Serve the landing page"""
    return send_from_directory(CONFIG['paths']['frontend'], 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from frontend directory with proper MIME types"""
    try:
        import os
        from flask import make_response

        # Get full file path
        file_path = os.path.join(CONFIG['paths']['frontend'], path)

        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return jsonify({'error': 'File not found'}), 404

        # Determine MIME type
        mimetype = 'application/octet-stream'  # Default
        if path.endswith('.js'):
            mimetype = 'application/javascript; charset=utf-8'
        elif path.endswith('.css'):
            mimetype = 'text/css; charset=utf-8'
        elif path.endswith('.json'):
            mimetype = 'application/json; charset=utf-8'
        elif path.endswith('.html'):
            mimetype = 'text/html; charset=utf-8'
        elif path.endswith('.png'):
            mimetype = 'image/png'
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            mimetype = 'image/jpeg'
        elif path.endswith('.svg'):
            mimetype = 'image/svg+xml; charset=utf-8'
        elif path.endswith('.ico'):
            mimetype = 'image/x-icon'
        elif path.endswith('.woff') or path.endswith('.woff2'):
            mimetype = 'font/woff2'
        elif path.endswith('.ttf'):
            mimetype = 'font/ttf'

        # Read file content
        with open(file_path, 'rb') as f:
            content = f.read()

        # Create response with explicit Content-Type
        response = make_response(content)
        response.headers['Content-Type'] = mimetype
        response.headers['Content-Length'] = len(content)

        return response
    except Exception as e:
        logger.error(f"Error serving static file {path}: {e}")
        return jsonify({'error': 'File not found'}), 404


# ============================================================================
# Health Check & Status Endpoints
# ============================================================================

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': CONFIG['server']['name'],
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/api/status')
def api_status():
    """Detailed API status endpoint"""
    # Check Upbit API connectivity
    upbit_status = 'unknown'
    try:
        import requests
        response = requests.get(f"{CONFIG['api']['upbit_base_url']}/v1/market/all", timeout=3)
        upbit_status = 'connected' if response.status_code == 200 else 'error'
    except Exception as e:
        upbit_status = f'error: {str(e)}'
        logger.error(f"Upbit API health check failed: {e}")

    # Check database connectivity
    db_status = 'unknown'
    try:
        db_url = CONFIG['database']['url']
        if db_url.startswith('sqlite'):
            db_path = db_url.replace('sqlite:///', '')
            db_status = 'connected' if os.path.exists(db_path) else 'not_found'
        elif db_url.startswith('postgres'):
            # For PostgreSQL, we'd need to actually query it
            db_status = 'configured'
    except Exception as e:
        db_status = f'error: {str(e)}'
        logger.error(f"Database health check failed: {e}")

    return jsonify({
        'service': CONFIG['server']['name'],
        'status': 'operational',
        'components': {
            'upbit_api': upbit_status,
            'database': db_status,
            'authentication': 'operational',
            'trading': 'operational'
        },
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/api/trading/policies', methods=['GET', 'POST'])
def manage_trading_policies():
    """
    Trading policies management (USER-SPECIFIC)

    GET: Return user's trading configuration as policies format
    POST: Update user's trading configuration from policies format

    Note: This endpoint bridges the old policies format (from simple_dual_server.py)
    with the new UserConfig database model.
    """
    from backend.database import get_db_session, UserConfig
    from backend.middleware.auth_middleware import require_auth
    from flask import g

    # Require authentication
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            # Return empty policies for unauthenticated users (backward compatibility)
            if request.method == 'GET':
                return jsonify({
                    "auto_trading_enabled": False,
                    "coins": {}
                })
            else:
                return jsonify({"success": False, "error": "Authentication required"}), 401

        # Verify token
        token = auth_header.split(' ')[1]
        from backend.middleware.auth_middleware import verify_access_token
        user_data = verify_access_token(token)
        if not user_data:
            if request.method == 'GET':
                return jsonify({
                    "auto_trading_enabled": False,
                    "coins": {}
                })
            else:
                return jsonify({"success": False, "error": "Invalid token"}), 401

        user_id = user_data['user_id']

    except Exception as e:
        logger.error(f"[TradingPolicies] Auth error: {e}")
        if request.method == 'GET':
            return jsonify({
                "auto_trading_enabled": False,
                "coins": {}
            })
        else:
            return jsonify({"success": False, "error": "Authentication failed"}), 401

    session = get_db_session()
    try:
        if request.method == 'GET':
            # Get user's config from database
            config = session.query(UserConfig).filter_by(user_id=user_id).first()

            if not config:
                # Return default policies if no config exists
                return jsonify({
                    "auto_trading_enabled": False,
                    "coins": {}
                })

            # Convert UserConfig to policies format
            monitored_coins = config.monitored_coins or []
            coins_policies = {}
            for coin in monitored_coins:
                coins_policies[coin] = {
                    "enabled": True,
                    "budget": config.budget_per_position_krw,
                    "take_profit": float(config.take_profit_min),
                    "stop_loss": float(config.stop_loss_min)
                }

            policies = {
                "auto_trading_enabled": config.auto_trading_enabled,
                "swing_trading_enabled": config.swing_trading_enabled,
                "test_mode": config.test_mode,
                "coins": coins_policies,
                "budget": {
                    "total": config.total_budget_krw,
                    "per_position": config.budget_per_position_krw,
                    "max_positions": config.max_concurrent_positions
                },
                "risk": {
                    "take_profit_min": float(config.take_profit_min),
                    "take_profit_max": float(config.take_profit_max),
                    "stop_loss_min": float(config.stop_loss_min),
                    "stop_loss_max": float(config.stop_loss_max),
                    "emergency_stop_loss": float(config.emergency_stop_loss)
                }
            }

            return jsonify(policies)

        elif request.method == 'POST':
            # Update user's config from policies format
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "error": "No data provided"}), 400

            # Get or create user config
            config = session.query(UserConfig).filter_by(user_id=user_id).first()
            if not config:
                config = UserConfig(user_id=user_id)
                session.add(config)

            # Update config from policies
            config.auto_trading_enabled = data.get('auto_trading_enabled', False)
            config.swing_trading_enabled = data.get('swing_trading_enabled', False)
            config.test_mode = data.get('test_mode', True)

            # Update budget settings
            if 'budget' in data:
                budget = data['budget']
                config.total_budget_krw = budget.get('total', config.total_budget_krw)
                config.budget_per_position_krw = budget.get('per_position', config.budget_per_position_krw)
                config.max_concurrent_positions = budget.get('max_positions', config.max_concurrent_positions)

            # Update risk settings
            if 'risk' in data:
                risk = data['risk']
                config.take_profit_min = risk.get('take_profit_min', config.take_profit_min)
                config.take_profit_max = risk.get('take_profit_max', config.take_profit_max)
                config.stop_loss_min = risk.get('stop_loss_min', config.stop_loss_min)
                config.stop_loss_max = risk.get('stop_loss_max', config.stop_loss_max)
                config.emergency_stop_loss = risk.get('emergency_stop_loss', config.emergency_stop_loss)

            # Update monitored coins
            if 'coins' in data:
                monitored_coins = [coin for coin, settings in data['coins'].items() if settings.get('enabled')]
                config.monitored_coins = monitored_coins

            session.commit()

            return jsonify({
                "success": True,
                "message": "Policies saved successfully"
            })

    except Exception as e:
        session.rollback()
        logger.error(f"[TradingPolicies] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        session.close()


@app.route('/api/user/plan', methods=['GET'])
def get_user_plan():
    """
    Get current user's plan and feature limits

    Returns:
        JSON with plan info and features
    """
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({
            'success': False,
            'message': 'Authorization required',
            'plan': 'free',
            'features': {
                'manual_trading': False,
                'max_auto_trading_alerts': 0
            }
        }), 401

    try:
        # Extract token (format: "Bearer <token>")
        token = auth_header.split(' ')[1]

        # Verify token
        from backend.utils.auth_utils import decode_token
        payload = decode_token(token)
        user_id = payload.get('user_id')

        if not user_id:
            raise Exception('Invalid token payload')

        # Get user's subscription
        from backend.models.subscription_models import Subscription, SubscriptionStatus
        from backend.models.plan_features import PLAN_FEATURES

        session = get_db_session()
        try:
            subscription = session.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL])
            ).first()

            # Default to free plan if no active subscription
            if not subscription:
                plan = 'free'
            else:
                plan = subscription.plan.value

            # Get features for this plan
            features = PLAN_FEATURES.get(plan, PLAN_FEATURES['free'])

            return jsonify({
                'success': True,
                'plan': plan,
                'features': features,
                'subscription': subscription.to_dict() if subscription else None
            })

        finally:
            session.close()

    except Exception as e:
        logger.error(f"[UserPlan] Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'plan': 'free',
            'features': PLAN_FEATURES['free']
        }), 500


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 error: {request.url}")
    return jsonify({
        'success': False,
        'error': 'Resource not found',
        'code': 'NOT_FOUND',
        'path': request.path
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'code': 'SERVER_ERROR'
    }), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {error}", exc_info=True)

    # Don't expose internal errors in production
    if CONFIG['server']['debug']:
        error_message = str(error)
    else:
        error_message = 'An unexpected error occurred'

    return jsonify({
        'success': False,
        'error': error_message,
        'code': 'UNEXPECTED_ERROR'
    }), 500


# ============================================================================
# Background Services Initialization
# ============================================================================

def init_background_services():
    """Initialize background services (order sync, WebSocket, etc.)"""

    # Initialize WebSocket service (Phase 3)
    try:
        ws_service = init_websocket_service(socketio)
        setup_socketio_handlers(socketio)

        # Store reference for later use
        app.ws_service = ws_service

        logger.info("WebSocket service started - Real-time updates enabled")
    except Exception as e:
        logger.error(f"Failed to start WebSocket service: {e}")

    # Background order sync is DISABLED for multi-user architecture
    # NOTE: Orders now use database-first strategy with per-user API keys.
    # Each user's orders are synced on-demand when they access /api/orders.
    # To re-enable, BackgroundSyncScheduler needs refactoring to loop through all users.
    logger.info("Background order sync: DISABLED (multi-user mode, database-first strategy)")

    # Initialize subscription renewal scheduler (Phase 8)
    try:
        from backend.services.subscription_scheduler import start_scheduler

        subscription_scheduler = start_scheduler()

        # Store reference for later use
        app.subscription_scheduler = subscription_scheduler

        logger.info("Subscription renewal scheduler started (daily check at 00:00 KST)")
    except Exception as e:
        logger.error(f"Failed to start subscription renewal scheduler: {e}")

    # Initialize backup scheduler (Production Stabilization)
    try:
        from backend.services.backup_scheduler import start_backup_scheduler

        backup_scheduler = start_backup_scheduler()

        # Store reference for later use
        app.backup_scheduler = backup_scheduler

        backup_time = os.getenv('BACKUP_TIME', '02:00')
        logger.info(f"Database backup scheduler started (daily backup at {backup_time})")
    except Exception as e:
        logger.error(f"Failed to start backup scheduler: {e}")

    # Initialize Telegram alert bot (Optional - requires TELEGRAM_BOT_TOKEN)
    telegram_bot = None
    try:
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if telegram_token:
            from backend.services.telegram_bot import SurgeTelegramBot, TELEGRAM_AVAILABLE
            from backend.services.surge_alert_scheduler import SurgeAlertScheduler

            if TELEGRAM_AVAILABLE:
                # Initialize Telegram bot
                telegram_bot = SurgeTelegramBot(token=telegram_token)

                # Start bot in background
                import asyncio
                import threading

                def run_telegram_bot():
                    """Run Telegram bot in separate thread"""
                    try:
                        asyncio.run(telegram_bot.start())
                    except Exception as e:
                        logger.error(f"Telegram bot error: {e}")

                telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
                telegram_thread.start()

                # Initialize surge alert scheduler (5 minute interval)
                surge_alert_scheduler = SurgeAlertScheduler(
                    telegram_bot=telegram_bot,
                    check_interval=300  # 5 minutes
                )

                # Start scheduler in background
                def run_surge_alerts():
                    """Run surge alert scheduler"""
                    try:
                        asyncio.run(surge_alert_scheduler.start())
                    except Exception as e:
                        logger.error(f"Surge alert scheduler error: {e}")

                alert_thread = threading.Thread(target=run_surge_alerts, daemon=True)
                alert_thread.start()

                # Store references
                app.telegram_bot = telegram_bot
                app.surge_alert_scheduler = surge_alert_scheduler

                logger.info("Telegram bot and surge alert scheduler started (5 minute interval)")
            else:
                logger.warning("python-telegram-bot not installed - Telegram alerts disabled")
        else:
            logger.info("TELEGRAM_BOT_TOKEN not set - Telegram alerts disabled")
    except Exception as e:
        logger.error(f"Failed to start Telegram services: {e}")

    # Initialize signal generation scheduler (Phase 5 - Auto Trading)
    # NOTE: Must be initialized AFTER Telegram bot to enable signal notifications
    try:
        from backend.services.signal_scheduler import SignalScheduler

        # Create scheduler with telegram_bot (if available)
        signal_scheduler = SignalScheduler(telegram_bot=telegram_bot)
        signal_scheduler.start()

        # Store reference for later use
        app.signal_scheduler = signal_scheduler

        if telegram_bot:
            logger.info("Signal generation scheduler started with Telegram notifications (surge analysis every 15 minutes)")
        else:
            logger.info("Signal generation scheduler started without Telegram notifications (surge analysis every 15 minutes)")
    except Exception as e:
        logger.error(f"Failed to start signal scheduler: {e}")


# ============================================================================
# Application Startup
# ============================================================================

def startup():
    """Run startup tasks"""
    logger.info("=" * 80)
    logger.info(f"Starting {CONFIG['server']['name']}")
    logger.info("=" * 80)

    # Log configuration
    logger.info(f"Host: {CONFIG['server']['host']}")
    logger.info(f"Port: {CONFIG['server']['port']}")
    logger.info(f"Debug: {CONFIG['server']['debug']}")
    logger.info(f"Database: {CONFIG['database']['url']}")

    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs(CONFIG['paths']['logs'], exist_ok=True)

    # Initialize background services
    init_background_services()

    logger.info("Startup complete - Server ready!")
    logger.info("=" * 80)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    startup()

    # Get PORT from environment (Railway/Render) or config
    port = int(os.environ.get('PORT', CONFIG['server']['port']))
    
    # Run the Flask app with SocketIO support (Phase 3)
    # Note: Using socketio.run() instead of app.run() for WebSocket support
    socketio.run(
        app,
        host='0.0.0.0',  # Must be 0.0.0.0 for Railway
        port=port,
        debug=False,  # Disable debug in production
        allow_unsafe_werkzeug=True
    )
