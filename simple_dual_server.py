# Simple Dual Server - Holdings & Uptrend Data Server (with Real Upbit API)
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import random
import time
import os
import sys
import signal
import requests
from urllib.parse import urlencode, unquote

# Import backend common modules
from backend.common import UpbitAPI, load_api_keys
# Import backend services
from backend.services import AutoTradingEngine, HoldingsService
from backend.services.swing_trading_engine import SwingTradingEngine
# Import backend utilities
from backend.utils import is_port_available, find_available_port
# Import backend routes
from backend.routes import init_holdings_routes
from backend.routes.surge_routes import surge_bp

# TradingPolicyEngine removed - using SimplePolicy instead

# Config loading function
def load_env_config():
    """Load configuration from JSON file and environment variables."""
    from dotenv import load_dotenv
    load_dotenv()

    # Try to load from JSON config file first
    try:
        with open('trading_server_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("[Config] Loaded from trading_server_config.json")
        return config
    except FileNotFoundError:
        print("[Config] trading_server_config.json not found, using environment variables")

    # Fallback to environment variables
    return {
        "server": {
            "host": os.getenv('SERVER_HOST', '0.0.0.0'),
            "port": int(os.getenv('TRADING_SERVER_PORT', 8081)),
            "debug": os.getenv('DEBUG_MODE', 'true').lower() == 'true',
            "cors_origins": "*"
        },
        "api": {
            "upbit_base_url": "https://api.upbit.com",
            "default_count": int(os.getenv('MAX_DATA_COUNT', 200)),
            "max_count": int(os.getenv('MAX_DATA_COUNT', 200)),
            "request_timeout": 5,
            "max_retries": 3
        },
        "cors": {
            "origins": [
                "http://localhost:8080",
                "http://127.0.0.1:8080",
                "http://localhost:8081",
                "http://127.0.0.1:8081",
                "http://localhost:8082",
                "http://127.0.0.1:8082",
                "*"
            ]
        },
        "paths": {"frontend": "frontend", "policies": "policies"}
    }

# Load configuration
CONFIG = load_env_config()

app = Flask(__name__)

# CORS setup using config values
cors_origins = CONFIG.get('cors', {}).get('origins', ['*'])
CORS(app, origins=cors_origins, supports_credentials=True)

# Upbit API setup - using backend common module
UPBIT_BASE_URL = CONFIG.get('api', {}).get('upbit_base_url', 'https://api.upbit.com')

# Load API keys using backend common function
UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY = load_api_keys()

# Note: UpbitAPI class removed - now imported from backend.common
# API 인스턴스 생성
upbit_api = UpbitAPI(UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY) if UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY else None

# 정책 엔진 초기화
# policy_engine = TradingPolicyEngine()  # Disabled - dependency removed during cleanup

# Note: AutoTradingEngine class moved to backend.services.auto_trading_engine
# 전역 자동매매 엔진 인스턴스
auto_trading_engine = AutoTradingEngine()
auto_trading_engine.load_policies()

# Note: HoldingsService class moved to backend.services.holdings_service
# 전역 보유 코인 서비스 인스턴스
holdings_service = HoldingsService(upbit_api)

# Background order sync scheduler (runs incremental sync every 5 minutes)
from backend.services.background_sync import BackgroundSyncScheduler
background_sync_scheduler = None
if upbit_api:
    background_sync_scheduler = BackgroundSyncScheduler(upbit_api, sync_interval_seconds=300)
    print("[Init] Background sync scheduler initialized (5 minute interval)")

# Swing Trading Engine 초기화
swing_trading_engine = SwingTradingEngine(upbit_api) if upbit_api else None
if swing_trading_engine:
    print("[SwingEngine] Initialized successfully")

# Register route blueprints
holdings_routes = init_holdings_routes(CONFIG, upbit_api, holdings_service)
app.register_blueprint(holdings_routes)

# Register surge prediction routes
app.register_blueprint(surge_bp)
print("[Routes] Surge prediction routes registered")

# 자동매매 스케줄러
import threading
import time
from datetime import datetime

def auto_trading_scheduler():
    """자동매매 스케줄러 (백그라운드 실행)"""
    while True:
        try:
            if auto_trading_engine.policies['auto_trading_enabled']:
                # Pass upbit_api and holdings_getter to run_auto_trading_cycle
                auto_trading_engine.run_auto_trading_cycle(upbit_api, holdings_service.get_real_holdings_data)

            # 체크 간격만큼 대기
            check_interval = auto_trading_engine.policies['global_settings'].get('check_interval', 60)
            time.sleep(check_interval)

        except Exception as e:
            print(f"[ERROR] 자동매매 스케줄러 오류: {e}")
            time.sleep(60)  # 오류 시 1분 대기

# 백그라운드 스레드 시작
trading_thread = threading.Thread(target=auto_trading_scheduler, daemon=True)
trading_thread.start()

# 스윙 트레이딩 스케줄러
def swing_trading_scheduler():
    """스윙 트레이딩 스케줄러 (백그라운드 실행)"""
    while True:
        try:
            if swing_trading_engine and swing_trading_engine.enabled:
                swing_trading_engine.run_cycle()

            # 체크 간격 (5분)
            check_interval = 300  # 5 minutes
            time.sleep(check_interval)

        except Exception as e:
            print(f"[ERROR] 스윙 트레이딩 스케줄러 오류: {e}")
            time.sleep(60)  # 오류 시 1분 대기

# 스윙 트레이딩 백그라운드 스레드 시작
if swing_trading_engine:
    swing_thread = threading.Thread(target=swing_trading_scheduler, daemon=True)
    swing_thread.start()
    print("[SwingEngine] Background scheduler started")

# Note: Holdings functions (get_real_holdings_data, get_fallback_holdings_data, get_coin_korean_name)
# moved to backend.services.holdings_service

# ==============================================================================
# Flask API Endpoints
# ==============================================================================

# 정적 파일 서빙 (프론트엔드)
@app.route('/<path:filename>')
def serve_frontend_files(filename):
    """프론트엔드 정적 파일 서빙"""
    try:
        if filename == 'favicon.ico':
            # 파비콘 요청 무시
            return '', 200, {'Content-Type': 'image/x-icon'}
        
        # frontend 디렉토리에서 파일 서빙
        return send_from_directory(CONFIG['paths']['frontend'], filename)
    except Exception as e:
        print(f"파일 서빙 에러: {e}")
        return jsonify({"error": "File not found"}), 404

@app.route('/frontend/<path:filename>')
def serve_frontend_root(filename):
    """프론트엔드 루트 디렉토리 서빙"""
    try:
        return send_from_directory(CONFIG['paths']['frontend'], filename)
    except Exception as e:
        print(f"파일 서빙 에러: {e}")
        return jsonify({"error": "File not found"}), 404

# 루트 경로: index.html (기본 페이지)
@app.route('/')
def index():
    return send_from_directory(CONFIG['paths']['frontend'], 'trading_chart.html')

# Holdings API (잔고 및 수익률)
# Note: Holdings routes moved to backend/routes/holdings_routes.py
# - /api/holdings
# - /api/trading/current-price/<market>
# - /api/orders
# - /api/order/<uuid>

@app.route('/api/health')
def health_check():
    """서버 상태 확인"""
    return jsonify({
        "status": "healthy",
        "service": "Simple Dual Coin API Server",
        "port": CONFIG.get('server', {}).get('port', 8080),
        "endpoints": ["/api/holdings", "/api/orders", "/api/order/<uuid>", "/api/health", "/api/policies", "/api/global-settings", "/api/backtest", "/api/upbit/candles/minutes", "/api/upbit/candles/days", "/api/upbit/candles/weeks", "/api/upbit/candles/months"]
    })

# 정책 관리 API 엔드포인트

@app.route('/api/policies', methods=['GET'])
def get_policies():
    """모든 정책 조회"""
    try:
        return jsonify({
            "success": True,
            "auto_trading_enabled": auto_trading_engine.policies.get('auto_trading_enabled', False),
            "default_policy": auto_trading_engine.policies.get('default_policy', {}),
            "coin_policies": auto_trading_engine.policies.get('coin_policies', {}),
            "global_settings": auto_trading_engine.policies.get('global_settings', {})
        })
    except Exception as e:
        print(f"정책 조회 오류: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/policies', methods=['POST'])
def save_policy():
    """코인별 정책 저장"""
    try:
        data = request.get_json()
        coin_symbol = data.get('coin_symbol')
        policy_data = data.get('policy_data')
        
        if not coin_symbol or not policy_data:
            return jsonify({"success": False, "error": "coin_symbol과 policy_data가 필요합니다."}), 400

        auto_trading_engine.update_coin_policy(coin_symbol, policy_data)
        print(f"{coin_symbol} 정책 저장 완료")

        return jsonify({
            "success": True,
            "message": f"{coin_symbol} 정책이 저장되었습니다.",
            "policy": auto_trading_engine.policies['coin_policies'].get(coin_symbol)
        })
    except Exception as e:
        print(f"정책 저장 오류: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/global-settings', methods=['GET', 'POST'])
def manage_global_settings():
    """글로벌 설정 조회 및 저장"""
    try:
        if request.method == 'GET':
            return jsonify({
                "success": True,
                "global_settings": auto_trading_engine.policies.get('global_settings', {})
            })
        elif request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "error": "No data provided"}), 400

            # 설정 업데이트
            current_settings = auto_trading_engine.policies.get('global_settings', {})
            auto_trading_engine.policies['global_settings'] = {**current_settings, **data}
            
            # 자동매매 활성화/비활성화 상태도 확인
            enabled = data.get('auto_trading_enabled', auto_trading_engine.policies.get('auto_trading_enabled', False))
            auto_trading_engine.enable_auto_trading(enabled)

            # 파일에 저장
            auto_trading_engine.save_policies()

            return jsonify({
                "success": True,
                "message": "Global settings saved successfully",
                "global_settings": auto_trading_engine.policies['global_settings'],
                "auto_trading_enabled": auto_trading_engine.policies['auto_trading_enabled']
            })
    except Exception as e:
        print(f"글로벌 설정 오류: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/trading/enable', methods=['POST'])
def enable_auto_trading():
    """자동매매 활성화/비활성화"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)

        auto_trading_engine.enable_auto_trading(enabled)

        return jsonify({
            "success": True,
            "message": f"자동매매가 {'활성화' if enabled else '비활성화'}되었습니다.",
            "auto_trading_enabled": enabled
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/trading/policies', methods=['GET', 'POST'])
def manage_trading_policies():
    """자동매매 정책 조회 및 저장 (전체)"""
    try:
        if request.method == 'GET':
            # 정책 조회
            return jsonify(auto_trading_engine.policies)
        elif request.method == 'POST':
            # 정책 전체 저장
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "error": "No data provided"}), 400

            # 정책 업데이트
            auto_trading_engine.policies = data
            
            # 자동매매 상태도 업데이트
            enabled = data.get('auto_trading_enabled', False)
            auto_trading_engine.trading_active = enabled

            # 파일에 저장
            auto_trading_engine.save_policies()

            return jsonify({
                "success": True,
                "message": "Policies saved successfully",
                "policies": auto_trading_engine.policies
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/trading/status')
def get_trading_status():
    """자동매매 상태 조회"""
    try:
        summary = auto_trading_engine.get_policy_summary()
        return jsonify({
            "success": True,
            "status": "enabled" if summary['auto_trading_enabled'] else "disabled",
            "auto_trading_enabled": summary['auto_trading_enabled'],
            "active_policies": summary['active_policies'],
            "total_policies": summary['total_policies'],
            "last_check": summary['last_check'],
            "trading_active": summary['trading_active'],
            "message": f"자동매매 {'활성화' if summary['auto_trading_enabled'] else '비활성화'}됨"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/trading/analyze/<coin_symbol>')
def analyze_coin_market(coin_symbol):
    """특정 코인 시장 상황 분석 (시그널 확인)"""
    try:
        if not upbit_api:
            return jsonify({ "success": False, "error": "Upbit API 키가 설정되지 않았습니다." }), 400

        # 현재가 조회
        current_price = upbit_api.get_current_price(coin_symbol)
        if not current_price:
            return jsonify({ "success": False, "error": f"{coin_symbol} 현재가를 조회할 수 없습니다." }), 400

        # 차트 데이터 조회 (최근 20일)
        chart_data = upbit_api.get_candles_days(coin_symbol, count=20)
        if not chart_data:
            return jsonify({ "success": False, "error": f"{coin_symbol} 차트 데이터를 조회할 수 없습니다." }), 400

        # 시장 분석
        analysis = auto_trading_engine.analyze_market_condition(coin_symbol, current_price, chart_data)

        return jsonify({
            "success": True,
            "coin_symbol": coin_symbol,
            "current_price": current_price,
            "analysis": analysis
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/trading/backtest/<coin_symbol>', methods=['POST'])
def backtest_coin_policy(coin_symbol):
    """코인 정책 백테스트"""
    try:
        if not upbit_api:
            return jsonify({ "success": False, "error": "Upbit API 키가 설정되지 않았습니다." }), 400
            
        data = request.get_json() or {}
        days = data.get('days', 100)

        # 차트 데이터 조회
        chart_data = upbit_api.get_candles_days(coin_symbol, count=days)
        if not chart_data:
            return jsonify({ "success": False, "error": f"{coin_symbol} 차트 데이터를 조회할 수 없습니다." }), 400

        # 백테스트 실행
        result = auto_trading_engine.backtest_policy(coin_symbol, chart_data)

        return jsonify({
            "success": True,
            "coin_symbol": coin_symbol,
            "backtest": result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/trading/logs', methods=['GET'])
def get_trading_logs():
    """자동매매 로그 조회"""
    try:
        limit = request.args.get('limit', 100, type=int)
        logs = auto_trading_engine.trading_log[-limit:] if auto_trading_engine.trading_log else []
        return jsonify(logs)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/trading/cycle', methods=['POST'])
def run_trading_cycle():
    """수동으로 자동매매 사이클 실행"""
    try:
        # 백그라운드 스레드로 실행되므로, 이 엔드포인트는 즉시 응답하고 스케줄러를 트리거함
        # run_auto_trading_cycle은 스레드 안전하지 않으므로, 이 부분을 개선해야 하나,
        # 현재는 디버깅/테스트용으로 스케줄러에만 의존하는 방식 유지

        # 스케줄러가 짧은 주기로 실행되므로, 수동 실행 요청은 무시하거나 메시지만 반환
        if auto_trading_engine.policies['auto_trading_enabled']:
            # 스케줄러가 이미 실행 중인 경우
            message = "자동매매 스케줄러가 활성화되어 있습니다. 다음 주기까지 기다리거나 비활성화 후 수동 실행하세요."
        else:
            # 수동으로 한번 실행 (동기 방식)
            auto_trading_engine.run_auto_trading_cycle()
            message = "자동매매 사이클을 수동으로 실행했습니다. 로그를 확인하세요."
        
        return jsonify({ 
            "success": True, 
            "message": message,
            "auto_trading_enabled": auto_trading_engine.policies['auto_trading_enabled']
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==============================================================================
# Swing Trading API Endpoints
# ==============================================================================

@app.route('/api/swing/status', methods=['GET'])
def get_swing_status():
    """스윙 트레이딩 상태 조회"""
    try:
        if not swing_trading_engine:
            return jsonify({
                "success": False,
                "error": "Swing trading engine not initialized"
            }), 500

        status = swing_trading_engine.get_status()
        return jsonify({
            "success": True,
            "status": status
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/swing/enable', methods=['POST'])
def enable_swing_trading():
    """스윙 트레이딩 활성화/비활성화"""
    try:
        if not swing_trading_engine:
            return jsonify({
                "success": False,
                "error": "Swing trading engine not initialized"
            }), 500

        data = request.get_json()
        enabled = data.get('enabled', False)

        swing_trading_engine.enable(enabled)

        return jsonify({
            "success": True,
            "message": f"Swing trading {'enabled' if enabled else 'disabled'}",
            "enabled": enabled
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/swing/positions', methods=['GET'])
def get_swing_positions():
    """현재 스윙 트레이딩 포지션 조회"""
    try:
        if not swing_trading_engine:
            return jsonify({
                "success": False,
                "error": "Swing trading engine not initialized"
            }), 500

        summary = swing_trading_engine.position_tracker.get_position_summary()

        return jsonify({
            "success": True,
            "positions": summary
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/swing/statistics', methods=['GET'])
def get_swing_statistics():
    """스윙 트레이딩 통계 조회"""
    try:
        if not swing_trading_engine:
            return jsonify({
                "success": False,
                "error": "Swing trading engine not initialized"
            }), 500

        stats = swing_trading_engine.position_tracker.get_statistics()

        return jsonify({
            "success": True,
            "statistics": stats
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/swing/run', methods=['POST'])
def run_swing_cycle():
    """수동으로 스윙 트레이딩 사이클 실행"""
    try:
        if not swing_trading_engine:
            return jsonify({
                "success": False,
                "error": "Swing trading engine not initialized"
            }), 500

        if not swing_trading_engine.enabled:
            return jsonify({
                "success": False,
                "error": "Swing trading is not enabled"
            }), 400

        # Run cycle manually
        swing_trading_engine.run_cycle()

        return jsonify({
            "success": True,
            "message": "Swing trading cycle executed successfully"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==============================================================================
# Multi-User Swing Trading API Endpoints
# ==============================================================================

from backend.database import get_db_session, User, UserConfig

@app.route('/api/swing/user/verify', methods=['POST'])
def verify_user_api_key():
    """Verify user API key and return user info"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '')

        if not api_key:
            return jsonify({"success": False, "error": "API key required"}), 400

        session = get_db_session()
        try:
            user = session.query(User).filter_by(api_key=api_key, is_active=True).first()

            if user:
                return jsonify({
                    "success": True,
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email
                })
            else:
                return jsonify({"success": False, "error": "Invalid API key"}), 401

        finally:
            session.close()

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/swing/user/<int:user_id>/config', methods=['GET'])
def get_user_config(user_id):
    """Get user swing trading configuration"""
    try:
        session = get_db_session()
        try:
            config = session.query(UserConfig).filter_by(user_id=user_id).first()

            if config:
                return jsonify(config.to_dict())
            else:
                return jsonify({"error": "User config not found"}), 404

        finally:
            session.close()

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/swing/user/<int:user_id>/config', methods=['PUT'])
def update_user_config(user_id):
    """Update user swing trading configuration"""
    try:
        data = request.get_json()

        session = get_db_session()
        try:
            config = session.query(UserConfig).filter_by(user_id=user_id).first()

            if not config:
                return jsonify({"error": "User config not found"}), 404

            # Update configuration
            if 'total_budget_krw' in data:
                config.total_budget_krw = data['total_budget_krw']
            if 'min_order_amount' in data:
                config.min_order_amount = data['min_order_amount']
            if 'max_order_amount' in data:
                config.max_order_amount = data['max_order_amount']
            if 'max_concurrent_positions' in data:
                config.max_concurrent_positions = data['max_concurrent_positions']
            if 'holding_period_days' in data:
                config.holding_period_days = data['holding_period_days']
            if 'force_sell_after_period' in data:
                config.force_sell_after_period = data['force_sell_after_period']
            if 'take_profit_min' in data:
                config.take_profit_min = data['take_profit_min']
            if 'take_profit_max' in data:
                config.take_profit_max = data['take_profit_max']
            if 'stop_loss_min' in data:
                config.stop_loss_min = data['stop_loss_min']
            if 'stop_loss_max' in data:
                config.stop_loss_max = data['stop_loss_max']
            if 'emergency_stop_loss' in data:
                config.emergency_stop_loss = data['emergency_stop_loss']
            if 'auto_stop_on_loss' in data:
                config.auto_stop_on_loss = data['auto_stop_on_loss']
            if 'swing_trading_enabled' in data:
                config.swing_trading_enabled = data['swing_trading_enabled']
            if 'test_mode' in data:
                config.test_mode = data['test_mode']

            session.commit()

            return jsonify({
                "success": True,
                "message": "Configuration updated successfully",
                "config": config.to_dict()
            })

        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/swing/user/<int:user_id>/status', methods=['GET'])
def get_user_status(user_id):
    """Get user swing trading status"""
    try:
        # Import DB swing engine
        from backend.services.db_swing_trading_engine import DBSwingTradingEngine

        # Create engine instance (temporary for status check)
        engine = DBSwingTradingEngine(upbit_api)
        status = engine.get_user_status(user_id)

        if 'error' in status:
            return jsonify({"error": status['error']}), 500

        return jsonify(status)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==============================================================================
# Upbit Chart Data Proxy Endpoints
# ==============================================================================

@app.route('/api/upbit/candles/minutes')
def get_candles_minutes_query():
    """분봉 데이터 프록시 (query parameter 방식)"""
    try:
        market = request.args.get('market', 'KRW-BTC')
        count = request.args.get('count', '200')
        unit = request.args.get('unit', '1')
        to = request.args.get('to', '')

        params = {'market': market, 'count': count}
        if to:
            params['to'] = to

        response = requests.get(f'{UPBIT_BASE_URL}/v1/candles/minutes/{unit}', params=params)

        if response.status_code == 200:
            candle_data = response.json()
            return jsonify({
                "success": True,
                "data": candle_data
            })
        else:
            return jsonify({"success": False, "error": f"Upbit API Error: {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/upbit/candles/days')
def get_candles_days_query():
    """일봉 데이터 프록시"""
    try:
        market = request.args.get('market', 'KRW-BTC')
        count = request.args.get('count', '200')
        to = request.args.get('to', '')
        
        print(f"[API] 일봉 요청 - market: {market}, count: {count}, to: {to}")

        params = {'market': market, 'count': count}
        if to:
            params['to'] = to

        # URL 인코딩 처리
        from urllib.parse import urlencode
        query_string = urlencode(params)
        full_url = f'{UPBIT_BASE_URL}/v1/candles/days?{query_string}'

        print(f"[API] 최종 요청 URL: {full_url}")
        response = requests.get(full_url)

        if response.status_code == 200:
            candle_data = response.json()
            return jsonify({
                "success": True,
                "data": candle_data
            })
        else:
            return jsonify({"success": False, "error": f"Upbit API Error: {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/upbit/candles/weeks')
def get_candles_weeks_query():
    """주봉 데이터 프록시"""
    try:
        market = request.args.get('market', 'KRW-BTC')
        count = request.args.get('count', '200')
        to = request.args.get('to', '')

        params = {'market': market, 'count': count}
        if to:
            params['to'] = to

        response = requests.get(f'{UPBIT_BASE_URL}/v1/candles/weeks', params=params)

        if response.status_code == 200:
            candle_data = response.json()
            return jsonify({
                "success": True,
                "data": candle_data
            })
        else:
            return jsonify({"success": False, "error": f"Upbit API Error: {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/upbit/candles/months')
def get_candles_months_query():
    """월봉 데이터 프록시"""
    try:
        market = request.args.get('market', 'KRW-BTC')
        count = request.args.get('count', '200')
        to = request.args.get('to', '')

        params = {'market': market, 'count': count}
        if to:
            params['to'] = to

        response = requests.get(f'{UPBIT_BASE_URL}/v1/candles/months', params=params)

        if response.status_code == 200:
            candle_data = response.json()
            return jsonify({
                "success": True,
                "data": candle_data
            })
        else:
            return jsonify({"success": False, "error": f"Upbit API Error: {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/upbit/market-all')
def get_market_all():
    """전체 마켓 코드 조회"""
    try:
        response = requests.get(f'{UPBIT_BASE_URL}/v1/market/all')
        
        if response.status_code == 200:
            markets = response.json()
            # KRW 마켓만 필터링
            krw_markets = [market for market in markets if market['market'].startswith('KRW-')]
            
            return jsonify({
                "success": True,
                "markets": krw_markets,
                "count": len(krw_markets)
            })
        else:
            return jsonify({"success": False, "error": "Failed to get market list"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/security/keys')
def get_api_keys():
    """API 키 상태 조회 (보안을 위해 일부만 노출)"""
    try:
        # 실제 API 호출을 통해 키 유효성 확인 (get_accounts가 성공하면 유효한 것으로 간주)
        upbit_valid = False
        if upbit_api:
            accounts = upbit_api.get_accounts()
            if accounts is not None:
                upbit_valid = True
        
        return jsonify({
            "success": True,
            "api_keys": {
                "upbit_access_key": "***" + (UPBIT_ACCESS_KEY[-4:] if UPBIT_ACCESS_KEY else "None"),
                "upbit_secret_key": "***" + (UPBIT_SECRET_KEY[-4:] if UPBIT_SECRET_KEY else "None"),
                "upbit_valid": upbit_valid,
                "validation_timestamp": time.time()
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/security/rotate-keys', methods=['POST'])
def rotate_api_keys():
    """API 키 로테이션 (개발용)"""
    try:
        data = request.get_json()
        new_access_key = data.get('access_key')
        new_secret_key = data.get('secret_key')

        if not new_access_key or not new_secret_key:
            return jsonify({
                "success": False,
                "error": "새로운 API 키가 필요합니다"
            }), 400

        # 환경변수 업데이트 (메모리상에서만)
        global UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY, upbit_api
        UPBIT_ACCESS_KEY = new_access_key
        UPBIT_SECRET_KEY = new_secret_key

        # API 인스턴스 재생성
        upbit_api = UpbitAPI(UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY)

        # 유효성 재확인
        upbit_valid = False
        accounts = upbit_api.get_accounts()
        if accounts is not None:
            upbit_valid = True

        return jsonify({
            "success": True,
            "message": "API 키가 성공적으로 업데이트되었습니다. (서버 재시작 전까지 유효)",
            "upbit_valid": upbit_valid
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    server_config = CONFIG.get('server', {})
    host = server_config.get('host', '0.0.0.0')
    port = server_config.get('port', 8081)  # 거래 서버는 8081 포트 사용
    debug = server_config.get('debug', True)

    print(f"[INFO] 포트 {port}에서 서버를 시작합니다...")

    print("=" * 50)
    print("Simple Dual Coin API Server Starting...")
    print("=" * 50)
    print(f"URL: http://localhost:{port}")
    print("Endpoints:")
    print("  - Holdings: /api/holdings")
    print("  - Orders: /api/orders (DB-first strategy)")
    print("  - Health: /api/health")
    print("  - Upbit Candles: /api/upbit/candles/minutes")
    print("  - Trading Policies: /api/policies")
    print("=" * 50)

    #  Shutdown handler for clean resource cleanup
    def cleanup_on_shutdown(signum, frame):
        """Cleanup resources on server shutdown (SIGINT/SIGTERM)."""
        print("\n[Shutdown] Cleaning up resources...")

        # Stop background sync
        if background_sync_scheduler:
            print("[Shutdown] Stopping background sync...")
            background_sync_scheduler.stop()

        # Close database connections
        print("[Shutdown] Closing database connections...")
        from backend.database import close_database
        close_database()

        print("[Shutdown] Cleanup complete")
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup_on_shutdown)   # Ctrl+C
    signal.signal(signal.SIGTERM, cleanup_on_shutdown)  # Kill signal
    print("[Server] Signal handlers registered (SIGINT, SIGTERM)")

    # Initialize database (settings loaded from .env)
    print("\n[Database] Initializing database...")
    from backend.database import init_database
    init_database(create_tables=True)
    print("[Database] Database initialized successfully")

    # Start background sync scheduler
    if background_sync_scheduler:
        background_sync_scheduler.start()
        print("\n[BackgroundSync] Started - Incremental sync every 5 minutes")
        print("=" * 50)

    # Enable threading for concurrent user support (100+ users)
    try:
        app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)
    finally:
        cleanup_on_shutdown(None, None)