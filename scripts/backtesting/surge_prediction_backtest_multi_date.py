"""
급등 예측 알고리즘 다중 날짜 백테스트

여러 날짜에서 일관성 확인 (통계적 유의성)
- 4주간 매주 테스트 (4개 날짜)
- 상위 30개 코인
- 목표: 총 20-30개 거래 확보
"""

import sys
import os
from datetime import datetime, timedelta
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.common import UpbitAPI, load_api_keys
from backend.services.surge_predictor import SurgePredictor


# 상위 30개 인기 코인
POPULAR_COINS = [
    'KRW-XRP', 'KRW-ADA', 'KRW-DOGE', 'KRW-AVAX', 'KRW-SHIB',
    'KRW-DOT', 'KRW-MATIC', 'KRW-SOL', 'KRW-LINK', 'KRW-BCH',
    'KRW-NEAR', 'KRW-XLM', 'KRW-ALGO', 'KRW-ATOM', 'KRW-ETC',
    'KRW-VET', 'KRW-ICP', 'KRW-FIL', 'KRW-HBAR', 'KRW-APT',
    'KRW-SAND', 'KRW-MANA', 'KRW-AXS', 'KRW-AAVE', 'KRW-EOS',
    'KRW-THETA', 'KRW-XTZ', 'KRW-EGLD', 'KRW-BSV', 'KRW-ZIL'
]

# 테스트할 날짜들 (매주)
TEST_DATES = [
    datetime(2024, 11, 13),  # Week 1
    datetime(2024, 11, 20),  # Week 2
    datetime(2024, 11, 27),  # Week 3
    datetime(2024, 12, 4),   # Week 4
]


