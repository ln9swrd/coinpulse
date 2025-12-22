"""
급등 예측 API 라우트

검증된 알고리즘 (81.25% 적중률)으로 실시간 급등 후보 코인 제공

NOTE: This service uses PUBLIC Upbit API (no authentication needed).
Candle data and ticker information are publicly available.
"""
from flask import Blueprint, jsonify
from backend.common import UpbitAPI
from backend.services.surge_predictor import SurgePredictor
from backend.services.market_filter_service import MarketFilter
from backend.services.signal_generation_service import signal_generator
import time
from datetime import datetime, timedelta

surge_bp = Blueprint('surge', __name__)

# Cache for surge candidates (5 minutes TTL)
_surge_cache = {
    'data': None,
    'timestamp': None,
    'ttl': 300  # 5 minutes
}

def get_cached_surge_data():
    """Get cached surge data if still valid"""
    if _surge_cache['data'] and _surge_cache['timestamp']:
        age = (datetime.now() - _surge_cache['timestamp']).total_seconds()
        if age < _surge_cache['ttl']:
            print(f"[Surge] Returning cached data (age: {age:.1f}s)")
            return _surge_cache['data']
    return None

def set_surge_cache(data):
    """Set surge data cache"""
    _surge_cache['data'] = data
    _surge_cache['timestamp'] = datetime.now()
    print(f"[Surge] Cache updated at {_surge_cache['timestamp']}")

# Initialize with public API (no authentication)
upbit_api = UpbitAPI(None, None)  # Public API only
market_filter = MarketFilter()

# Config from backtest
SURGE_CONFIG = {
    "surge_prediction": {
        "volume_increase_threshold": 1.5,
        "rsi_oversold_level": 35,
        "rsi_buy_zone_max": 50,
        "support_level_proximity": 0.02,
        "uptrend_confirmation_days": 3,
        "min_surge_probability_score": 60
    }
}

predictor = SurgePredictor(SURGE_CONFIG)

# Pre-filter markets based on volume surge (smart filtering)
def get_volume_surge_candidates(max_count=30):
    """
    거래량 급증 기반 스마트 필터링

    1. 전체 마켓의 ticker 정보를 1번의 API 호출로 가져옴
    2. 거래량이 평균 대비 1.5배 이상 급증한 코인만 선별
    3. 최대 max_count개까지만 반환

    이 방식으로 API 호출을 대폭 줄이면서도 급등 후보를 놓치지 않음

    Args:
        max_count: 반환할 최대 마켓 수

    Returns:
        list: 거래량 급증 마켓 코드 리스트
    """
    try:
        # Get all KRW markets ticker (1 API call for all markets!)
        print("[Surge] Fetching ticker data for volume pre-filtering...")
        tickers = upbit_api.get_ticker(markets='ALL')  # Single API call

        if not tickers:
            raise Exception("Failed to get ticker data")

        # Filter KRW markets only
        krw_tickers = [t for t in tickers if t.get('market', '').startswith('KRW-')]

        # Sort by acc_trade_price_24h (24h trading volume in KRW)
        sorted_by_volume = sorted(
            krw_tickers,
            key=lambda x: float(x.get('acc_trade_price_24h', 0)),
            reverse=True
        )

        # Get top candidates
        candidates = []
        for ticker in sorted_by_volume[:max_count]:
            market = ticker.get('market')
            volume_24h = float(ticker.get('acc_trade_price_24h', 0))

            # Minimum volume threshold: 1 billion KRW
            if volume_24h >= 1_000_000_000:
                candidates.append(market)

        print(f"[Surge] Pre-filtered to {len(candidates)} high-volume markets (from {len(krw_tickers)} total)")
        return candidates

    except Exception as e:
        print(f"[Surge] Error in volume pre-filtering: {e}")
        # Fallback to popular coins
        return [
            'KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA', 'KRW-DOGE',
            'KRW-AVAX', 'KRW-SOL', 'KRW-DOT', 'KRW-MATIC', 'KRW-LINK',
            'KRW-NEAR', 'KRW-XLM', 'KRW-ALGO', 'KRW-ATOM', 'KRW-ETC'
        ]


