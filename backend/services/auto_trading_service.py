"""
Auto Trading Service Wrapper

This module provides a simplified interface for auto-trading operations,
wrapping the EnhancedAutoTradingEngine with a user-friendly API.
"""

import logging
from typing import Dict
from backend.common import UpbitAPI, load_api_keys
from backend.services.enhanced_auto_trading_engine import EnhancedAutoTradingEngine

logger = logging.getLogger(__name__)


class AutoTradingService:
    """
    Simplified auto-trading service interface.

    This class wraps EnhancedAutoTradingEngine and provides a cleaner API
    for surge trading monitoring and other auto-trading features.
    """

    def __init__(self, user_id: int):
        """
        Initialize auto trading service for a specific user.

        Args:
            user_id: User ID for trading operations
        """
        self.user_id = user_id

        # Initialize Upbit API
        access_key, secret_key = load_api_keys()
        self.upbit_api = UpbitAPI(access_key, secret_key)

        # Initialize enhanced auto trading engine
        self.engine = EnhancedAutoTradingEngine(self.upbit_api)

        logger.info(f"[AutoTradingService] Initialized for user {user_id}")

    def execute_sell_order(self, market: str, amount: float = None, reason: str = 'auto_signal') -> Dict:
        """
        Execute a sell order with simplified interface.

        Args:
            market: Market code (e.g., 'KRW-BTC')
            amount: Amount to sell (optional, will sell entire position if not specified)
            reason: Sell reason ('take_profit', 'stop_loss', 'auto_signal')

        Returns:
            dict: Execution result with keys:
                - success (bool): Whether the order succeeded
                - executed_price (float): Actual executed price
                - error (str): Error message if failed
                - order_uuid (str): Order UUID if successful
                - quantity (float): Quantity sold
                - profit_loss (float): Profit/loss amount
        """
        try:
            # Get current price
            current_price = self.upbit_api.get_current_price(market)
            if not current_price:
                return {
                    'success': False,
                    'error': f'Failed to get current price for {market}'
                }

            # Extract coin symbol from market (KRW-BTC -> BTC)
            coin_symbol = market

            # Execute sell via enhanced engine
            result = self.engine.execute_sell_order(
                user_id=self.user_id,
                coin_symbol=coin_symbol,
                current_price=current_price,
                reason=reason
            )

            # Translate response format for surge trading monitor
            if result.get('success'):
                return {
                    'success': True,
                    'executed_price': result.get('price', current_price),  # Map 'price' to 'executed_price'
                    'order_uuid': result.get('order_uuid'),
                    'quantity': result.get('quantity'),
                    'profit_loss': result.get('profit_loss'),
                    'reason': result.get('reason')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('reason', 'Unknown error')
                }

        except Exception as e:
            logger.error(f"[AutoTradingService] execute_sell_order failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def execute_buy_order(self, market: str, amount: float, reason: str = 'auto_signal') -> Dict:
        """
        Execute a buy order.

        Args:
            market: Market code (e.g., 'KRW-BTC')
            amount: Amount in KRW to buy
            reason: Buy reason

        Returns:
            dict: Execution result
        """
        try:
            # Get current price
            current_price = self.upbit_api.get_current_price(market)
            if not current_price:
                return {
                    'success': False,
                    'error': f'Failed to get current price for {market}'
                }

            # Calculate quantity to buy
            quantity = amount / current_price

            # Place market buy order
            order_result = self.upbit_api.place_order(
                market=market,
                side='bid',
                volume=None,
                price=amount,  # For market buy, specify total KRW amount
                ord_type='price'  # Buy with specific KRW amount
            )

            if order_result and 'uuid' in order_result:
                logger.info(f"[AutoTradingService] Buy order executed: {market} {quantity:.8f} @ {current_price:,.0f} KRW")
                return {
                    'success': True,
                    'executed_price': current_price,
                    'order_uuid': order_result['uuid'],
                    'quantity': quantity,
                    'amount': amount,
                    'reason': reason
                }
            else:
                return {
                    'success': False,
                    'error': 'Order placement failed'
                }

        except Exception as e:
            logger.error(f"[AutoTradingService] execute_buy_order failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
