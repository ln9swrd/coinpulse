# -*- coding: utf-8 -*-
"""
Surge Predictor V2 - Early Detection Strategy

Detects coins BEFORE they surge (Day 1-2 entry, not Day 4)
Strategy: Accumulation Phase → Early Breakout → 3-day profit target

Key difference from V1:
- V1: Detects coins already surging (late entry, high risk)
- V2: Detects coins preparing to surge (early entry, low risk)
"""

import statistics


class SurgePredictorV2:
    """
    Early Detection Surge Predictor.

    Analysis factors (NEW):
    1. Accumulation Phase (25 points) - 거래량 증가 + 가격 횡보
    2. Support Bounce (25 points) - 지지선 반등 초기
    3. Early Momentum (20 points) - 초기 상승 (3-8%)
    4. Volume Timing (20 points) - 거래량 급증 첫날
    5. Pattern Recognition (10 points) - 상승 패턴 초기

    Avoids:
    - Coins already up 10%+ (too late)
    - RSI > 60 (overbought)
    - Volume 5x+ (already exploded)
    """

    def __init__(self, config):
        self.config = config
        self.surge_config = config.get('surge_prediction', {})

    def analyze_coin(self, coin_symbol, candle_data, current_price):
        """
        Analyze coin for EARLY surge signals.

        Args:
            coin_symbol: Coin symbol
            candle_data: Historical candle data (list of dicts)
            current_price: Current market price

        Returns:
            {
                'coin': coin_symbol,
                'score': int (0-100),
                'signals': dict,
                'recommendation': str,
                'entry_timing': str (early/late/missed)
            }
        """
        try:
            if not candle_data or len(candle_data) < 30:
                return {
                    'coin': coin_symbol,
                    'score': 0,
                    'signals': {},
                    'recommendation': 'insufficient_data',
                    'entry_timing': 'unknown'
                }

            # Calculate all signals
            signals = {}

            # 1. Accumulation Phase Detection (거래량 증가 + 가격 횡보)
            signals['accumulation'] = self._detect_accumulation(candle_data)

            # 2. Support Bounce Detection (지지선 반등 초기)
            signals['support_bounce'] = self._detect_support_bounce(candle_data, current_price)

            # 3. Early Momentum Detection (초기 상승 3-8%)
            signals['early_momentum'] = self._detect_early_momentum(candle_data)

            # 4. Volume Timing (거래량 급증 타이밍)
            signals['volume_timing'] = self._detect_volume_timing(candle_data)

            # 5. Pattern Recognition (상승 패턴 초기)
            signals['pattern'] = self._detect_pattern(candle_data)

            # Calculate total score
            total_score = self._calculate_score(signals)

            # Determine entry timing
            entry_timing = self._assess_entry_timing(candle_data, current_price, signals)

            # Generate recommendation
            min_score = self.surge_config.get('min_surge_probability_score', 70)

            if entry_timing == 'late' or entry_timing == 'missed':
                recommendation = 'pass'  # Too late, don't chase
            elif total_score >= min_score:
                recommendation = 'strong_buy'
            elif total_score >= 60:
                recommendation = 'buy'
            elif total_score >= 50:
                recommendation = 'hold'
            else:
                recommendation = 'pass'

            return {
                'coin': coin_symbol,
                'score': total_score,
                'signals': signals,
                'recommendation': recommendation,
                'entry_timing': entry_timing,
                'current_price': current_price
            }

        except Exception as e:
            print(f"[SurgePredictorV2] ERROR analyzing {coin_symbol}: {e}")
            return {
                'coin': coin_symbol,
                'score': 0,
                'signals': {},
                'recommendation': 'error',
                'entry_timing': 'unknown'
            }

    def _detect_accumulation(self, candle_data):
        """
        Detect Accumulation Phase (축적 단계).

        Signs:
        - Volume increasing 1.5-3x (not 5x+ yet)
        - Price consolidating (sideways ±5%)
        - Volatility decreasing

        Returns: score 0-25
        """
        try:
            # Get recent data
            recent_volumes = [float(c.get('candle_acc_trade_price', 0)) for c in candle_data[:7]]
            avg_volume = statistics.mean([float(c.get('candle_acc_trade_price', 0)) for c in candle_data[7:30]])

            recent_prices = [float(c.get('trade_price', 0)) for c in candle_data[:7]]

            if not recent_volumes or not recent_prices or avg_volume == 0:
                return {'score': 0, 'description': 'No data'}

            # 1. Volume increase (1.5-3x is ideal, not 5x+)
            current_volume = recent_volumes[0]
            volume_ratio = current_volume / avg_volume

            volume_score = 0
            if 1.5 <= volume_ratio < 2.5:
                volume_score = 15  # Perfect - starting to increase
            elif 2.5 <= volume_ratio < 4.0:
                volume_score = 10  # Good - increasing
            elif volume_ratio >= 4.0:
                volume_score = 0   # Too late - already exploded

            # 2. Price consolidation (low volatility)
            price_std = statistics.stdev(recent_prices) if len(recent_prices) > 1 else 0
            price_mean = statistics.mean(recent_prices)
            volatility_pct = (price_std / price_mean * 100) if price_mean > 0 else 0

            consolidation_score = 0
            if volatility_pct < 3:
                consolidation_score = 10  # Very stable - accumulating
            elif volatility_pct < 5:
                consolidation_score = 7   # Stable
            elif volatility_pct < 8:
                consolidation_score = 3   # Moderate
            else:
                consolidation_score = 0   # Too volatile

            total = volume_score + consolidation_score

            return {
                'score': min(25, total),
                'volume_ratio': volume_ratio,
                'volatility_pct': volatility_pct,
                'description': f'Accumulation (vol: {volume_ratio:.1f}x, volatility: {volatility_pct:.1f}%)'
            }

        except Exception as e:
            print(f"[SurgePredictorV2] Accumulation detection error: {e}")
            return {'score': 0, 'description': 'Error'}

    def _detect_support_bounce(self, candle_data, current_price):
        """
        Detect Support Bounce (지지선 반등).

        Signs:
        - Price near support (within 5%)
        - Bouncing off support (1-3 days ago)
        - Volume increasing during bounce

        Returns: score 0-25
        """
        try:
            # Find support level (lowest low in last 30 days)
            lows = [float(c.get('low_price', 0)) for c in candle_data[:30]]
            support_level = min(lows) if lows else 0

            if support_level == 0 or current_price == 0:
                return {'score': 0, 'description': 'No support data'}

            # Distance from support
            distance_pct = ((current_price - support_level) / support_level) * 100

            # Check if recently bounced (was near support 1-3 days ago)
            recent_lows = [float(c.get('low_price', 0)) for c in candle_data[:3]]
            touched_support = any(abs((low - support_level) / support_level * 100) < 2 for low in recent_lows)

            # Check if price is recovering (higher than recent low)
            recent_low = min(recent_lows) if recent_lows else current_price
            is_recovering = current_price > recent_low * 1.01  # At least 1% above recent low

            score = 0

            # Score based on distance and bounce confirmation
            if distance_pct <= 3 and touched_support and is_recovering:
                score = 25  # Perfect - just bounced off support
            elif distance_pct <= 5 and touched_support:
                score = 20  # Good - near support, bouncing
            elif distance_pct <= 5:
                score = 15  # Near support
            elif distance_pct <= 8:
                score = 10  # Close to support
            elif distance_pct <= 12:
                score = 5   # Moderate distance
            else:
                score = 0   # Too far from support

            return {
                'score': score,
                'support_level': support_level,
                'distance_pct': distance_pct,
                'touched_support': touched_support,
                'description': f'Support bounce ({distance_pct:.1f}% above support)'
            }

        except Exception as e:
            print(f"[SurgePredictorV2] Support bounce error: {e}")
            return {'score': 0, 'description': 'Error'}

    def _detect_early_momentum(self, candle_data):
        """
        Detect Early Momentum (초기 모멘텀).

        Ideal: 3-8% gain in recent 3-5 days
        Too low: < 3% (not moving yet)
        Too high: > 10% (already late)

        Returns: score 0-20
        """
        try:
            # Get prices for last 5 days
            prices = [float(c.get('trade_price', 0)) for c in candle_data[:5]]

            if len(prices) < 5 or prices[-1] == 0:
                return {'score': 0, 'description': 'Insufficient data'}

            # Calculate momentum
            oldest_price = prices[-1]
            newest_price = prices[0]
            momentum_pct = ((newest_price - oldest_price) / oldest_price) * 100

            # Also check RSI
            rsi = self._calculate_rsi(candle_data, period=14)

            score = 0

            # Sweet spot: 3-8% gain
            if 3 <= momentum_pct <= 8:
                if 40 <= rsi <= 55:
                    score = 20  # Perfect - early stage, good RSI
                elif 35 <= rsi <= 60:
                    score = 15  # Good
                else:
                    score = 10  # Momentum ok, RSI not ideal

            # Too little momentum
            elif 1 <= momentum_pct < 3:
                score = 8   # Starting to move

            # Too much momentum (already late)
            elif momentum_pct > 10:
                score = 0   # Too late, don't chase

            # Negative momentum
            else:
                score = 0

            return {
                'score': score,
                'momentum_pct': momentum_pct,
                'rsi': rsi,
                'description': f'Early momentum ({momentum_pct:+.1f}%, RSI: {rsi:.0f})'
            }

        except Exception as e:
            print(f"[SurgePredictorV2] Early momentum error: {e}")
            return {'score': 0, 'description': 'Error'}

    def _detect_volume_timing(self, candle_data):
        """
        Detect Volume Spike Timing (거래량 급증 타이밍).

        Best: 2-3x volume increase (first day of spike)
        Late: 4-5x+ (already exploded)

        Returns: score 0-20
        """
        try:
            # Current and recent volume
            current_volume = float(candle_data[0].get('candle_acc_trade_price', 0))
            avg_volume = statistics.mean([float(c.get('candle_acc_trade_price', 0)) for c in candle_data[7:21]])

            if avg_volume == 0:
                return {'score': 0, 'description': 'No volume data'}

            volume_ratio = current_volume / avg_volume

            # Check if this is first day of spike
            yesterday_volume = float(candle_data[1].get('candle_acc_trade_price', 0))
            yesterday_ratio = yesterday_volume / avg_volume if avg_volume > 0 else 0

            is_first_spike_day = volume_ratio >= 2.0 and yesterday_ratio < 2.0

            score = 0

            # Perfect timing: 2-3x on first day
            if 2.0 <= volume_ratio < 3.0 and is_first_spike_day:
                score = 20
            elif 2.0 <= volume_ratio < 3.0:
                score = 15

            # Good: 3-4x
            elif 3.0 <= volume_ratio < 4.0:
                score = 12

            # Already spiked (late)
            elif volume_ratio >= 4.0:
                score = 5  # Too late

            # Not enough volume
            elif 1.5 <= volume_ratio < 2.0:
                score = 8  # Building up
            else:
                score = 0

            return {
                'score': score,
                'volume_ratio': volume_ratio,
                'is_first_spike': is_first_spike_day,
                'description': f'Volume timing ({volume_ratio:.1f}x, {"first spike" if is_first_spike_day else "ongoing"})'
            }

        except Exception as e:
            print(f"[SurgePredictorV2] Volume timing error: {e}")
            return {'score': 0, 'description': 'Error'}

    def _detect_pattern(self, candle_data):
        """
        Detect Bullish Pattern (상승 패턴).

        Patterns:
        - Higher Lows (저점 상승)
        - Higher Highs (고점 상승)
        - Triangle consolidation

        Returns: score 0-10
        """
        try:
            # Get recent highs and lows
            recent_highs = [float(c.get('high_price', 0)) for c in candle_data[:10]]
            recent_lows = [float(c.get('low_price', 0)) for c in candle_data[:10]]

            if len(recent_highs) < 10:
                return {'score': 0, 'description': 'Insufficient data'}

            # Check for Higher Lows
            low_1 = min(recent_lows[0:3])
            low_2 = min(recent_lows[3:6])
            low_3 = min(recent_lows[6:9])

            higher_lows = low_1 > low_2 > low_3

            # Check for Higher Highs
            high_1 = max(recent_highs[0:3])
            high_2 = max(recent_highs[3:6])
            high_3 = max(recent_highs[6:9])

            higher_highs = high_1 > high_2 > high_3

            score = 0
            if higher_lows and higher_highs:
                score = 10  # Strong uptrend pattern
            elif higher_lows:
                score = 7   # Support building
            elif higher_highs:
                score = 5   # Breaking resistance
            else:
                score = 0

            return {
                'score': score,
                'higher_lows': higher_lows,
                'higher_highs': higher_highs,
                'description': f'Pattern (HL: {higher_lows}, HH: {higher_highs})'
            }

        except Exception as e:
            print(f"[SurgePredictorV2] Pattern detection error: {e}")
            return {'score': 0, 'description': 'Error'}

    def _calculate_rsi(self, candle_data, period=14):
        """Calculate RSI indicator."""
        try:
            prices = [float(c.get('trade_price', 0)) for c in candle_data[:period+1]]

            if len(prices) < period + 1:
                return 50  # Default neutral

            gains = []
            losses = []

            for i in range(1, len(prices)):
                change = prices[i-1] - prices[i]  # Note: reversed order
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))

            avg_gain = sum(gains) / period
            avg_loss = sum(losses) / period

            if avg_loss == 0:
                return 100

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            return rsi

        except Exception as e:
            print(f"[SurgePredictorV2] RSI calculation error: {e}")
            return 50

    def _calculate_score(self, signals):
        """
        Calculate total score (0-100).

        Weights:
        - Accumulation: 25 points
        - Support Bounce: 25 points
        - Early Momentum: 20 points
        - Volume Timing: 20 points
        - Pattern: 10 points
        Total: 100 points
        """
        total = 0
        total += signals.get('accumulation', {}).get('score', 0)
        total += signals.get('support_bounce', {}).get('score', 0)
        total += signals.get('early_momentum', {}).get('score', 0)
        total += signals.get('volume_timing', {}).get('score', 0)
        total += signals.get('pattern', {}).get('score', 0)

        return min(100, max(0, total))

    def _assess_entry_timing(self, candle_data, current_price, signals):
        """
        Assess if entry timing is early/good/late/missed.

        Returns: 'early', 'good', 'late', 'missed'
        """
        try:
            # Get momentum
            momentum_pct = signals.get('early_momentum', {}).get('momentum_pct', 0)
            volume_ratio = signals.get('volume_timing', {}).get('volume_ratio', 0)

            # Get 30-day high
            highs_30d = [float(c.get('high_price', 0)) for c in candle_data[:30]]
            recent_high = max(highs_30d) if highs_30d else current_price
            price_position = (current_price / recent_high * 100) if recent_high > 0 else 0

            # Early: Just starting to move
            if momentum_pct < 5 and volume_ratio < 3 and price_position < 80:
                return 'early'

            # Good: Moving but not too much
            elif momentum_pct < 8 and volume_ratio < 4 and price_position < 85:
                return 'good'

            # Late: Already moved significantly
            elif momentum_pct < 12 or volume_ratio < 5 or price_position < 90:
                return 'late'

            # Missed: Too late, don't chase
            else:
                return 'missed'

        except Exception as e:
            print(f"[SurgePredictorV2] Entry timing error: {e}")
            return 'unknown'

    def get_target_prices(self, entry_price, analysis_result, settings=None):
        """
        Calculate target and stop loss prices.
        Same as V1 for compatibility.
        """
        if settings is None:
            settings = {}

        take_profit = settings.get('take_profit_percent', 10.0)
        stop_loss = settings.get('stop_loss_percent', -5.0)

        target_price = int(entry_price * (1 + take_profit / 100))
        stop_loss_price = int(entry_price * (1 + stop_loss / 100))

        return {
            'target_price': target_price,
            'stop_loss_price': stop_loss_price,
            'target_percent': take_profit,
            'stop_loss_percent': stop_loss,
            'calculation_mode': 'user_settings'
        }
