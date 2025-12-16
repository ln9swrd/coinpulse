# Clean Upbit API Server - English Only (with Trading Features)
from flask import Flask, jsonify, request, send_from_directory
import requests
import time
import json
import os
from functools import lru_cache

# Import backend common modules
from backend.common import setup_cors, SimpleCache, UpbitAPI, load_api_keys
# Import backend services
from backend.services import ChartService

app = Flask(__name__)

# Load configuration from file
try:
    with open('chart_server_config.json', 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    print("Warning: chart_server_config.json not found, using defaults")
    CONFIG = {
        "server": {"port": 8080, "host": "0.0.0.0", "debug": True},
        "api": {"upbit_base_url": "https://api.upbit.com", "request_timeout": 5, "max_retries": 3},
        "cache": {"default_ttl": 60, "enabled": True}
    }

# CORS setup using backend common module
setup_cors(app, 'chart_server_config.json')

# Cache system - using backend common module with config value
# Note: SimpleCache class removed - now imported from backend.common
cache_ttl = CONFIG.get('cache', {}).get('default_ttl', 60)
cache = SimpleCache(default_ttl=cache_ttl)

# Load environment variables for trading API
from dotenv import load_dotenv
load_dotenv()

# Upbit Trading API settings - using backend common module
UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY = load_api_keys()

# Note: UpbitTradingAPI class removed - now using UpbitAPI from backend.common
# Initialize trading API using backend common UpbitAPI
trading_api = UpbitAPI(UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY) if UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY else None

# Note: CleanUpbitAPI class moved to backend.services.ChartService
# Initialize chart service using backend services ChartService
api = ChartService(CONFIG)

@app.route('/api/upbit/candles/days')
def get_candles_days():
    try:
        print(f"ENDPOINT: Days candle request received")
        print(f"REQUEST ARGS: {dict(request.args)}")

        market = request.args.get('market', 'KRW-BTC')
        count = int(request.args.get('count', 200))
        to = request.args.get('to')

        print(f"PARSED: market={market}, count={count}, to={to}")

        # 캐시 키 생성
        cache_key = f"days_{market}_{count}_{to or 'none'}"
        
        # 캐시에서 데이터 확인
        cached_data = cache.get(cache_key)
        if cached_data:
            print(f"CACHE HIT: {cache_key}")
            return jsonify({
                'success': True,
                'data': cached_data,
                'market': market,
                'count': len(cached_data),
                'cached': True
            })

        data = api.get_candles('days', market, count, to=to)

        if data is not None:
            # 캐시에 저장
            cache.set(cache_key, data)
            print(f"CACHE SET: {cache_key}")
            
            return jsonify({
                'success': True,
                'data': data,
                'market': market,
                'count': len(data),
                'cached': False
            })
        else:
            print(f"ENDPOINT ERROR: Failed to get days data for {market}")
            return jsonify({'success': False, 'error': 'Failed to get days data'}), 500
    except Exception as e:
        print(f"ENDPOINT EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/api/upbit/candles/minutes')
def get_candles_minutes():
    try:
        print(f"ENDPOINT: Minutes candle request received")
        print(f"REQUEST ARGS: {dict(request.args)}")

        market = request.args.get('market', 'KRW-BTC')
        count = int(request.args.get('count', 200))
        unit = int(request.args.get('unit', 1))
        to = request.args.get('to')

        print(f"PARSED: market={market}, count={count}, unit={unit}, to={to}")

        data = api.get_candles('minutes', market, count, unit=unit, to=to)

        if data is not None:
            return jsonify({
                'success': True,
                'data': data,
                'market': market,
                'count': len(data)
            })
        else:
            print(f"ENDPOINT ERROR: Failed to get minutes data for {market}")
            return jsonify({'success': False, 'error': 'Failed to get minutes data'}), 500
    except Exception as e:
        print(f"ENDPOINT EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/api/upbit/candles/weeks')
def get_candles_weeks():
    market = request.args.get('market', 'KRW-BTC')
    count = int(request.args.get('count', 200))
    to = request.args.get('to')

    data = api.get_candles('weeks', market, count, to=to)

    if data is not None:
        return jsonify({
            'success': True,
            'data': data,
            'market': market,
            'count': len(data)
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to get weeks data'}), 500

@app.route('/api/upbit/candles/months')
def get_candles_months():
    market = request.args.get('market', 'KRW-BTC')
    count = int(request.args.get('count', 200))
    to = request.args.get('to')

    data = api.get_candles('months', market, count, to=to)

    if data is not None:
        return jsonify({
            'success': True,
            'data': data,
            'market': market,
            'count': len(data)
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to get months data'}), 500

@app.route('/api/upbit/market/all')
def get_market_all():
    try:
        url = f"{api.base_url}/v1/market/all"
        response = requests.get(url)

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to get market list'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Clean Upbit Chart API Server with Trading Features"
    })

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """캐시 초기화"""
    try:
        cache.clear()
        return jsonify({
            'success': True,
            'message': '캐시가 성공적으로 초기화되었습니다.',
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cache/stats')
def cache_stats():
    """캐시 통계 조회"""
    try:
        with cache.lock:
            cache_size = len(cache.cache)
            current_time = time.time()
            valid_entries = sum(1 for _, (_, timestamp) in cache.cache.items() 
                              if current_time - timestamp < cache.default_ttl)
        
        return jsonify({
            'success': True,
            'stats': {
                'total_entries': cache_size,
                'valid_entries': valid_entries,
                'expired_entries': cache_size - valid_entries,
                'default_ttl': cache.default_ttl,
                'timestamp': current_time
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Trading API Endpoints (Short-term Trading)
@app.route('/api/trading/buy', methods=['POST'])
def quick_buy():
    """Quick buy order for short-term trading"""
    try:
        if not trading_api:
            return jsonify({
                "success": False,
                "error": "Upbit API keys not configured"
            }), 400

        data = request.get_json()
        market = data.get('market')
        order_type = data.get('order_type', 'market')
        amount = data.get('amount')
        price = data.get('price')

        if not market or not amount:
            return jsonify({
                "success": False,
                "error": "market and amount are required"
            }), 400

        print(f"Quick buy order: {market}, type: {order_type}, amount/quantity: {amount}")

        if order_type == 'market':
            result = trading_api.place_order(
                market=market,
                side='bid',
                price=amount,
                ord_type='market'
            )
        else:
            if not price:
                return jsonify({
                    "success": False,
                    "error": "price required for limit order"
                }), 400
            
            result = trading_api.place_order(
                market=market,
                side='bid',
                volume=amount,
                price=price,
                ord_type='limit'
            )

        return jsonify(result)

    except Exception as e:
        print(f"Quick buy error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/trading/sell', methods=['POST'])
def quick_sell():
    """Quick sell order for short-term trading"""
    try:
        if not trading_api:
            return jsonify({
                "success": False,
                "error": "Upbit API keys not configured"
            }), 400

        data = request.get_json()
        market = data.get('market')
        order_type = data.get('order_type', 'market')
        volume = data.get('volume')
        price = data.get('price')

        if not market or not volume:
            return jsonify({
                "success": False,
                "error": "market and volume are required"
            }), 400

        print(f"Quick sell order: {market}, type: {order_type}, volume: {volume}")

        if order_type == 'market':
            result = trading_api.place_order(
                market=market,
                side='ask',
                volume=volume,
                ord_type='market'
            )
        else:
            if not price:
                return jsonify({
                    "success": False,
                    "error": "price required for limit order"
                }), 400
            
            result = trading_api.place_order(
                market=market,
                side='ask',
                volume=volume,
                price=price,
                ord_type='limit'
            )

        return jsonify(result)

    except Exception as e:
        print(f"Quick sell error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/trading/cancel/<order_uuid>', methods=['DELETE'])
def cancel_order(order_uuid):
    """Cancel order"""
    try:
        if not trading_api:
            return jsonify({
                "success": False,
                "error": "Upbit API keys not configured"
            }), 400

        print(f"Order cancel request: {order_uuid}")
        result = trading_api.cancel_order(order_uuid)
        return jsonify(result)

    except Exception as e:
        print(f"Order cancel error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/trading/current-price/<market>')
def get_current_price(market):
    """Real-time current price query for short-term trading"""
    try:
        current_prices = trading_api.get_current_prices([market]) if trading_api else {}
        price_info = current_prices.get(market, {})
        
        if price_info:
            return jsonify({
                "success": True,
                "market": market,
                "price": float(price_info.get('trade_price', 0)),
                "change_rate": float(price_info.get('change_rate', 0)) * 100,
                "change_price": float(price_info.get('change_price', 0)),
                "volume": float(price_info.get('acc_trade_volume_24h', 0)),
                "timestamp": price_info.get('timestamp')
            })
        else:
            return jsonify({
                "success": False,
                "error": "Unable to get price information"
            }), 404

    except Exception as e:
        print(f"Current price query error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/orders')
def get_orders():
    """Trading history query"""
    try:
        if not trading_api:
            return jsonify({
                "success": False,
                "error": "Upbit API keys not configured",
                "orders": []
            })

        market = request.args.get('market', None)
        state = request.args.get('state', 'done')
        limit = int(request.args.get('limit', 100))

        orders = trading_api.get_orders_history(market=market, state=state, limit=limit)

        if orders:
            import datetime
            processed_orders = []
            for order in orders:
                created_at = datetime.datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))

                processed_order = {
                    "uuid": order.get('uuid', ''),
                    "market": order.get('market', ''),
                    "coin": order.get('market', '').split('-')[-1] if order.get('market') else '',
                    "side": order.get('side', ''),
                    "ord_type": order.get('ord_type', ''),
                    "price": float(order.get('price', 0)),
                    "avg_price": float(order.get('avg_price', 0)) if order.get('avg_price') else float(order.get('price', 0)),
                    "volume": float(order.get('volume', 0)),
                    "executed_volume": float(order.get('executed_volume', 0)),
                    "state": order.get('state', ''),
                    "created_at": order.get('created_at', ''),
                    "created_at_kr": created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                processed_orders.append(processed_order)

            return jsonify({
                "success": True,
                "orders": processed_orders,
                "count": len(processed_orders)
            })
        else:
            return jsonify({
                "success": True,
                "orders": [],
                "count": 0,
                "message": "No trading history found"
            })

    except Exception as e:
        print(f"Trading history error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Static file serving for frontend
@app.route('/frontend/<path:filename>')
def serve_frontend(filename):
    return send_from_directory('frontend', filename)

# CSS 파일 서빙
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('frontend/css', filename)

# JavaScript 파일 서빙
@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('frontend/js', filename)

@app.route('/favicon.ico')
def favicon():
    """Favicon serving"""
    try:
        return send_from_directory('frontend', 'favicon.ico')
    except Exception:
        return '', 200, {'Content-Type': 'image/x-icon'}

# Root redirect to main app (with trading features)
@app.route('/')
def index():
    return send_from_directory('frontend', 'trading_chart.html')

@app.route('/policy_manager.html')
def policy_manager():
    """정책 관리자 페이지"""
    return send_from_directory('.', 'policy_manager.html')

@app.route('/config.json')
def serve_config():
    """Config file serving"""
    return send_from_directory('.', 'config.json')

if __name__ == '__main__':
    # Load configuration from JSON file
    import os
    import json
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Load configuration from JSON file
    try:
        with open('chart_server_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        server_config = config.get('server', {})
        host = server_config.get('host', '0.0.0.0')
        port = server_config.get('port', 8080)
        debug = server_config.get('debug', True)
        print("Configuration loaded from chart_server_config.json")
    except FileNotFoundError:
        # Fallback to environment variables if config file not found
        host = os.getenv('SERVER_HOST', '0.0.0.0')
        port = int(os.getenv('CHART_SERVER_PORT', 8080))
        debug = os.getenv('DEBUG_MODE', 'true').lower() == 'true'
        print("Configuration loaded from environment variables (fallback)")

    print("Clean Upbit Chart API Server Starting...")
    print(f"URL: http://localhost:{port}")
    
    # ⚠️ 최종 수정: 프로세스 문제를 해결하기 위해 debug와 use_reloader를 False로 강제 설정합니다.
    print(f"Host: {host}, Debug: {debug} -> FORCED TO FALSE")
    # Enable threading for concurrent user support (100+ users)
    app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)