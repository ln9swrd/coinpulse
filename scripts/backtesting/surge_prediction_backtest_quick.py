"""
급등 예측 알고리즘 빠른 백테스트 (최근 1개월)

빠른 검증을 위해 최근 1개월 데이터만 테스트
- 기간: 2024년 11월 13일 ~ 12월 12일 (약 30일)
- 예상 시간: 10-15분
"""

import sys
import os
from datetime import datetime, timedelta
import json
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.common import UpbitAPI, load_api_keys
from backend.services.surge_predictor import SurgePredictor


class QuickBacktest:
    """빠른 백테스트 (최근 1개월)"""

    def __init__(self):
        # Initialize Upbit API
        access_key, secret_key = load_api_keys()
        self.upbit_api = UpbitAPI(access_key, secret_key)

        # Initialize SurgePredictor
        self.config = {
            "surge_prediction": {
                "volume_increase_threshold": 1.5,
                "rsi_oversold_level": 35,
                "rsi_buy_zone_max": 50,
                "support_level_proximity": 0.02,
                "uptrend_confirmation_days": 3,
                "min_surge_probability_score": 60
            }
        }
        self.predictor = SurgePredictor(self.config)

        # Quick test settings
        self.start_date = datetime(2024, 11, 13)
        self.end_date = datetime(2024, 12, 9)  # 3일 전 (holding period 고려)
        self.holding_days = 3
        self.min_score = 60

    def get_candle_data_at_date(self, market, target_date, count=30):
        """특정 날짜 기준 캔들 데이터"""
        try:
            to_date = target_date.strftime('%Y-%m-%d 09:00:00')
            candles = self.upbit_api.get_candles_days(market=market, count=count, to=to_date)
            return candles
        except Exception as e:
            print(f"  [ERROR] {market}: {e}")
            return None

    def get_price_at_date(self, market, target_date):
        """특정 날짜 종가"""
        try:
            candles = self.get_candle_data_at_date(market, target_date, count=1)
            if candles and len(candles) > 0:
                return float(candles[0].get('trade_price', 0))
            return None
        except Exception as e:
            return None

    def run_quick_test(self):
        """빠른 테스트 실행"""
        print("\n" + "="*60)
        print("QUICK BACKTEST (1 Month)")
        print("="*60)
        print(f"Period: {self.start_date.strftime('%Y-%m-%d')} ~ {self.end_date.strftime('%Y-%m-%d')}")
        print(f"Holding: {self.holding_days} days, Min score: {self.min_score}")
        print("="*60)

        # Get markets
        markets = self.upbit_api.get_markets()
        krw_markets = [m['market'] for m in markets if m['market'].startswith('KRW-')]

        # Exclude major coins
        excluded = ['KRW-BTC', 'KRW-ETH', 'KRW-USDT']
        krw_markets = [m for m in krw_markets if m not in excluded]

        print(f"\n[INFO] Testing {len(krw_markets)} coins...")
        print(f"[INFO] Test date: {self.start_date.strftime('%Y-%m-%d')}\n")

        # Test single date
        candidates = []

        for i, market in enumerate(krw_markets, 1):
            if i % 20 == 0:
                print(f"[PROGRESS] {i}/{len(krw_markets)} coins analyzed...")

            try:
                # Get data
                candle_data = self.get_candle_data_at_date(market, self.start_date, count=30)
                if not candle_data or len(candle_data) < 20:
                    continue

                current_price = float(candle_data[0].get('trade_price', 0))
                if current_price == 0:
                    continue

                # Analyze
                analysis = self.predictor.analyze_coin(market, candle_data, current_price)

                if analysis['score'] >= self.min_score:
                    candidates.append({
                        'market': market,
                        'score': analysis['score'],
                        'buy_price': current_price,
                        'signals': analysis['signals']
                    })
                    print(f"  [FOUND] {market}: Score {analysis['score']}")

                time.sleep(0.5)  # Rate limit (increased to avoid 429)

            except Exception as e:
                continue

        print(f"\n[RESULT] Found {len(candidates)} candidates\n")

        # Calculate returns
        sell_date = self.start_date + timedelta(days=self.holding_days)
        print(f"[INFO] Calculating returns (sell date: {sell_date.strftime('%Y-%m-%d')})...\n")

        results = []
        for candidate in candidates:
            market = candidate['market']
            buy_price = candidate['buy_price']

            try:
                sell_price = self.get_price_at_date(market, sell_date)
                if sell_price is None:
                    continue

                return_pct = ((sell_price - buy_price) / buy_price) * 100

                result = {
                    'market': market,
                    'score': candidate['score'],
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'return_pct': return_pct,
                    'success': return_pct > 0
                }

                results.append(result)

                status = "[WIN]" if return_pct > 0 else "[LOSS]"
                print(f"  {status} {market}: {return_pct:+.2f}% ({buy_price:,.0f} -> {sell_price:,.0f})")

                time.sleep(0.5)

            except Exception as e:
                continue

        # Summary
        if results:
            total = len(results)
            wins = len([r for r in results if r['success']])
            losses = total - wins
            win_rate = (wins / total * 100) if total > 0 else 0
            avg_return = sum(r['return_pct'] for r in results) / total if total > 0 else 0

            print("\n" + "="*60)
            print("QUICK TEST SUMMARY")
            print("="*60)
            print(f"Total Trades: {total}")
            print(f"Wins: {wins} ({win_rate:.2f}%)")
            print(f"Losses: {losses}")
            print(f"Average Return: {avg_return:+.2f}%")
            print("="*60)

            if win_rate >= 70:
                print("[EXCELLENT!] Win rate 70%+ - Full backtest recommended!")
            elif win_rate >= 60:
                print("[GOOD!] Win rate 60%+ - Promising results!")
            elif win_rate >= 50:
                print("[FAIR] Win rate 50-60% - Algorithm needs improvement")
            else:
                print("[POOR] Win rate <50% - Algorithm redesign needed")

            # Save results
            output_file = 'docs/backtest_results/quick_backtest.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'test_date': self.start_date.strftime('%Y-%m-%d'),
                    'sell_date': sell_date.strftime('%Y-%m-%d'),
                    'results': results,
                    'summary': {
                        'total_trades': total,
                        'wins': wins,
                        'losses': losses,
                        'win_rate': win_rate,
                        'avg_return': avg_return
                    }
                }, f, ensure_ascii=False, indent=2)
            print(f"\n[SAVE] Results saved to: {output_file}")

        else:
            print("\n[WARN] No results")


def main():
    print("\n" + "="*60)
    print("Quick Backtest - Last 1 Month")
    print("="*60)

    backtest = QuickBacktest()

    try:
        backtest.run_quick_test()
    except KeyboardInterrupt:
        print("\n\n[STOP] Interrupted")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
