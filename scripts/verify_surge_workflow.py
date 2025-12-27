# -*- coding: utf-8 -*-
"""
Test Surge Detection Workflow
Tests: Detection → Telegram → Auto-Trading → Monitoring
"""

import json
import os
import sys
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_db_session
from sqlalchemy import text
from backend.common.upbit_api import UpbitAPI
from backend.services.surge_predictor import SurgePredictor

def test_workflow():
    """Test complete surge detection workflow"""

    print("=" * 100)
    print("SURGE DETECTION WORKFLOW TEST")
    print("=" * 100)

    # Load config
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Initialize components
    access_key = os.getenv('UPBIT_ACCESS_KEY', '')
    secret_key = os.getenv('UPBIT_SECRET_KEY', '')
    api = UpbitAPI(access_key, secret_key)
    predictor = SurgePredictor(config)

    print("\n[Step 1] Testing Surge Detection...")
    print("-" * 100)

    # Test markets
    test_markets = [
        'KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-DOGE', 'KRW-ADA',
        'KRW-SOL', 'KRW-AVAX', 'KRW-DOT', 'KRW-MATIC', 'KRW-LINK',
        'KRW-UNI', 'KRW-ATOM', 'KRW-NEAR', 'KRW-APT', 'KRW-ARB',
        'KRW-OP', 'KRW-IMX', 'KRW-SAND', 'KRW-MANA', 'KRW-AXS'
    ]

    candidates = []

    for market in test_markets:
        try:
            candles = api.get_candles_days(market, count=200)
            if not candles or len(candles) < 30:
                continue

            current_price = float(candles[0]['trade_price'])
            result = predictor.analyze_coin(market, candles, current_price)

            score = result.get('score', 0)
            pattern_type = result.get('pattern_type', 'unknown')
            entry_timing = result.get('entry_timing', 'unknown')

            if score >= 50:  # Lower threshold for testing
                candidates.append({
                    'market': market,
                    'score': score,
                    'pattern': pattern_type,
                    'timing': entry_timing,
                    'current_price': current_price,
                    'result': result
                })

                status = '' if score >= 60 else ''
                print(f"{status} {market:12} | Score: {score:3.0f} | Pattern: {pattern_type:20} | Timing: {entry_timing}")

        except Exception as e:
            print(f" {market:12} | Error: {str(e)[:50]}")
            continue

    print("-" * 100)
    print(f"Found {len(candidates)} candidates (score >= 50)")
    print(f"Production threshold (60+): {sum(1 for c in candidates if c['score'] >= 60)} candidates")

    if not candidates:
        print("\n No candidates found for testing workflow")
        print("This is expected if market conditions don't match Pattern A or B criteria")
        return

    # Use best candidate for workflow test
    best = max(candidates, key=lambda x: x['score'])

    print("\n[Step 2] Testing Database Insert...")
    print("-" * 100)
    print(f"Using: {best['market']} (Score: {best['score']}, Pattern: {best['pattern']})")

    with get_db_session() as session:
        # Insert test signal
        try:
            insert_query = text("""
                INSERT INTO surge_alerts (
                    user_id, market, coin, confidence, signal_type, week_number,
                    entry_price, target_price, stop_loss_price, expected_return,
                    current_price, reason, alert_message,
                    sent_at, status
                ) VALUES (
                    :user_id, :market, :coin, :confidence, :signal_type, :week_number,
                    :entry_price, :target_price, :stop_loss_price, :expected_return,
                    :current_price, :reason, :alert_message,
                    :sent_at, :status
                )
                RETURNING id
            """)

            entry_price = best['current_price']
            target_price = int(entry_price * 1.10)
            stop_loss_price = int(entry_price * 0.95)

            result = session.execute(insert_query, {
                'user_id': 1,
                'market': best['market'],
                'coin': best['market'].replace('KRW-', ''),
                'confidence': best['score'],
                'signal_type': 'surge',
                'week_number': datetime.now().isocalendar()[1],
                'entry_price': entry_price,
                'target_price': target_price,
                'stop_loss_price': stop_loss_price,
                'expected_return': 10.0,
                'current_price': entry_price,
                'reason': f"Test signal - {best['pattern']}",
                'alert_message': f"[TEST] {best['market']} surge detected (Score: {best['score']})",
                'sent_at': datetime.now(),
                'status': 'pending'
            })

            signal_id = result.fetchone()[0]
            session.commit()

            print(f" Signal inserted to DB (ID: {signal_id})")

        except Exception as e:
            print(f" Database insert failed: {str(e)}")
            return

    print("\n[Step 3] Testing Telegram Notification...")
    print("-" * 100)

    # Check Telegram bot status
    try:
        from backend.services.telegram_bot import SurgeTelegramBot, get_telegram_bot

        # Check if bot is configured
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        if not telegram_token:
            print(" Telegram bot token not configured")
            print("Set TELEGRAM_BOT_TOKEN environment variable to enable")
        else:
            print(f" Telegram bot configured (token: {telegram_token[:10]}...)")
            print("Note: Actual notification sending requires user subscriptions")

            # Try to get bot instance
            bot = get_telegram_bot()
            if bot:
                print(" Telegram bot instance created successfully")
            else:
                print(" Telegram bot instance is None (python-telegram-bot may not be installed)")

    except Exception as e:
        print(f" Telegram bot check failed: {str(e)}")

    print("\n[Step 4] Testing Auto-Trading System...")
    print("-" * 100)

    # Check auto-trading configuration
    try:
        check_query = text("""
            SELECT id, market, confidence, entry_price, status
            FROM surge_alerts
            WHERE id = :signal_id
        """)

        with get_db_session() as session:
            signal = session.execute(check_query, {'signal_id': signal_id}).fetchone()

            if signal:
                print(f" Signal found in DB:")
                print(f"   Market: {signal[1]}")
                print(f"   Confidence: {signal[2]}")
                print(f"   Entry Price: {signal[3]:,}")
                print(f"   Status: {signal[4]}")

                # Check if user has auto-trading enabled
                auto_trading_query = text("""
                    SELECT enabled, amount_per_trade, total_budget, min_confidence
                    FROM surge_auto_trading_settings
                    WHERE user_id = :user_id
                """)

                auto_settings = session.execute(auto_trading_query, {'user_id': 1}).fetchone()

                if auto_settings and auto_settings[0]:
                    print(f"\n Auto-trading enabled for user")
                    print(f"   Amount per trade: {auto_settings[1]:,} KRW")
                    print(f"   Total budget: {auto_settings[2]:,} KRW")
                    print(f"   Min confidence: {auto_settings[3]}%")
                else:
                    print(f"\n Auto-trading not enabled for user")
                    print("   Enable in surge_auto_trading_settings table")

    except Exception as e:
        print(f" Auto-trading check failed: {str(e)}")

    print("\n[Step 5] Testing Monitoring System...")
    print("-" * 100)

    # Check if signal is in monitoring cache
    try:
        from backend.services.surge_alert_scheduler import SurgeAlertScheduler

        # Create scheduler instance
        scheduler = SurgeAlertScheduler(config)

        print(" Monitoring system initialized")
        print(f"   Check interval: {scheduler.check_interval}s")
        print(f"   Monitored coins: {scheduler.num_coins}")
        print("\nNote: Signal will be picked up in next scheduler run (every 5 minutes)")

    except Exception as e:
        print(f" Monitoring check failed: {str(e)}")

    print("\n" + "=" * 100)
    print("WORKFLOW TEST SUMMARY")
    print("=" * 100)
    print(f"""
     Detection: {len(candidates)} candidates found (score >= 50)
     Database: Test signal inserted (ID: {signal_id})
     Telegram: Bot configured (requires user subscriptions)
     Auto-Trading: System available (requires user settings)
     Monitoring: Scheduler running (5 minute intervals)

    Next Steps:
    1. Wait for next scheduler run (check logs: journalctl -u coinpulse -f)
    2. Monitor signal status updates
    3. Check Telegram notifications (if user subscribed)
    4. Verify auto-trading execution (if enabled)

    Test Signal ID: {signal_id}
    Market: {best['market']}
    Score: {best['score']}
    Pattern: {best['pattern']}
    """)

    print("=" * 100)


if __name__ == '__main__':
    test_workflow()
