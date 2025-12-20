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
from backend.common import UpbitAPI, load_api_keys
from backend.services import ChartService, HoldingsService

# Import all route blueprints
from backend.routes.auth_routes import auth_bp
from backend.routes.user_routes import user_bp  # User API routes (plan, profile)
from backend.routes.holdings_routes import holdings_bp, init_holdings_routes
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
from backend.routes.scheduler_admin import scheduler_admin_bp  # Subscription scheduler admin

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
    # Initialize holdings routes with dependencies
    try:
        access_key, secret_key = load_api_keys()
        if access_key and secret_key:
            upbit_api = UpbitAPI(access_key, secret_key)
        else:
            upbit_api = None
            logger.warning("API keys not configured - holdings API will use fallback mode")

        holdings_service = HoldingsService(upbit_api)
        init_holdings_routes(CONFIG, upbit_api, holdings_service)
        logger.info("Holdings routes initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize holdings routes: {e}")

    blueprints = [
        (auth_bp, '/api/auth'),
        (user_bp, None),  # User API routes (already has /api/user prefix)
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
        (scheduler_admin_bp, '/api/admin')  # Subscription renewal scheduler admin
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

    # Initialize background order sync
    try:
        from backend.services.background_sync import BackgroundSyncScheduler

        # Load API keys
        access_key, secret_key = load_api_keys()
        if not access_key or not secret_key:
            logger.warning("API keys not configured - background sync disabled")
        else:
            # Create UpbitAPI instance
            upbit_api = UpbitAPI(access_key, secret_key)

            # Create and start background sync scheduler
            sync_scheduler = BackgroundSyncScheduler(upbit_api, sync_interval_seconds=300)
            sync_scheduler.start()

            # Store reference for later use (e.g., manual sync endpoint)
            app.sync_scheduler = sync_scheduler

            logger.info("Background order sync started (5 minute interval)")
    except Exception as e:
        logger.error(f"Failed to start background order sync: {e}")

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
