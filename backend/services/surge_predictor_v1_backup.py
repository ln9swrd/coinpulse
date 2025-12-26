"""
Surge Predictor Module

Predicts coins likely to surge in price within 3 days.
Uses technical analysis to identify high-probability candidates.
"""

import statistics


class SurgePredictor:
    """
    Predicts price surge probability for coins.

    Analysis factors:
    - Volume increase (거래량 급증)
    - RSI oversold recovery (과매도에서 회복)
    - Support level proximity (지지선 근처)
    - Uptrend confirmation (상승 추세)
    - Price momentum (가격 모멘텀)
    """

    def __init__(self, config):
        self.config = config
        self.surge_config = config.get('surge_prediction', {})

    def analyze_coin(self, coin_symbol, candle_data, current_price):
        """
        Analyze coin for surge probability.

        Args:
            coin_symbol: Coin symbol
            candle_data: Historical candle data (list of dicts)
            current_price: Current market price

        Returns:
            {
                'coin': coin_symbol,
                'score': int (0-100),
                'signals': dict,
                'recommendation': str
            }
        """
        try:
            if not candle_data or len(candle_data) < 20:
                return {
                    'coin': coin_symbol,
                    'score': 0,
                    'signals': {},
                    'recommendation': 'insufficient_data'
                }

            # Calculate all signals
            signals = {}

            # 1. Volume Analysis (거래량 분석)
            signals['volume'] = self._analyze_volume(candle_data)

            # 2. RSI Analysis (RSI 분석)
            signals['rsi'] = self._analyze_rsi(candle_data)

            # 3. Support Level (지지선 분석)
            signals['support'] = self._analyze_support(candle_data, current_price)

            # 4. Trend Analysis (추세 분석)
            signals['trend'] = self._analyze_trend(candle_data)

            # 5. Price Momentum (가격 모멘텀)
            signals['momentum'] = self._analyze_momentum(candle_data)

            # Calculate total score (0-100)
            base_score = self._calculate_score(signals)

            # Apply risk adjustments (penalties for high-risk entries)
            penalties = self._calculate_risk_penalties(candle_data, current_price, signals)
            total_score = max(0, base_score - penalties)

            # Generate recommendation
            min_score = self.surge_config.get('min_surge_probability_score', 70)
            if total_score >= min_score:
                recommendation = 'strong_buy'
            elif total_score >= 50:
                recommendation = 'buy'
            elif total_score >= 40:
                recommendation = 'hold'
            else:
                recommendation = 'pass'

            return {
                'coin': coin_symbol,
                'score': total_score,
                'signals': signals,
                'recommendation': recommendation,
                'current_price': current_price
            }

        except Exception as e:
            print(f"[SurgePredictor] ERROR analyzing {coin_symbol}: {e}")
            return {
                'coin': coin_symbol,
                'score': 0,
                'signals': {},
                'recommendation': 'error'
            }

    def _analyze_volume(self, candle_data):
        """
        Analyze volume increase.

        Returns score 0-20 based on volume surge.
        """
        try:
            # Get recent 5 days and previous 15 days
            recent_volumes = [float(c.get('candle_acc_trade_price', 0)) for c in candle_data[:5]]
            previous_volumes = [float(c.get('candle_acc_trade_price', 0)) for c in candle_data[5:20]]

            if not recent_volumes or not previous_volumes:
                return {'score': 0, 'description': 'No volume data'}

            recent_avg = sum(recent_volumes) / len(recent_volumes)
            previous_avg = sum(previous_volumes) / len(previous_volumes)

            if previous_avg == 0:
                return {'score': 0, 'description': 'No previous volume'}

            # Calculate volume increase ratio
            volume_ratio = recent_avg / previous_avg
            threshold = self.surge_config.get('volume_increase_threshold', 1.5)

            # Score based on volume increase
            if volume_ratio >= threshold * 2:  # 3배 이상
                score = 20
                description = f"Volume surge 3x ({volume_ratio:.1f}x)"
            elif volume_ratio >= threshold * 1.5:  # 2.25배
                score = 15
                description = f"Strong volume increase ({volume_ratio:.1f}x)"
            elif volume_ratio >= threshold:  # 1.5배
                score = 10
                description = f"Volume increase ({volume_ratio:.1f}x)"
            elif volume_ratio >= 1.2:
                score = 5
                description = f"Slight volume increase ({volume_ratio:.1f}x)"
            else:
                score = 0
                description = f"No volume surge ({volume_ratio:.1f}x)"

            return {
                'score': score,
                'volume_ratio': volume_ratio,
                'description': description
            }

        except Exception as e:
            print(f"[SurgePredictor] Volume analysis error: {e}")
            return {'score': 0, 'description': 'Error'}

    def _analyze_rsi(self, candle_data):
        """
        Analyze RSI for oversold recovery.

        Returns score 0-25 based on RSI position.
        """
        try:
            # Calculate RSI
            prices = [float(c.get('trade_price', 0)) for c in candle_data[:14]]

            if len(prices) < 14:
                return {'score': 0, 'rsi': None, 'description': 'Insufficient data'}

            # Simple RSI calculation
            gains = []
            losses = []
            for i in range(1, len(prices)):
                change = prices[i-1] - prices[i]  # Reverse order (newest first)
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))

            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0

            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            # Get thresholds
            oversold_level = self.surge_config.get('rsi_oversold_level', 35)
            buy_zone_max = self.surge_config.get('rsi_buy_zone_max', 50)

            # Score based on RSI
            if oversold_level <= rsi <= buy_zone_max:
                # Perfect buy zone (35-50)
                score = 25
                description = f"RSI in buy zone ({rsi:.1f})"
            elif 30 <= rsi < oversold_level:
                # Oversold (30-35)
                score = 20
                description = f"RSI oversold ({rsi:.1f})"
            elif buy_zone_max < rsi <= 60:
                # Slightly above buy zone
                score = 15
                description = f"RSI moderate ({rsi:.1f})"
            elif rsi < 30:
                # Very oversold (risky)
                score = 10
                description = f"RSI very oversold ({rsi:.1f})"
            else:
                # Overbought or neutral
                score = 0
                description = f"RSI not favorable ({rsi:.1f})"

            return {
                'score': score,
                'rsi': rsi,
                'description': description
            }

        except Exception as e:
            print(f"[SurgePredictor] RSI analysis error: {e}")
            return {'score': 0, 'rsi': None, 'description': 'Error'}

    def _analyze_support(self, candle_data, current_price):
        """
        Analyze proximity to support level.

        Returns score 0-20 based on support proximity.
        """
        try:
            # Get recent lows (last 20 days)
            lows = [float(c.get('low_price', 0)) for c in candle_data[:20]]

            if not lows or current_price == 0:
                return {'score': 0, 'description': 'No price data'}

            # Find support level (recent low)
            support_level = min(lows)

            # Calculate distance from support
            distance_percent = ((current_price - support_level) / support_level) * 100

            # Get proximity threshold
            proximity_threshold = self.surge_config.get('support_level_proximity', 0.02) * 100  # 2%

            # Score based on proximity to support
            if distance_percent <= proximity_threshold:
                score = 20
                description = f"At support level ({distance_percent:.1f}% above)"
            elif distance_percent <= proximity_threshold * 2:
                score = 15
                description = f"Near support ({distance_percent:.1f}% above)"
            elif distance_percent <= proximity_threshold * 3:
                score = 10
                description = f"Close to support ({distance_percent:.1f}% above)"
            elif distance_percent <= proximity_threshold * 5:
                score = 5
                description = f"Moderate distance ({distance_percent:.1f}% above)"
            else:
                score = 0
                description = f"Far from support ({distance_percent:.1f}% above)"

            return {
                'score': score,
                'support_level': support_level,
                'distance_percent': distance_percent,
                'description': description
            }

        except Exception as e:
            print(f"[SurgePredictor] Support analysis error: {e}")
            return {'score': 0, 'description': 'Error'}

    def _analyze_trend(self, candle_data):
        """
        Analyze price trend.

        Returns score 0-20 based on uptrend strength.
        """
        try:
            # Get prices for last 7 days
            prices = [float(c.get('trade_price', 0)) for c in candle_data[:7]]

            if len(prices) < 7:
                return {'score': 0, 'description': 'Insufficient data'}

            # Calculate simple moving averages
            sma_3 = sum(prices[:3]) / 3
            sma_7 = sum(prices) / 7

            # Check trend direction
            uptrend_days = self.surge_config.get('uptrend_confirmation_days', 3)

            # Count consecutive up days
            up_days = 0
            for i in range(1, min(uptrend_days + 1, len(prices))):
                if prices[i-1] > prices[i]:  # Newer > Older (reverse order)
                    up_days += 1
                else:
                    break

            # Score based on trend
            if sma_3 > sma_7 * 1.02 and up_days >= 2:
                score = 20
                description = f"Strong uptrend ({up_days} days)"
            elif sma_3 > sma_7 and up_days >= 1:
                score = 15
                description = f"Uptrend ({up_days} days)"
            elif sma_3 > sma_7:
                score = 10
                description = "Slight uptrend"
            elif up_days >= 1:
                score = 5
                description = f"Recent bounce ({up_days} days)"
            else:
                score = 0
                description = "No uptrend"

            return {
                'score': score,
                'sma_3': sma_3,
                'sma_7': sma_7,
                'up_days': up_days,
                'description': description
            }

        except Exception as e:
            print(f"[SurgePredictor] Trend analysis error: {e}")
            return {'score': 0, 'description': 'Error'}

    def _analyze_momentum(self, candle_data):
        """
        Analyze price momentum.

        Returns score 0-15 based on momentum strength.
        """
        try:
            # Get prices for last 5 days
            prices = [float(c.get('trade_price', 0)) for c in candle_data[:5]]

            if len(prices) < 5:
                return {'score': 0, 'description': 'Insufficient data'}

            # Calculate momentum (price change rate)
            oldest_price = prices[-1]
            newest_price = prices[0]

            if oldest_price == 0:
                return {'score': 0, 'description': 'Invalid price'}

            momentum_percent = ((newest_price - oldest_price) / oldest_price) * 100

            # Score based on positive momentum
            if momentum_percent >= 10:
                score = 15
                description = f"Very strong momentum (+{momentum_percent:.1f}%)"
            elif momentum_percent >= 5:
                score = 12
                description = f"Strong momentum (+{momentum_percent:.1f}%)"
            elif momentum_percent >= 2:
                score = 8
                description = f"Positive momentum (+{momentum_percent:.1f}%)"
            elif momentum_percent >= 0:
                score = 4
                description = f"Slight positive ({momentum_percent:.1f}%)"
            else:
                score = 0
                description = f"Negative momentum ({momentum_percent:.1f}%)"

            return {
                'score': score,
                'momentum_percent': momentum_percent,
                'description': description
            }

        except Exception as e:
            print(f"[SurgePredictor] Momentum analysis error: {e}")
            return {'score': 0, 'description': 'Error'}

    def _calculate_score(self, signals):
        """
        Calculate total surge probability score (0-100).

        Weights:
        - Volume: 20 points
        - RSI: 25 points
        - Support: 20 points
        - Trend: 20 points
        - Momentum: 15 points
        Total: 100 points
        """
        total = 0
        total += signals.get('volume', {}).get('score', 0)
        total += signals.get('rsi', {}).get('score', 0)
        total += signals.get('support', {}).get('score', 0)
        total += signals.get('trend', {}).get('score', 0)
        total += signals.get('momentum', {}).get('score', 0)

        return min(100, max(0, total))  # Clamp to 0-100

    def _calculate_risk_penalties(self, candle_data, current_price, signals):
        """
        Calculate risk penalties to prevent high-point entry (고점 진입 방지).

        Penalties:
        1. High Entry Penalty: 최근 고점 근처 진입 (-20점)
        2. Overheating Penalty: 단기 급등 후 진입 (-15점)
        3. RSI Overbought Penalty: RSI > 60 (-10점)
        4. Excessive Momentum Penalty: 5일간 10% 이상 상승 (-10점)

        Returns:
            int: Total penalty points (0-55)
        """
        penalty = 0

        try:
            # 1. High Entry Penalty (최근 30일 고점 대비 현재 가격 위치)
            highs_30d = [float(c.get('high_price', 0)) for c in candle_data[:30]]
            if highs_30d and current_price > 0:
                recent_high = max(highs_30d)
                price_position = (current_price / recent_high) * 100

                if price_position >= 95:
                    penalty += 25  # 고점 95% 이상: 매우 위험
                elif price_position >= 90:
                    penalty += 20  # 고점 90% 이상: 위험
                elif price_position >= 85:
                    penalty += 15  # 고점 85% 이상: 주의
                elif price_position >= 80:
                    penalty += 10  # 고점 80% 이상: 경계

            # 2. Overheating Penalty (최근 7일 vs 이전 7일 급등 감지)
            if len(candle_data) >= 14:
                recent_7d_avg = statistics.mean([float(c.get('trade_price', 0)) for c in candle_data[:7]])
                previous_7d_avg = statistics.mean([float(c.get('trade_price', 0)) for c in candle_data[7:14]])

                if previous_7d_avg > 0:
                    weekly_surge = ((recent_7d_avg - previous_7d_avg) / previous_7d_avg) * 100

                    if weekly_surge >= 30:
                        penalty += 20  # 1주일간 30% 이상 상승: 과열
                    elif weekly_surge >= 20:
                        penalty += 15  # 1주일간 20% 이상 상승: 과열 위험
                    elif weekly_surge >= 15:
                        penalty += 10  # 1주일간 15% 이상 상승: 주의

            # 3. RSI Overbought Penalty (RSI > 60)
            rsi = signals.get('rsi', {}).get('rsi')
            if rsi:
                if rsi >= 70:
                    penalty += 15  # RSI 70 이상: 과매수
                elif rsi >= 65:
                    penalty += 10  # RSI 65 이상: 과매수 위험
                elif rsi >= 60:
                    penalty += 5   # RSI 60 이상: 주의

            # 4. Excessive Momentum Penalty (5일간 10% 이상 상승)
            momentum_pct = signals.get('momentum', {}).get('momentum_percent', 0)
            if momentum_pct >= 15:
                penalty += 15  # 5일간 15% 이상 상승: 이미 충분히 올랐음
            elif momentum_pct >= 10:
                penalty += 10  # 5일간 10% 이상 상승: 주의

        except Exception as e:
            print(f"[SurgePredictor] Risk penalty calculation error: {e}")

        return penalty

    def calculate_dynamic_target(self, analysis_result, min_target=3.0, max_target=10.0):
        """
        Calculate dynamic target price percentage based on signal strength.

        Args:
            analysis_result: Result from analyze_coin() containing score and signals
            min_target: Minimum target percentage (default: 3.0%)
            max_target: Maximum target percentage (default: 10.0%)

        Returns:
            float: Target percentage (e.g., 7.5 for 7.5%)

        Algorithm (Adjusted for realistic 3-day holding):
            Base target: 3%
            + Confidence bonus: 0-2% (based on score/100)
            + Momentum bonus: 0-3% (based on momentum_percent)
            + Volume bonus: 0-1% (based on volume_ratio)
            + Trend bonus: 0-1% (based on trend strength)
            = Total target: 3-10%
        """
        try:
            score = analysis_result.get('score', 0)
            signals = analysis_result.get('signals', {})

            # Base target (minimum viable target for 3-day holding)
            base_target = 3.0

            # 1. Confidence/Score Bonus (0-2%)
            # Score 60-100 → 0-2% bonus
            score_normalized = max(0, min(100, score))
            confidence_bonus = ((score_normalized - 60) / 40) * 2.0
            confidence_bonus = max(0, min(2, confidence_bonus))

            # 2. Momentum Bonus (0-3%)
            # Momentum 0-25% → 0-3% bonus
            momentum_data = signals.get('momentum', {})
            momentum_percent = abs(momentum_data.get('momentum_percent', 0))
            momentum_bonus = (momentum_percent / 25) * 3.0
            momentum_bonus = max(0, min(3, momentum_bonus))

            # 3. Volume Bonus (0-1%)
            # Volume ratio 1-8x → 0-1% bonus
            volume_data = signals.get('volume', {})
            volume_ratio = volume_data.get('volume_ratio', 1.0)
            volume_bonus = ((volume_ratio - 1) / 7) * 1.0
            volume_bonus = max(0, min(1, volume_bonus))

            # 4. Trend Bonus (0-1%)
            # Trend score 0-20 → 0-1% bonus
            trend_data = signals.get('trend', {})
            trend_score = trend_data.get('score', 0)
            trend_bonus = (trend_score / 20) * 1.0
            trend_bonus = max(0, min(1, trend_bonus))

            # Calculate total target
            target_percent = base_target + confidence_bonus + momentum_bonus + volume_bonus + trend_bonus

            # Clamp to user-defined min/max range
            target_percent = max(min_target, min(max_target, target_percent))

            return round(target_percent, 2)

        except Exception as e:
            print(f"[SurgePredictor] ERROR calculating dynamic target: {e}")
            return min_target  # Return safe minimum on error

    def calculate_dynamic_stop_loss(self, target_percent, risk_ratio=0.5):
        """
        Calculate stop loss percentage based on target percentage.

        Args:
            target_percent: Target profit percentage
            risk_ratio: Risk/reward ratio (default: 0.5 = 1:2 reward/risk)

        Returns:
            float: Stop loss percentage (negative value, e.g., -6.0 for -6%)

        Example:
            Target: 12% → Stop loss: -6% (1:2 ratio)
            Target: 8% → Stop loss: -4% (1:2 ratio)
        """
        stop_loss = -(target_percent * risk_ratio)
        return round(stop_loss, 2)

    def get_target_prices(self, entry_price, analysis_result, settings=None):
        """
        Calculate target and stop loss prices based on settings.

        Args:
            entry_price: Entry price in KRW
            analysis_result: Analysis result from analyze_coin()
            settings: User settings dict with:
                - use_dynamic_target: bool
                - target_calculation_mode: 'fixed'/'dynamic'/'hybrid'
                - min_target_percent: float
                - max_target_percent: float
                - take_profit_percent: float (for fixed/hybrid)
                - stop_loss_percent: float

        Returns:
            dict: {
                'target_price': int,
                'stop_loss_price': int,
                'target_percent': float,
                'stop_loss_percent': float,
                'calculation_mode': str
            }
        """
        try:
            # Default settings
            if not settings:
                settings = {
                    'use_dynamic_target': True,
                    'target_calculation_mode': 'dynamic',
                    'min_target_percent': 5.0,
                    'max_target_percent': 18.0,
                    'take_profit_percent': 10.0,
                    'stop_loss_percent': -5.0
                }

            use_dynamic = settings.get('use_dynamic_target', True)
            mode = settings.get('target_calculation_mode', 'dynamic')
            min_target = settings.get('min_target_percent', 5.0)
            max_target = settings.get('max_target_percent', 18.0)
            fixed_target = settings.get('take_profit_percent', 10.0)
            fixed_stop = settings.get('stop_loss_percent', -5.0)

            # Calculate target percentage based on mode
            if not use_dynamic or mode == 'fixed':
                # Fixed mode: Use user-defined percentage
                target_percent = fixed_target
                calculation_mode = 'fixed'

            elif mode == 'hybrid':
                # Hybrid mode: Start from fixed value, adjust by signal strength
                dynamic_target = self.calculate_dynamic_target(analysis_result, min_target, max_target)
                # Adjust fixed target by signal strength (weighted average)
                target_percent = (fixed_target + dynamic_target) / 2
                target_percent = max(min_target, min(max_target, target_percent))
                calculation_mode = 'hybrid'

            else:  # mode == 'dynamic'
                # Dynamic mode: Calculate based on signal strength
                target_percent = self.calculate_dynamic_target(analysis_result, min_target, max_target)
                calculation_mode = 'dynamic'

            # Calculate stop loss (proportional to target)
            if mode == 'fixed':
                stop_loss_percent = fixed_stop
            else:
                # Dynamic stop loss: 50% of target (1:2 risk/reward)
                stop_loss_percent = self.calculate_dynamic_stop_loss(target_percent, risk_ratio=0.5)

            # Calculate actual prices
            target_price = int(entry_price * (1 + target_percent / 100))
            stop_loss_price = int(entry_price * (1 + stop_loss_percent / 100))

            return {
                'target_price': target_price,
                'stop_loss_price': stop_loss_price,
                'target_percent': round(target_percent, 2),
                'stop_loss_percent': round(stop_loss_percent, 2),
                'calculation_mode': calculation_mode,
                'signal_score': analysis_result.get('score', 0)
            }

        except Exception as e:
            print(f"[SurgePredictor] ERROR calculating target prices: {e}")
            # Return safe defaults
            return {
                'target_price': int(entry_price * 1.05),
                'stop_loss_price': int(entry_price * 0.95),
                'target_percent': 5.0,
                'stop_loss_percent': -5.0,
                'calculation_mode': 'fixed',
                'signal_score': 0
            }

    def find_surge_candidates(self, upbit_api, excluded_coins=None):
        """
        Find top surge candidates from all available coins.

        Args:
            upbit_api: UpbitAPI instance
            excluded_coins: List of coins to exclude

        Returns:
            List of candidates sorted by score (highest first)
        """
        try:
            print("[SurgePredictor] Scanning for surge candidates...")

            # Get all KRW markets
            markets = upbit_api.get_markets()
            krw_markets = [m for m in markets if m['market'].startswith('KRW-')]

            # Filter excluded coins
            if excluded_coins:
                krw_markets = [m for m in krw_markets if m['market'] not in excluded_coins]

            # Analyze each coin
            candidates = []

            for market in krw_markets:
                coin_symbol = market['market']

                try:
                    # Get current price
                    current_price = upbit_api.get_current_price(coin_symbol)
                    if not current_price:
                        continue

                    # Get candle data (30 days for analysis)
                    candle_data = upbit_api.get_candles_days(coin_symbol, count=30)
                    if not candle_data:
                        continue

                    # Analyze coin
                    analysis = self.analyze_coin(coin_symbol, candle_data, current_price)

                    # Only include coins with minimum score
                    min_score = self.surge_config.get('min_surge_probability_score', 70)
                    if analysis['score'] >= min_score:
                        candidates.append(analysis)
                        print(f"[SurgePredictor] ✅ {coin_symbol}: Score {analysis['score']} - {analysis['recommendation']}")

                except Exception as e:
                    print(f"[SurgePredictor] Error analyzing {coin_symbol}: {e}")
                    continue

            # Sort by score (highest first)
            candidates.sort(key=lambda x: x['score'], reverse=True)

            print(f"[SurgePredictor] Found {len(candidates)} candidates")

            return candidates

        except Exception as e:
            print(f"[SurgePredictor] ERROR finding candidates: {e}")
            return []
