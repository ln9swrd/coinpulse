"""
급등 예측 알고리즘 최소 백테스트

상위 30개 인기 코인만 테스트 (API Rate Limit 회피)
- 예상 시간: 3-5분
- 빠른 검증용
"""

import sys
import os
from datetime import datetime, timedelta
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.common import UpbitAPI, load_api_keys
from backend.services.surge_predictor import SurgePredictor


# 상위 30개 인기 코인 (시가총액 기준)
POPULAR_COINS = [
    'KRW-XRP', 'KRW-ADA', 'KRW-DOGE', 'KRW-AVAX', 'KRW-SHIB',
    'KRW-DOT', 'KRW-MATIC', 'KRW-SOL', 'KRW-LINK', 'KRW-BCH',
    'KRW-NEAR', 'KRW-XLM', 'KRW-ALGO', 'KRW-ATOM', 'KRW-ETC',
    'KRW-VET', 'KRW-ICP', 'KRW-FIL', 'KRW-HBAR', 'KRW-APT',
    'KRW-SAND', 'KRW-MANA', 'KRW-AXS', 'KRW-AAVE', 'KRW-EOS',
    'KRW-THETA', 'KRW-XTZ', 'KRW-EGLD', 'KRW-BSV', 'KRW-ZIL'
]


class MinimalBacktest:
    """최소 백테스트 (상위 30개 코인)"""

    def __init__(self):
        access_key, secret_key = load_api_keys()
        self.upbit_api = UpbitAPI(access_key, secret_key)

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

        self.start_date = datetime(2024, 11, 13)
        self.end_date = datetime(2024, 12, 9)
        self.holding_days = 3
        self.min_score = 60

    def get_candle_data_at_date(self, market, target_date, count=30):
        """특정 날짜 캔들 데이터"""
        try:
            to_date = target_date.strftime('%Y-%m-%d 09:00:00')
            candles = self.upbit_api.get_candles_days(market=market, count=count, to=to_date)
            time.sleep(0.5)  # Rate limit
            return candles
        except Exception as e:
            print(f"  [ERROR] {market}: {e}")
            time.sleep(1)  # Longer wait on error
            return None

    def get_price_at_date(self, market, target_date):
        """특정 날짜 종가"""
        try:
            candles = self.get_candle_data_at_date(market, target_date, count=1)
            if candles and len(candles) > 0:
                return float(candles[0].get('trade_price', 0))
            return None
        except Exception as e:
            time.sleep(1)
            return None

    def run_minimal_test(self):
        """최소 테스트 실행"""
        print("\n" + "="*60)
        print("MINIMAL BACKTEST (Top 30 Coins)")
        print("="*60)
        print(f"Period: {self.start_date.strftime('%Y-%m-%d')} ~ {self.end_date.strftime('%Y-%m-%d')}")
        print(f"Coins: {len(POPULAR_COINS)}")
        print(f"Holding: {self.holding_days} days, Min score: {self.min_score}")
        print("="*60)

        print(f"\n[INFO] Testing {len(POPULAR_COINS)} popular coins...")
        print(f"[INFO] Test date: {self.start_date.strftime('%Y-%m-%d')}\n")

        candidates = []

        for i, market in enumerate(POPULAR_COINS, 1):
            print(f"[{i}/{len(POPULAR_COINS)}] Analyzing {market}...", end=" ")

            try:
                # Get data
                candle_data = self.get_candle_data_at_date(market, self.start_date, count=30)
                if not candle_data or len(candle_data) < 20:
                    print("SKIP (insufficient data)")
                    continue

                current_price = float(candle_data[0].get('trade_price', 0))
                if current_price == 0:
                    print("SKIP (invalid price)")
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
                    print(f"FOUND! Score {analysis['score']}")
                else:
                    print(f"Score {analysis['score']} (< {self.min_score})")

            except Exception as e:
                print(f"ERROR: {e}")
                continue

        print(f"\n[RESULT] Found {len(candidates)} candidates\n")

        if not candidates:
            print("[WARN] No candidates found. Try lowering min_score.")
            return

        # Calculate returns
        sell_date = self.start_date + timedelta(days=self.holding_days)
        print(f"[INFO] Calculating returns (sell date: {sell_date.strftime('%Y-%m-%d')})...\n")

        results = []
        for i, candidate in enumerate(candidates, 1):
            market = candidate['market']
            buy_price = candidate['buy_price']

            print(f"[{i}/{len(candidates)}] {market}...", end=" ")

            try:
                sell_price = self.get_price_at_date(market, sell_date)
                if sell_price is None:
                    print("SKIP (no sell price)")
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

                status = "WIN" if return_pct > 0 else "LOSS"
                print(f"{status} {return_pct:+.2f}% ({buy_price:,.0f} -> {sell_price:,.0f})")

            except Exception as e:
                print(f"ERROR: {e}")
                continue

        # Summary
        if results:
            total = len(results)
            wins = len([r for r in results if r['success']])
            losses = total - wins
            win_rate = (wins / total * 100) if total > 0 else 0
            avg_return = sum(r['return_pct'] for r in results) / total if total > 0 else 0
            avg_win = sum(r['return_pct'] for r in results if r['success']) / wins if wins > 0 else 0
            avg_loss = sum(r['return_pct'] for r in results if not r['success']) / losses if losses > 0 else 0

            best = max(results, key=lambda x: x['return_pct'])
            worst = min(results, key=lambda x: x['return_pct'])

            print("\n" + "="*60)
            print("MINIMAL TEST SUMMARY")
            print("="*60)
            print(f"Total Trades: {total}")
            print(f"Wins: {wins} ({win_rate:.2f}%)")
            print(f"Losses: {losses}")
            print(f"\nAverage Return: {avg_return:+.2f}%")
            print(f"Average Win: {avg_win:+.2f}%")
            print(f"Average Loss: {avg_loss:+.2f}%")
            print(f"\nBest: {best['market']} ({best['return_pct']:+.2f}%)")
            print(f"Worst: {worst['market']} ({worst['return_pct']:+.2f}%)")
            print("="*60)

            if win_rate >= 70:
                print("\n[EXCELLENT!] Win rate 70%+ - Algorithm works!")
                print("Next step: Run full 3-month backtest")
            elif win_rate >= 60:
                print("\n[GOOD!] Win rate 60%+ - Promising results!")
                print("Consider running full backtest for more data")
            elif win_rate >= 50:
                print("\n[FAIR] Win rate 50-60% - Needs improvement")
                print("Try adjusting algorithm parameters")
            else:
                print("\n[POOR] Win rate <50% - Algorithm redesign needed")
                print("Review signal weights and thresholds")

            # Save
            output_file = 'docs/backtest_results/minimal_backtest.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'coins_tested': POPULAR_COINS,
                    'test_date': self.start_date.strftime('%Y-%m-%d'),
                    'sell_date': sell_date.strftime('%Y-%m-%d'),
                    'candidates': candidates,
                    'results': results,
                    'summary': {
                        'total_trades': total,
                        'wins': wins,
                        'losses': losses,
                        'win_rate': win_rate,
                        'avg_return': avg_return,
                        'avg_win': avg_win,
                        'avg_loss': avg_loss,
                        'best_trade': {
                            'market': best['market'],
                            'return': best['return_pct']
                        },
                        'worst_trade': {
                            'market': worst['market'],
                            'return': worst['return_pct']
                        }
                    }
                }, f, ensure_ascii=False, indent=2)
            print(f"\n[SAVE] Results saved to: {output_file}")

        else:
            print("\n[WARN] No valid results")


def main():
    print("\n" + "="*60)
    print("Minimal Backtest - Top 30 Coins")
    print("="*60)

    backtest = MinimalBacktest()

    try:
        backtest.run_minimal_test()
    except KeyboardInterrupt:
        print("\n\n[STOP] Interrupted")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
