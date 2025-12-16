"""
⚠️ LEGACY - Auto Trading Engine (Basic)

DEPRECATED: Use 'enhanced_auto_trading_engine.py' instead.

This is a basic auto-trading engine without full database integration.
For production systems with multi-user support and comprehensive features, please use:
- backend/services/enhanced_auto_trading_engine.py (recommended)

Auto Trading Engine Module
Provides automated trading policy execution and market analysis.
"""

import os
import json
from datetime import datetime


class AutoTradingEngine:
    """
    Auto trading policy engine for cryptocurrency trading.

    This class handles:
    - Trading policy management per coin
    - Market condition analysis (SMA, RSI)
    - Automated buy/sell signal generation
    - Backtest functionality
    - Trading execution logging
    """

    def __init__(self):
        self.policies = {
            'auto_trading_enabled': False,
            'coin_policies': {},
            'global_settings': {
                'max_position_size': 0.1,  # Maximum position size (10%)
                'risk_level': 'medium',    # Risk level: low, medium, high
                'trading_hours': '24/7',   # Trading hours
                'min_profit_rate': 0.02,   # Minimum profit rate (2%)
                'max_loss_rate': 0.05,     # Maximum loss rate (5%)
                'check_interval': 60       # Check interval (seconds)
            }
        }
        self.trading_active = False
        self.last_check_time = None
        self.trading_log = []

    def update_coin_policy(self, coin_symbol, policy_data):
        """Update trading policy for a specific coin."""
        if 'coin_policies' not in self.policies:
            self.policies['coin_policies'] = {}

        # Default policy structure
        default_policy = {
            'enabled': True,
            'buy_threshold': 0.02,      # Buy threshold (2%)
            'sell_threshold': 0.05,     # Sell threshold (5%)
            'stop_loss': 0.03,          # Stop loss (3%)
            'take_profit': 0.10,        # Take profit (10%)
            'position_size': 0.05,      # Position size (5%)
            'strategy': 'trend_following',  # Strategy: trend_following, mean_reversion, momentum
            'timeframe': '1h',          # Analysis timeframe
            'indicators': ['sma_20', 'rsi_14', 'macd']  # Indicators to use
        }

        # Merge user settings with defaults
        merged_policy = {**default_policy, **policy_data}
        self.policies['coin_policies'][coin_symbol] = merged_policy
        self.save_policies()
        print(f"[AutoTradingEngine] {coin_symbol} policy updated: {merged_policy}")

    def enable_auto_trading(self, enabled=True):
        """Enable/disable auto trading."""
        self.policies['auto_trading_enabled'] = enabled
        self.trading_active = enabled
        self.save_policies()
        status = "enabled" if enabled else "disabled"
        print(f"[AutoTradingEngine] Auto trading {status}")

    def get_policy_summary(self):
        """Get policy summary information."""
        active_policies = sum(1 for policy in self.policies['coin_policies'].values() if policy.get('enabled', False))
        return {
            "auto_trading_enabled": self.policies['auto_trading_enabled'],
            "active_policies": active_policies,
            "total_policies": len(self.policies['coin_policies']),
            "global_settings": self.policies['global_settings'],
            "last_check": self.last_check_time,
            "trading_active": self.trading_active
        }

    def analyze_market_condition(self, coin_symbol, current_price, historical_data):
        """Analyze market conditions and generate trading signals."""
        try:
            if not historical_data or len(historical_data) < 20:
                return {"signal": "hold", "reason": "Insufficient data"}

            # Analyze with recent 20 data points
            recent_data = historical_data[:20]
            prices = [float(candle['trade_price']) for candle in recent_data]

            # Calculate simple moving averages
            sma_5 = sum(prices[:5]) / 5
            sma_20 = sum(prices) / 20

            # Compare with current price
            price_vs_sma5 = (current_price - sma_5) / sma_5
            price_vs_sma20 = (current_price - sma_20) / sma_20

            # Calculate RSI (simple version)
            gains = []
            losses = []
            for i in range(1, len(prices)):
                change = prices[i-1] - prices[i]  # Reverse order
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))

            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            rs = avg_gain / avg_loss if avg_loss > 0 else 100
            rsi = 100 - (100 / (1 + rs))

            # Generate trading signal
            signal = "hold"
            reason = ""

            if price_vs_sma5 > 0.02 and price_vs_sma20 > 0.01 and rsi < 70:
                signal = "buy"
                reason = f"Uptrend (SMA5: {price_vs_sma5:.2%}, RSI: {rsi:.1f})"
            elif price_vs_sma5 < -0.02 or rsi > 80:
                signal = "sell"
                reason = f"Downtrend signal (SMA5: {price_vs_sma5:.2%}, RSI: {rsi:.1f})"
            else:
                reason = f"Neutral (SMA5: {price_vs_sma5:.2%}, RSI: {rsi:.1f})"

            return {
                "signal": signal,
                "reason": reason,
                "indicators": {
                    "sma_5": sma_5,
                    "sma_20": sma_20,
                    "rsi": rsi,
                    "price_vs_sma5": price_vs_sma5,
                    "price_vs_sma20": price_vs_sma20
                }
            }

        except Exception as e:
            print(f"[AutoTradingEngine] ERROR analyzing {coin_symbol}: {e}")
            return {"signal": "hold", "reason": f"Analysis error: {e}"}

    def execute_trading_decision(self, coin_symbol, signal, current_price, holdings_data):
        """Execute trading decision based on signal."""
        try:
            if not self.policies['auto_trading_enabled']:
                return {"executed": False, "reason": "Auto trading disabled"}

            policy = self.policies['coin_policies'].get(coin_symbol)
            if not policy or not policy.get('enabled', False):
                return {"executed": False, "reason": f"{coin_symbol} policy disabled"}

            # Check current balance
            holding = next((h for h in holdings_data if h['coin'] == coin_symbol.replace('KRW-', '')), None)
            current_balance = float(holding['balance']) if holding else 0
            current_value = current_balance * current_price

            if signal == "buy" and current_balance == 0:
                # Buy logic (in production, this would call order API)
                order_amount = policy.get('position_size', 0.05) * 100000  # 50k KRW base
                self.trading_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": "buy_signal",
                    "coin": coin_symbol,
                    "price": current_price,
                    "amount": order_amount,
                    "reason": "Auto buy signal"
                })
                return {"executed": True, "action": "buy", "amount": order_amount}

            elif signal == "sell" and current_balance > 0:
                # Sell logic
                self.trading_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": "sell_signal",
                    "coin": coin_symbol,
                    "price": current_price,
                    "amount": current_balance,
                    "reason": "Auto sell signal"
                })
                return {"executed": True, "action": "sell", "amount": current_balance}

            return {"executed": False, "reason": "Conditions not met"}

        except Exception as e:
            print(f"[AutoTradingEngine] ERROR executing trade for {coin_symbol}: {e}")
            return {"executed": False, "reason": f"Execution error: {e}"}

    def run_auto_trading_cycle(self, upbit_api, holdings_getter):
        """
        Run auto trading cycle.

        Args:
            upbit_api: UpbitAPI instance for market data
            holdings_getter: Function to get current holdings data
        """
        if not self.policies['auto_trading_enabled']:
            return

        try:
            print("[AutoTradingEngine] Starting auto trading cycle...")
            self.last_check_time = datetime.now().isoformat()

            # Get holdings data
            holdings_data = holdings_getter()
            if not holdings_data:
                print("[AutoTradingEngine] ERROR: No holdings data")
                return

            # Process only coins with active policies
            active_coins = [coin for coin, policy in self.policies['coin_policies'].items()
                          if policy.get('enabled', False)]

            for coin_symbol in active_coins:
                try:
                    # Get current price
                    current_price = upbit_api.get_current_price(coin_symbol)
                    if not current_price:
                        continue

                    # Get chart data (recent 20 candles)
                    chart_data = upbit_api.get_candles_days(coin_symbol, count=20)
                    if not chart_data:
                        continue

                    # Analyze market
                    analysis = self.analyze_market_condition(coin_symbol, current_price, chart_data)
                    print(f"[AutoTradingEngine] ANALYSIS {coin_symbol}: {analysis['signal']} - {analysis['reason']}")

                    # Execute trading decision
                    if analysis['signal'] in ['buy', 'sell']:
                        result = self.execute_trading_decision(coin_symbol, analysis['signal'], current_price, holdings_data)
                        if result['executed']:
                            print(f"[AutoTradingEngine] EXECUTE {coin_symbol} {result['action']} signal: {result['amount']}")
                        else:
                            print(f"[AutoTradingEngine] SKIP {coin_symbol} {result['reason']}")

                except Exception as e:
                    print(f"[AutoTradingEngine] ERROR processing {coin_symbol}: {e}")
                    continue

            print("[AutoTradingEngine] Auto trading cycle completed")

        except Exception as e:
            print(f"[AutoTradingEngine] ERROR in auto trading cycle: {e}")

    def save_policies(self):
        """Save policies to file."""
        try:
            with open('trading_policies.json', 'w', encoding='utf-8') as f:
                json.dump(self.policies, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[AutoTradingEngine] ERROR saving policies: {e}")

    def load_policies(self):
        """Load policies from file."""
        try:
            if os.path.exists('trading_policies.json'):
                with open('trading_policies.json', 'r', encoding='utf-8') as f:
                    self.policies = json.load(f)
                print("[AutoTradingEngine] Policies loaded successfully")
        except Exception as e:
            print(f"[AutoTradingEngine] ERROR loading policies: {e}")

    def backtest_policy(self, coin_symbol, historical_data):
        """Backtest trading policy."""
        try:
            if not historical_data or len(historical_data) < 100:
                return {"status": "error", "message": "Insufficient data"}

            policy = self.policies['coin_policies'].get(coin_symbol, {})
            if not policy:
                return {"status": "error", "message": "No policy found"}

            # Simple backtest logic
            buy_signals = 0
            sell_signals = 0

            for i in range(20, len(historical_data)):
                current_price = float(historical_data[i]['trade_price'])
                analysis = self.analyze_market_condition(coin_symbol, current_price, historical_data[i-20:i])

                if analysis['signal'] == 'buy':
                    buy_signals += 1
                elif analysis['signal'] == 'sell':
                    sell_signals += 1

            return {
                "status": "success",
                "coin": coin_symbol,
                "period": f"{len(historical_data)} days",
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "total_signals": buy_signals + sell_signals
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}
