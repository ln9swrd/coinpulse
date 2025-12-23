"""
급등 예측 알고리즘 백테스트

과거 3개월 데이터로 급등 예측 알고리즘의 실제 성능 검증
- 기간: 2024년 9월 1일 ~ 12월 12일 (약 100일)
- 방법: 매일 60점 이상 코인 선정 → 3일 후 수익률 확인
- 목표: 적중률 60% 이상 (70%면 매우 우수)
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


class SurgePredictionBacktest:
    """급등 예측 백테스트"""

    def __init__(self):
        # Initialize Upbit API
        access_key, secret_key = load_api_keys()
        self.upbit_api = UpbitAPI(access_key, secret_key)

        # Initialize SurgePredictor with config
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

        # Backtest settings
        self.start_date = datetime(2024, 9, 1)
        self.end_date = datetime(2024, 12, 12)
        self.holding_days = 3  # 3일 보유
        self.min_score = 60  # 최소 점수

        # Results
        self.results = []

    def get_candle_data_at_date(self, market, target_date, count=30):
        """특정 날짜 기준으로 과거 캔들 데이터 조회"""
        try:
            # Convert date to string format
            to_date = target_date.strftime('%Y-%m-%d 09:00:00')

            candles = self.upbit_api.get_candles_days(
                market=market,
                count=count,
                to=to_date
            )

            return candles
        except Exception as e:
            print(f"  [ERROR] Failed to get candle data for {market} at {target_date}: {e}")
            return None

    def get_price_at_date(self, market, target_date):
        """특정 날짜의 종가 조회"""
        try:
            candles = self.get_candle_data_at_date(market, target_date, count=1)
            if candles and len(candles) > 0:
                return float(candles[0].get('trade_price', 0))
            return None
        except Exception as e:
            print(f"  [ERROR] Failed to get price for {market} at {target_date}: {e}")
            return None

    def run_backtest_for_date(self, test_date):
        """특정 날짜에 대해 백테스트 실행"""
        print(f"\n{'='*60}")
        print(f"Testing date: {test_date.strftime('%Y-%m-%d')}")
        print(f"{'='*60}")

        # Get all KRW markets
        markets = self.upbit_api.get_markets()
        krw_markets = [m for m in markets if m['market'].startswith('KRW-')]

        # Exclude major coins (BTC, ETH, USDT)
        excluded = ['KRW-BTC', 'KRW-ETH', 'KRW-USDT']
        krw_markets = [m for m in krw_markets if m['market'] not in excluded]

        print(f"Analyzing {len(krw_markets)} coins...")

        candidates = []

        for market_info in krw_markets:
            market = market_info['market']

            try:
                # Get historical data up to test_date
                candle_data = self.get_candle_data_at_date(market, test_date, count=30)

                if not candle_data or len(candle_data) < 20:
                    continue

                # Get current price (at test_date)
                current_price = float(candle_data[0].get('trade_price', 0))

                if current_price == 0:
                    continue

                # Run surge prediction
                analysis = self.predictor.analyze_coin(market, candle_data, current_price)

                if analysis['score'] >= self.min_score:
                    # Calculate dynamic target prices based on signal strength
                    target_result = self.predictor.get_target_prices(
                        entry_price=int(current_price),
                        analysis_result=analysis,
                        settings={
                            'use_dynamic_target': True,
                            'target_calculation_mode': 'dynamic',
                            'min_target_percent': 5.0,
                            'max_target_percent': 18.0
                        }
                    )

                    candidates.append({
                        'date': test_date.strftime('%Y-%m-%d'),
                        'market': market,
                        'score': analysis['score'],
                        'buy_price': current_price,
                        'target_price': target_result['target_price'],
                        'target_percent': target_result['target_percent'],
                        'stop_loss_price': target_result['stop_loss_price'],
                        'stop_loss_percent': target_result['stop_loss_percent'],
                        'signals': analysis['signals'],
                        'recommendation': analysis['recommendation']
                    })
                    print(f"  [OK] {market}: Score {analysis['score']}, Target +{target_result['target_percent']:.1f}% - {analysis['recommendation']}")

                # Rate limit (10 requests per second)
                time.sleep(0.1)

            except Exception as e:
                print(f"  [ERROR] Failed to analyze {market}: {e}")
                continue

        print(f"\nFound {len(candidates)} candidates (score >= {self.min_score})")

        # Calculate actual returns after holding_days
        sell_date = test_date + timedelta(days=self.holding_days)

        if sell_date > datetime.now():
            print(f"[WARN] Sell date ({sell_date.strftime('%Y-%m-%d')}) is in the future, skipping return calculation")
            return candidates, []

        print(f"\nCalculating returns (sell date: {sell_date.strftime('%Y-%m-%d')})...")

        results = []

        for candidate in candidates:
            market = candidate['market']
            buy_price = candidate['buy_price']
            target_price = candidate.get('target_price', buy_price * 1.05)  # Fallback to +5%
            target_percent = candidate.get('target_percent', 5.0)
            stop_loss_price = candidate.get('stop_loss_price', buy_price * 0.95)

            try:
                # Get price after holding_days
                sell_price = self.get_price_at_date(market, sell_date)

                if sell_price is None:
                    print(f"  [WARN] {market}: No sell price data")
                    continue

                # Calculate return
                return_pct = ((sell_price - buy_price) / buy_price) * 100

                # Determine success based on dynamic target
                # Success if: sell price >= target OR any positive return
                target_hit = sell_price >= target_price
                any_profit = return_pct > 0
                success = target_hit or any_profit

                result = {
                    'date': candidate['date'],
                    'market': market,
                    'score': candidate['score'],
                    'buy_price': buy_price,
                    'target_price': target_price,
                    'target_percent': target_percent,
                    'stop_loss_price': stop_loss_price,
                    'sell_price': sell_price,
                    'return_pct': return_pct,
                    'target_hit': target_hit,
                    'success': success,
                    'signals': candidate['signals']
                }

                results.append(result)

                # Enhanced status display
                if target_hit:
                    status = "[TARGET HIT!]"
                elif any_profit:
                    status = "[WIN]"
                else:
                    status = "[LOSS]"

                print(f"  {status} {market}: {return_pct:+.2f}% (Buy: {buy_price:,.0f} -> Sell: {sell_price:,.0f}, Target: {target_price:,.0f} [{target_percent:+.1f}%])")

                time.sleep(0.1)

            except Exception as e:
                print(f"  [ERROR] Failed to calculate return for {market}: {e}")
                continue

        return candidates, results

    def run_full_backtest(self):
        """전체 기간에 대해 백테스트 실행"""
        print(f"\n[START] Starting Full Backtest")
        print(f"Period: {self.start_date.strftime('%Y-%m-%d')} ~ {self.end_date.strftime('%Y-%m-%d')}")
        print(f"Holding period: {self.holding_days} days")
        print(f"Min score: {self.min_score}")

        all_candidates = []
        all_results = []

        # Test every 7 days (weekly) to reduce API calls
        current_date = self.start_date
        test_dates = []

        while current_date <= self.end_date:
            # Only test if sell_date is before now
            sell_date = current_date + timedelta(days=self.holding_days)
            if sell_date <= datetime.now():
                test_dates.append(current_date)
            current_date += timedelta(days=7)

        print(f"\nTotal test dates: {len(test_dates)}")

        for i, test_date in enumerate(test_dates, 1):
            print(f"\n[PROGRESS] Test {i}/{len(test_dates)}")

            candidates, results = self.run_backtest_for_date(test_date)

            all_candidates.extend(candidates)
            all_results.extend(results)

            # Save intermediate results
            self.save_results(all_candidates, all_results)

            # Rate limit between dates
            time.sleep(1)

        return all_candidates, all_results

    def save_results(self, candidates, results):
        """결과 저장"""
        output_file = 'docs/backtest_results/surge_prediction_backtest.json'

        data = {
            'config': self.config,
            'backtest_period': {
                'start': self.start_date.strftime('%Y-%m-%d'),
                'end': self.end_date.strftime('%Y-%m-%d'),
                'holding_days': self.holding_days
            },
            'candidates': candidates,
            'results': results,
            'summary': self.calculate_summary(results)
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n[SAVE] Results saved to: {output_file}")

    def calculate_summary(self, results):
        """결과 요약 통계 계산 (동적 목표가 포함)"""
        if not results:
            return {}

        total_trades = len(results)
        winning_trades = [r for r in results if r['success']]
        losing_trades = [r for r in results if not r['success']]

        # Target hit statistics
        target_hit_trades = [r for r in results if r.get('target_hit', False)]
        target_hit_rate = (len(target_hit_trades) / total_trades * 100) if total_trades > 0 else 0

        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0

        avg_return = sum(r['return_pct'] for r in results) / total_trades if total_trades > 0 else 0
        avg_win = sum(r['return_pct'] for r in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(r['return_pct'] for r in losing_trades) / len(losing_trades) if losing_trades else 0

        # Average dynamic target percent
        avg_target_percent = sum(r.get('target_percent', 0) for r in results) / total_trades if total_trades > 0 else 0

        best_trade = max(results, key=lambda x: x['return_pct']) if results else None
        worst_trade = min(results, key=lambda x: x['return_pct']) if results else None

        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(win_rate, 2),
            'target_hit_trades': len(target_hit_trades),
            'target_hit_rate': round(target_hit_rate, 2),
            'avg_target_percent': round(avg_target_percent, 2),
            'avg_return': round(avg_return, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'best_trade': {
                'market': best_trade['market'],
                'return': round(best_trade['return_pct'], 2)
            } if best_trade else None,
            'worst_trade': {
                'market': worst_trade['market'],
                'return': round(worst_trade['return_pct'], 2)
            } if worst_trade else None
        }


def main():
    """메인 실행 함수"""
    print("\n" + "="*60)
    print("급등 예측 알고리즘 백테스트")
    print("="*60)

    backtest = SurgePredictionBacktest()

    try:
        candidates, results = backtest.run_full_backtest()

        # Print summary
        if results:
            summary = backtest.calculate_summary(results)

            print("\n" + "="*60)
            print("BACKTEST SUMMARY (Dynamic Targets)")
            print("="*60)
            print(f"Total Trades: {summary['total_trades']}")
            print(f"Winning Trades: {summary['winning_trades']} ({summary['win_rate']:.2f}%)")
            print(f"Losing Trades: {summary['losing_trades']}")
            print(f"\nTarget Hit Trades: {summary['target_hit_trades']} ({summary['target_hit_rate']:.2f}%)")
            print(f"Average Target: {summary['avg_target_percent']:+.2f}%")
            print(f"\nAverage Return: {summary['avg_return']:+.2f}%")
            print(f"Average Win: {summary['avg_win']:+.2f}%")
            print(f"Average Loss: {summary['avg_loss']:+.2f}%")

            if summary['best_trade']:
                print(f"\nBest Trade: {summary['best_trade']['market']} ({summary['best_trade']['return']:+.2f}%)")
            if summary['worst_trade']:
                print(f"Worst Trade: {summary['worst_trade']['market']} ({summary['worst_trade']['return']:+.2f}%)")

            print("\n" + "="*60)

            # Evaluation
            win_rate = summary['win_rate']
            if win_rate >= 70:
                print("[EXCELLENT!] Win rate 70%+ - Ready to launch!")
            elif win_rate >= 60:
                print("[GOOD!] Win rate 60%+ - Launch OK")
            elif win_rate >= 50:
                print("[FAIR] Win rate 50-60% - Algorithm improvement recommended")
            else:
                print("[POOR] Win rate <50% - Algorithm redesign needed")
        else:
            print("\n[WARN] No results to analyze")

    except KeyboardInterrupt:
        print("\n\n[STOP] Backtest interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