class MultiDateBacktest:
    """다중 날짜 백테스트"""

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
            time.sleep(1)
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

    def test_single_date(self, test_date):
        """단일 날짜 테스트"""
        print(f"\n{'='*60}")
        print(f"Testing Date: {test_date.strftime('%Y-%m-%d')}")
        print(f"{'='*60}")

        candidates = []

        for i, market in enumerate(POPULAR_COINS, 1):
            print(f"[{i}/{len(POPULAR_COINS)}] {market}...", end=" ")

            try:
                candle_data = self.get_candle_data_at_date(market, test_date, count=30)
                if not candle_data or len(candle_data) < 20:
                    print("SKIP")
                    continue

                current_price = float(candle_data[0].get('trade_price', 0))
                if current_price == 0:
                    print("SKIP")
                    continue

                analysis = self.predictor.analyze_coin(market, candle_data, current_price)

                if analysis['score'] >= self.min_score:
                    candidates.append({
                        'date': test_date.strftime('%Y-%m-%d'),
                        'market': market,
                        'score': analysis['score'],
                        'buy_price': current_price,
                        'signals': analysis['signals']
                    })
                    print(f"FOUND (Score {analysis['score']})")
                else:
                    print(f"Score {analysis['score']}")

            except Exception as e:
                print(f"ERROR")
                continue

        print(f"\n[RESULT] {len(candidates)} candidates found")

        # Calculate returns
        sell_date = test_date + timedelta(days=self.holding_days)

        # Check if sell_date is in the future
        if sell_date > datetime.now():
            print(f"[WARN] Sell date ({sell_date.strftime('%Y-%m-%d')}) is in the future, skipping")
            return candidates, []

        print(f"[INFO] Calculating returns (sell date: {sell_date.strftime('%Y-%m-%d')})...")

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
                    'date': candidate['date'],
                    'market': market,
                    'score': candidate['score'],
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'return_pct': return_pct,
                    'success': return_pct > 0
                }

                results.append(result)

                status = "WIN" if return_pct > 0 else "LOSS"
                print(f"  {status} {market}: {return_pct:+.2f}%")

            except Exception as e:
                continue

        return candidates, results

    def run_multi_date_test(self):
        """다중 날짜 테스트 실행"""
        print("\n" + "="*60)
        print("MULTI-DATE BACKTEST")
        print("="*60)
        print(f"Test Dates: {len(TEST_DATES)}")
        print(f"Coins per date: {len(POPULAR_COINS)}")
        print(f"Holding: {self.holding_days} days, Min score: {self.min_score}")
        print("="*60)

        all_candidates = []
        all_results = []

        for i, test_date in enumerate(TEST_DATES, 1):
            print(f"\n\n[{i}/{len(TEST_DATES)}] Testing {test_date.strftime('%Y-%m-%d')}...")

            candidates, results = self.test_single_date(test_date)

            all_candidates.extend(candidates)
            all_results.extend(results)

            print(f"[SUMMARY] Date {i}: {len(candidates)} candidates, {len(results)} valid trades")

            # Rate limit between dates
            time.sleep(2)

        # Overall summary
        self.print_summary(all_results)

        # Save results
        output_file = 'docs/backtest_results/multi_date_backtest.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_dates': [d.strftime('%Y-%m-%d') for d in TEST_DATES],
                'coins_tested': POPULAR_COINS,
                'holding_days': self.holding_days,
                'min_score': self.min_score,
                'all_candidates': all_candidates,
                'all_results': all_results,
                'summary': self.calculate_summary(all_results)
            }, f, ensure_ascii=False, indent=2)
        print(f"\n[SAVE] Results saved to: {output_file}")

    def calculate_summary(self, results):
        """결과 요약 계산"""
        if not results:
            return {}

        total = len(results)
        wins = len([r for r in results if r['success']])
        losses = total - wins
        win_rate = (wins / total * 100) if total > 0 else 0

        avg_return = sum(r['return_pct'] for r in results) / total if total > 0 else 0
        avg_win = sum(r['return_pct'] for r in results if r['success']) / wins if wins > 0 else 0
        avg_loss = sum(r['return_pct'] for r in results if not r['success']) / losses if losses > 0 else 0

        best = max(results, key=lambda x: x['return_pct']) if results else None
        worst = min(results, key=lambda x: x['return_pct']) if results else None

        return {
            'total_trades': total,
            'wins': wins,
            'losses': losses,
            'win_rate': round(win_rate, 2),
            'avg_return': round(avg_return, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'best_trade': {
                'date': best['date'],
                'market': best['market'],
                'return': round(best['return_pct'], 2)
            } if best else None,
            'worst_trade': {
                'date': worst['date'],
                'market': worst['market'],
                'return': round(worst['return_pct'], 2)
            } if worst else None
        }

    def print_summary(self, results):
        """결과 요약 출력"""
        if not results:
            print("\n[WARN] No valid results")
            return

        summary = self.calculate_summary(results)

        print("\n\n" + "="*60)
        print("MULTI-DATE BACKTEST SUMMARY")
        print("="*60)
        print(f"Total Trades: {summary['total_trades']}")
        print(f"Wins: {summary['wins']} ({summary['win_rate']:.2f}%)")
        print(f"Losses: {summary['losses']}")
        print(f"\nAverage Return: {summary['avg_return']:+.2f}%")
        print(f"Average Win: {summary['avg_win']:+.2f}%")
        print(f"Average Loss: {summary['avg_loss']:+.2f}%")

        if summary['best_trade']:
            print(f"\nBest Trade:")
            print(f"  {summary['best_trade']['date']} - {summary['best_trade']['market']}: {summary['best_trade']['return']:+.2f}%")

        if summary['worst_trade']:
            print(f"Worst Trade:")
            print(f"  {summary['worst_trade']['date']} - {summary['worst_trade']['market']}: {summary['worst_trade']['return']:+.2f}%")

        print("="*60)

        # Evaluation
        win_rate = summary['win_rate']
        if win_rate >= 70:
            print("\n[EXCELLENT!] Win rate 70%+ - Algorithm validated!")
            print("Next: Build UI and launch beta")
        elif win_rate >= 60:
            print("\n[GOOD!] Win rate 60%+ - Algorithm works!")
            print("Consider launching with monitoring")
        elif win_rate >= 50:
            print("\n[FAIR] Win rate 50-60% - Needs improvement")
            print("Review algorithm parameters")
        else:
            print("\n[POOR] Win rate <50% - Algorithm redesign needed")
            print("Consider different indicators or weights")


def main():
    print("\n" + "="*60)
    print("Multi-Date Backtest - 4 Weeks")
    print("="*60)

    backtest = MultiDateBacktest()

    try:
        backtest.run_multi_date_test()
    except KeyboardInterrupt:
        print("\n\n[STOP] Interrupted")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