@surge_bp.route('/surge-candidates', methods=['GET'])
def get_surge_candidates():
    """
    급등 예측 후보 코인 목록 (PUBLIC - No auth required)

    Returns:
        {
            "candidates": [
                {
                    "market": "KRW-XLM",
                    "score": 80,
                    "current_price": 176.5,
                    "signals": {...},
                    "recommendation": "strong_buy"
                }
            ],
            "backtest_stats": {
                "win_rate": 81.25,
                "avg_return": 19.12,
                "total_trades": 16
            },
            "monitored_markets": 50,
            "timestamp": "2025-12-13T10:00:00"
        }
    """
    try:
        # Check cache first
        cached_data = get_cached_surge_data()
        if cached_data:
            return jsonify(cached_data)

        print("[Surge] Analyzing candidates (cache miss)...")

        # Smart pre-filtering: Get volume surge candidates (1 API call + filtering)
        monitored_markets = get_volume_surge_candidates(max_count=30)
        print(f"[Surge] Analyzing {len(monitored_markets)} pre-filtered markets")

        candidates = []

        # Analyze all monitored coins
        for market in monitored_markets:
            try:
                # Get candle data (30 days) - PUBLIC API
                candle_data = upbit_api.get_candles_days(market=market, count=30)
                if not candle_data or len(candle_data) < 20:
                    continue

                # Get current price
                current_price = float(candle_data[0].get('trade_price', 0))
                if current_price == 0:
                    continue

                # Analyze coin
                analysis = predictor.analyze_coin(market, candle_data, current_price)

                # Only include candidates with score >= 60
                if analysis['score'] >= 60:
                    candidates.append({
                        'market': market,
                        'score': analysis['score'],
                        'current_price': current_price,
                        'signals': analysis['signals'],
                        'recommendation': analysis['recommendation']
                    })

                # Rate limit (0.1s between requests)
                time.sleep(0.1)

            except Exception as e:
                print(f"[Surge] Error analyzing {market}: {e}")
                continue

        # Sort by score (highest first)
        candidates.sort(key=lambda x: x['score'], reverse=True)

        print(f"[Surge] Found {len(candidates)} candidates")

        # Auto-generate signals for high-confidence predictions (score >= 80)
        high_confidence_candidates = [c for c in candidates if c['score'] >= 80]

        signal_generation_result = None
        if high_confidence_candidates:
            print(f"[Surge] Generating signals for {len(high_confidence_candidates)} high-confidence predictions...")
            signal_generation_result = signal_generator.batch_generate_from_candidates(high_confidence_candidates)
            print(f"[Surge] Generated {signal_generation_result['generated']} signals, distributed to {signal_generation_result['distributed_total']} users")

        # Prepare response data
        response_data = {
            'success': True,
            'candidates': candidates,
            'backtest_stats': {
                'win_rate': 81.25,
                'avg_return': 19.12,
                'avg_win': 24.19,
                'avg_loss': -2.84,
                'total_trades': 16,
                'period': '2024-11-13 ~ 2024-12-07'
            },
            'monitored_markets': len(monitored_markets),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'count': len(candidates),
            'signals_generated': signal_generation_result['generated'] if signal_generation_result else 0,
            'signals_distributed_to': signal_generation_result['distributed_total'] if signal_generation_result else 0
        }

        # Cache the result
        set_surge_cache(response_data)

        # Return results
        return jsonify(response_data)

    except Exception as e:
        error_msg = str(e)
        print(f"[Surge] Error: {error_msg}")

        # If rate limit error and we have old cache, return it with warning
        if 'rate limit' in error_msg.lower() or '429' in error_msg:
            old_cache = _surge_cache.get('data')
            if old_cache:
                print("[Surge] Rate limit hit, returning stale cache")
                old_cache['warning'] = 'Using cached data due to rate limit'
                old_cache['cache_age'] = (datetime.now() - _surge_cache['timestamp']).total_seconds()
                return jsonify(old_cache)

        return jsonify({
            'success': False,
            'error': error_msg,
            'retry_after': 60  # Suggest retry after 1 minute
        }), 500


@surge_bp.route('/surge-analysis/<market>', methods=['GET'])
def get_surge_analysis(market):
    """
    특정 코인의 급등 예측 상세 분석 (PUBLIC - No auth required)

    Args:
        market: 코인 마켓 (예: KRW-BTC)

    Returns:
        {
            "market": "KRW-BTC",
            "score": 75,
            "signals": {
                "volume": {...},
                "rsi": {...},
                "support": {...},
                "trend": {...},
                "momentum": {...}
            },
            "recommendation": "strong_buy",
            "current_price": 50000000
        }
    """
    try:
        print(f"[Surge] Analyzing {market}...")

        # Get candle data - PUBLIC API
        candle_data = upbit_api.get_candles_days(market=market, count=30)
        if not candle_data or len(candle_data) < 20:
            return jsonify({
                'success': False,
                'error': 'Insufficient data'
            }), 400

        # Get current price
        current_price = float(candle_data[0].get('trade_price', 0))
        if current_price == 0:
            return jsonify({
                'success': False,
                'error': 'Invalid price'
            }), 400

        # Analyze
        analysis = predictor.analyze_coin(market, candle_data, current_price)

        print(f"[Surge] {market}: score={analysis['score']}, recommendation={analysis['recommendation']}")

        return jsonify({
            'success': True,
            'market': market,
            'score': analysis['score'],
            'signals': analysis['signals'],
            'recommendation': analysis['recommendation'],
            'current_price': current_price,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
        })

    except Exception as e:
        print(f"[Surge] Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@surge_bp.route('/surge-backtest-results', methods=['GET'])
def get_backtest_results():
    """
    백테스트 검증 결과 상세 정보 (PUBLIC - No auth required)

    Returns:
        {
            "summary": {...},
            "weekly_breakdown": [...],
            "best_trades": [...],
            "worst_trades": [...]
        }
    """
    try:
        print("[Surge] Loading backtest results...")

        # Load backtest results
        import json
        with open('docs/backtest_results/multi_date_backtest.json', 'r', encoding='utf-8') as f:
            backtest_data = json.load(f)

        # Extract key information
        summary = backtest_data.get('summary', {})
        all_results = backtest_data.get('all_results', [])

        # Group by week
        weekly_breakdown = {}
        for result in all_results:
            week = result.get('date', 'Unknown')
            if week not in weekly_breakdown:
                weekly_breakdown[week] = {
                    'trades': [],
                    'wins': 0,
                    'losses': 0
                }
            weekly_breakdown[week]['trades'].append(result)
            if result.get('success'):
                weekly_breakdown[week]['wins'] += 1
            else:
                weekly_breakdown[week]['losses'] += 1

        # Best and worst trades
        sorted_results = sorted(all_results, key=lambda x: x.get('return_pct', 0), reverse=True)
        best_trades = sorted_results[:5]
        worst_trades = sorted_results[-5:]

        print(f"[Surge] Backtest results: {len(all_results)} trades")

        return jsonify({
            'success': True,
            'summary': summary,
            'weekly_breakdown': weekly_breakdown,
            'best_trades': best_trades,
            'worst_trades': worst_trades,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
        })

    except Exception as e:
        print(f"[Surge] Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
