#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Manual Surge Scan
수동으로 급등 후보를 스캔하고 캐시 업데이트
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.connection import get_db_session
from backend.models.surge_system_settings import SurgeSystemSettings
from backend.services.surge_predictor import SurgePredictor
from backend.services.dynamic_market_selector import get_market_selector
from backend.common import UpbitAPI, load_api_keys
from backend.models.surge_candidates_cache_models import SurgeCandidatesCache
from datetime import datetime
import time


def manual_scan():
    """Manually scan for surge candidates and update cache"""
    print("[Manual Scan] Starting...")

    # Load system settings
    session = get_db_session()
    try:
        settings = session.query(SurgeSystemSettings).filter_by(id=1).first()
        if not settings:
            print("[Manual Scan] No system settings found!")
            return

        min_score = settings.telegram_min_score
        monitor_count = settings.monitor_coins_count

        print(f"[Manual Scan] Settings:")
        print(f"  - Min score: {min_score}")
        print(f"  - Monitor coins: {monitor_count}")

        # Initialize components
        access_key, secret_key = load_api_keys()
        upbit_api = UpbitAPI(access_key, secret_key)

        analysis_config = settings.get_analysis_config()
        config = {"surge_prediction": analysis_config}
        predictor = SurgePredictor(config)

        market_selector = get_market_selector(target_count=monitor_count)
        monitor_coins = market_selector.get_markets(force_update=True, update_interval_hours=24)

        print(f"[Manual Scan] Monitoring {len(monitor_coins)} coins")

        # Scan for candidates
        candidates = []
        for market in monitor_coins:
            try:
                # Get candle data
                candle_data = upbit_api.get_candles_days(market=market, count=30)
                if not candle_data or len(candle_data) < 20:
                    continue

                # Get current price
                current_price = float(candle_data[0].get('trade_price', 0))
                if current_price == 0:
                    continue

                # Analyze
                analysis = predictor.analyze_coin(market, candle_data, current_price)

                # Add to candidates if score >= min_score
                if analysis['score'] >= min_score:
                    coin = market.replace('KRW-', '')
                    price = round(current_price, 2) if current_price < 100 else int(current_price)

                    candidates.append({
                        'market': market,
                        'coin': coin,
                        'score': analysis['score'],
                        'current_price': price,
                        'analysis': analysis,
                        'signals': analysis['signals'],
                        'recommendation': analysis['recommendation']
                    })

                    print(f"  ✅ {market}: {analysis['score']:.1f} (price: {price:,})")

                # Rate limit
                time.sleep(0.1)

            except Exception as e:
                print(f"  ❌ Error analyzing {market}: {e}")
                continue

        print(f"\n[Manual Scan] Found {len(candidates)} candidates (>= {min_score})")

        # Update cache
        if candidates:
            print("[Manual Scan] Updating cache...")

            for candidate in candidates:
                # Upsert to cache
                existing = session.query(SurgeCandidatesCache).filter_by(
                    market=candidate['market']
                ).first()

                if existing:
                    existing.score = candidate['score']
                    existing.current_price = candidate['current_price']
                    existing.recommendation = candidate['recommendation']
                    existing.signals = candidate['signals']
                    existing.analysis_result = candidate['analysis']
                    existing.analyzed_at = datetime.utcnow()
                    existing.updated_at = datetime.utcnow()
                else:
                    new_cache = SurgeCandidatesCache(
                        market=candidate['market'],
                        coin=candidate['coin'],
                        score=candidate['score'],
                        current_price=candidate['current_price'],
                        recommendation=candidate['recommendation'],
                        signals=candidate['signals'],
                        analysis_result=candidate['analysis'],
                        analyzed_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(new_cache)

            session.commit()
            print(f"[Manual Scan] Cache updated: {len(candidates)} candidates")
        else:
            print("[Manual Scan] No candidates to cache")

        print("\n[Manual Scan] Completed!")

    except Exception as e:
        print(f"[Manual Scan] Error: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    manual_scan()
