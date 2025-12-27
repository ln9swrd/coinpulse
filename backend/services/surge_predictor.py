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


class SurgePredictor:
    """
    Dual-Pattern Surge Predictor.

    PATTERN A - Accumulation (기존):
    1. Accumulation Phase (25 points) - 거래량 증가 + 가격 횡보
    2. Support Bounce (25 points) - 지지선 반등 초기
    3. Early Momentum (20 points) - 초기 상승 (3-8%)
    4. Volume Timing (20 points) - 거래량 급증 첫날
    5. Pattern Recognition (10 points) - 상승 패턴 초기

    PATTERN B - Oversold Bounce (신규):
    1. Oversold Detection (30 points) - RSI < 30, 급락 -10% ~ -25%
    2. Volume Reversal (35 points) - 거래량 반등 시작
    3. Panic Recovery (35 points) - 공황 후 회복 신호

    Strategy: Use higher score from Pattern A or B
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

            # ===== PATTERN A: Accumulation =====
            signals_a = {}
            signals_a['accumulation'] = self._detect_accumulation(candle_data)
            signals_a['support_bounce'] = self._detect_support_bounce(candle_data, current_price)
            signals_a['early_momentum'] = self._detect_early_momentum(candle_data)
            signals_a['volume_timing'] = self._detect_volume_timing(candle_data)
            signals_a['pattern'] = self._detect_pattern(candle_data)

            score_a = self._calculate_score_pattern_a(signals_a)

            # ===== PATTERN B: Oversold Bounce =====
            signals_b = {}
            signals_b['oversold_detection'] = self._detect_oversold(candle_data)
            signals_b['volume_reversal'] = self._detect_volume_reversal(candle_data)
            signals_b['panic_recovery'] = self._detect_panic_recovery(candle_data, current_price)

            score_b = self._calculate_score_pattern_b(signals_b)

            # ===== Choose better pattern =====
            if score_a >= score_b:
                total_score = score_a
                signals = signals_a
                pattern_type = 'A_Accumulation'
                entry_timing = self._assess_entry_timing(candle_data, current_price, signals_a)
            else:
                total_score = score_b
                signals = signals_b
                pattern_type = 'B_OversoldBounce'
                entry_timing = self._assess_entry_timing_pattern_b(candle_data, current_price, signals_b)

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
                'pattern_type': pattern_type,
                'current_price': current_price
            }

        except Exception as e:
            print(f"[SurgePredictor] ERROR analyzing {coin_symbol}: {e}")
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
            print(f"[SurgePredictor] Accumulation detection error: {e}")
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
            print(f"[SurgePredictor] Support bounce error: {e}")
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
            print(f"[SurgePredictor] Early momentum error: {e}")
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
            print(f"[SurgePredictor] Volume timing error: {e}")
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
            print(f"[SurgePredictor] Pattern detection error: {e}")
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
            print(f"[SurgePredictor] RSI calculation error: {e}")
            return 50

    def _calculate_score_pattern_a(self, signals):
        """
        Calculate Pattern A score (0-100).

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

    def _calculate_score_pattern_b(self, signals):
        """
        Calculate Pattern B score (0-100).

        Weights:
        - Oversold Detection: 30 points
        - Volume Reversal: 35 points
        - Panic Recovery: 35 points
        Total: 100 points
        """
        total = 0
        total += signals.get('oversold_detection', {}).get('score', 0)
        total += signals.get('volume_reversal', {}).get('score', 0)
        total += signals.get('panic_recovery', {}).get('score', 0)

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
            print(f"[SurgePredictor] Entry timing error: {e}")
            return 'unknown'

    def _assess_entry_timing_pattern_b(self, candle_data, current_price, signals):
        """
        Assess entry timing for Pattern B (Oversold Bounce).

        Returns: 'early', 'good', 'late', 'missed'
        """
        try:
            # Get oversold data
            oversold_data = signals.get('oversold_detection', {})
            drop_pct = oversold_data.get('drop_pct', 0)
            rsi = oversold_data.get('rsi', 50)

            # Get recovery data
            recovery_data = signals.get('panic_recovery', {})
            recovery_days = recovery_data.get('recovery_days', 0)

            # Early: Just bounced, RSI still oversold
            if rsi < 25 and recovery_days <= 1:
                return 'early'

            # Good: Recovering, RSI improving
            elif rsi < 35 and recovery_days <= 2:
                return 'good'

            # Late: Already recovered significantly
            elif rsi < 45 and recovery_days <= 3:
                return 'late'

            # Missed: Too late
            else:
                return 'missed'

        except Exception as e:
            print(f"[SurgePredictor] Entry timing Pattern B error: {e}")
            return 'unknown'

    def _detect_oversold(self, candle_data):
        """
        Detect Oversold Condition.

        Signs:
        - RSI < 30 (oversold)
        - Recent drop -10% ~ -25%
        - Not in free fall (< -30%)

        Returns: score 0-30
        """
        try:
            # Calculate RSI
            rsi = self._calculate_rsi(candle_data, period=14)

            # Calculate recent drop (last 5 days)
            prices = [float(c.get('trade_price', 0)) for c in candle_data[:6]]

            if len(prices) < 6 or prices[-1] == 0:
                return {'score': 0, 'description': 'Insufficient data'}

            oldest_price = prices[-1]
            newest_price = prices[0]
            drop_pct = ((newest_price - oldest_price) / oldest_price) * 100

            score = 0

            # Perfect: RSI 15-25, drop -15% ~ -25%
            if 15 <= rsi <= 25 and -25 <= drop_pct <= -15:
                score = 30

            # Good: RSI < 30, drop -10% ~ -25%
            elif rsi < 30 and -25 <= drop_pct <= -10:
                score = 25

            # Acceptable: RSI < 35, drop -10% ~ -20%
            elif rsi < 35 and -20 <= drop_pct <= -10:
                score = 20

            # Moderate: RSI < 40, moderate drop
            elif rsi < 40 and -15 <= drop_pct <= -5:
                score = 15

            # Free fall (too risky)
            elif drop_pct < -30:
                score = 0

            # Not oversold enough
            else:
                score = 0

            return {
                'score': score,
                'rsi': rsi,
                'drop_pct': drop_pct,
                'description': f'Oversold (RSI: {rsi:.0f}, drop: {drop_pct:.1f}%)'
            }

        except Exception as e:
            print(f"[SurgePredictor] Oversold detection error: {e}")
            return {'score': 0, 'description': 'Error'}

    def _detect_volume_reversal(self, candle_data):
        """
        Detect Volume Reversal.

        Signs:
        - Volume was decreasing during drop
        - Now starting to increase
        - Ratio 0.8x → 1.5x+ (reversal)

        Returns: score 0-35
        """
        try:
            # Current and recent volumes
            current_volume = float(candle_data[0].get('candle_acc_trade_price', 0))
            yesterday_volume = float(candle_data[1].get('candle_acc_trade_price', 0))
            avg_volume = statistics.mean([float(c.get('candle_acc_trade_price', 0)) for c in candle_data[7:21]])

            if avg_volume == 0 or yesterday_volume == 0:
                return {'score': 0, 'description': 'No volume data'}

            current_ratio = current_volume / avg_volume
            yesterday_ratio = yesterday_volume / avg_volume

            # Check if volume is increasing
            volume_increasing = current_ratio > yesterday_ratio * 1.2

            score = 0

            # Perfect: Volume reversing (0.5-1.0x → 1.5-2.5x)
            if 1.5 <= current_ratio <= 2.5 and yesterday_ratio < 1.2 and volume_increasing:
                score = 35

            # Good: Volume starting to increase
            elif 1.2 <= current_ratio <= 2.5 and volume_increasing:
                score = 30

            # Moderate: Volume stabilizing
            elif 0.8 <= current_ratio <= 1.5:
                score = 20

            # Still decreasing
            elif current_ratio < 0.8:
                score = 10

            # Already spiked (late)
            elif current_ratio > 3.0:
                score = 5

            return {
                'score': score,
                'current_ratio': current_ratio,
                'yesterday_ratio': yesterday_ratio,
                'volume_increasing': volume_increasing,
                'description': f'Volume reversal ({current_ratio:.1f}x, {"increasing" if volume_increasing else "stable"})'
            }

        except Exception as e:
            print(f"[SurgePredictor] Volume reversal error: {e}")
            return {'score': 0, 'description': 'Error'}

    def _detect_panic_recovery(self, candle_data, current_price):
        """
        Detect Panic Recovery.

        Signs:
        - Price stopped falling
        - Starting to recover (1-3 days)
        - Higher lows forming

        Returns: score 0-35
        """
        try:
            # Get recent prices
            prices = [float(c.get('trade_price', 0)) for c in candle_data[:10]]
            lows = [float(c.get('low_price', 0)) for c in candle_data[:10]]

            if len(prices) < 10:
                return {'score': 0, 'description': 'Insufficient data'}

            # Find bottom (lowest point in last 5 days)
            recent_low = min(lows[:5])
            bottom_day = lows[:5].index(recent_low)

            # Check if recovering (price above recent low)
            recovery_pct = ((current_price - recent_low) / recent_low) * 100

            # Check for higher lows (bottom formation)
            low_1 = min(lows[0:2])
            low_2 = min(lows[2:4])
            low_3 = min(lows[4:6])

            higher_lows = low_1 > low_2

            score = 0

            # Perfect: Bottomed 1-2 days ago, recovering 2-5%
            if bottom_day <= 2 and 2 <= recovery_pct <= 5 and higher_lows:
                score = 35

            # Good: Bottomed recently, recovering
            elif bottom_day <= 3 and 1 <= recovery_pct <= 8:
                score = 30

            # Moderate: Starting to recover
            elif recovery_pct > 0 and recovery_pct <= 10:
                score = 20

            # Early: Just bottomed
            elif bottom_day <= 1 and recovery_pct <= 2:
                score = 25

            # Still falling
            elif recovery_pct < 0:
                score = 0

            # Already recovered too much (late)
            elif recovery_pct > 15:
                score = 5

            return {
                'score': score,
                'recent_low': recent_low,
                'recovery_pct': recovery_pct,
                'recovery_days': bottom_day,
                'higher_lows': higher_lows,
                'description': f'Panic recovery (bottom: {bottom_day}d ago, +{recovery_pct:.1f}%)'
            }

        except Exception as e:
            print(f"[SurgePredictor] Panic recovery error: {e}")
            return {'score': 0, 'description': 'Error'}

    def get_target_prices(self, entry_price, analysis_result, settings=None):
        """
        Calculate target and stop loss prices.
        Same as V1 for compatibility.
        """
        if settings is None:
            settings = {}

        take_profit = settings.get('take_profit_percent', 10.0)
        stop_loss = settings.get('stop_loss_percent', -5.0)

        # For low-price coins (< 100), keep 2 decimal places
        target_calc = entry_price * (1 + take_profit / 100)
        stop_loss_calc = entry_price * (1 + stop_loss / 100)

        target_price = round(target_calc, 2) if entry_price < 100 else int(target_calc)
        stop_loss_price = round(stop_loss_calc, 2) if entry_price < 100 else int(stop_loss_calc)

        return {
            'target_price': target_price,
            'stop_loss_price': stop_loss_price,
            'target_percent': take_profit,
            'stop_loss_percent': stop_loss,
            'calculation_mode': 'user_settings'
        }
