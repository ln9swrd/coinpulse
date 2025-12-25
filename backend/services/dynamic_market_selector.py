# -*- coding: utf-8 -*-
"""
Dynamic Market Selector for Surge Detection

Automatically selects top N coins to monitor based on:
- Market status (no warnings/delisting)
- Trading volume (24h trade value)
- Liquidity (active trading)

Updates the monitor list daily to adapt to market conditions.
"""

import requests
import time
from typing import List, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DynamicMarketSelector:
    """
    Dynamically select markets to monitor for surge detection
    """

    def __init__(self, target_count: int = 50):
        """
        Initialize market selector

        Args:
            target_count: Number of markets to select (default: 50)
        """
        self.target_count = target_count
        self.upbit_api_base = "https://api.upbit.com/v1"
        self.last_update = None
        self.selected_markets = []

        # Minimum thresholds
        self.min_trade_value_24h = 100_000_000  # 1억원 (100M KRW) minimum daily volume
        self.min_price = 1  # Minimum 1원

    def get_all_krw_markets(self) -> List[Dict]:
        """
        Get all KRW markets from Upbit

        Returns:
            List of market info dicts
        """
        try:
            response = requests.get(
                f"{self.upbit_api_base}/market/all",
                params={'isDetails': 'true'},
                timeout=10
            )

            if response.status_code != 200:
                logger.error(f"[MarketSelector] Failed to fetch markets: {response.status_code}")
                return []

            all_markets = response.json()

            # Filter KRW markets only
            krw_markets = [
                m for m in all_markets
                if m.get('market', '').startswith('KRW-')
            ]

            logger.info(f"[MarketSelector] Found {len(krw_markets)} KRW markets")
            return krw_markets

        except Exception as e:
            logger.error(f"[MarketSelector] Error fetching markets: {e}")
            return []

    def filter_valid_markets(self, markets: List[Dict]) -> List[Dict]:
        """
        Filter out invalid markets

        Criteria:
        - No market warning (유의지정 제외)
        - Not delisting (상장폐지 예정 제외)

        Args:
            markets: List of market dicts

        Returns:
            Filtered list of valid markets
        """
        valid_markets = []

        for market in markets:
            market_id = market.get('market', '')

            # Check market warning (유의지정)
            market_warning = market.get('market_warning')
            if market_warning and market_warning != 'NONE':
                logger.debug(f"[MarketSelector] Skipping {market_id}: warning={market_warning}")
                continue

            valid_markets.append(market)

        logger.info(f"[MarketSelector] {len(valid_markets)} valid markets (no warnings)")
        return valid_markets

    def get_market_volumes(self, market_ids: List[str]) -> Dict[str, Dict]:
        """
        Get 24h trading volumes for markets

        Args:
            market_ids: List of market IDs (e.g., ['KRW-BTC', 'KRW-ETH'])

        Returns:
            Dict mapping market_id to volume info
        """
        volume_data = {}

        # Batch request (max 100 markets per request)
        batch_size = 100
        for i in range(0, len(market_ids), batch_size):
            batch = market_ids[i:i+batch_size]
            markets_param = ','.join(batch)

            try:
                response = requests.get(
                    f"{self.upbit_api_base}/ticker",
                    params={'markets': markets_param},
                    timeout=10
                )

                if response.status_code != 200:
                    logger.warning(f"[MarketSelector] Failed to fetch volumes for batch {i//batch_size + 1}")
                    continue

                tickers = response.json()

                for ticker in tickers:
                    market_id = ticker.get('market')
                    volume_data[market_id] = {
                        'trade_price': ticker.get('trade_price', 0),
                        'acc_trade_price_24h': ticker.get('acc_trade_price_24h', 0),  # 24h trade value (KRW)
                        'acc_trade_volume_24h': ticker.get('acc_trade_volume_24h', 0),  # 24h trade volume
                        'change_rate': ticker.get('signed_change_rate', 0),
                        'timestamp': ticker.get('timestamp', 0)
                    }

                # Rate limit
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"[MarketSelector] Error fetching volumes: {e}")
                continue

        logger.info(f"[MarketSelector] Fetched volume data for {len(volume_data)} markets")
        return volume_data

    def rank_markets(self, markets: List[Dict], volume_data: Dict[str, Dict]) -> List[Dict]:
        """
        Rank markets by trading activity

        Ranking criteria (weighted):
        1. 24h trade value (KRW) - 70% weight
        2. 24h trade volume - 20% weight
        3. Price level (prefer mid-cap coins) - 10% weight

        Args:
            markets: List of market dicts
            volume_data: Volume data from get_market_volumes

        Returns:
            Sorted list of markets (best to worst)
        """
        ranked = []

        for market in markets:
            market_id = market.get('market')
            volumes = volume_data.get(market_id)

            if not volumes:
                continue

            # Get metrics
            trade_price = volumes.get('trade_price', 0)
            trade_value_24h = volumes.get('acc_trade_price_24h', 0)
            trade_volume_24h = volumes.get('acc_trade_volume_24h', 0)

            # Filter minimum requirements
            if trade_price < self.min_price:
                continue

            if trade_value_24h < self.min_trade_value_24h:
                continue

            # Calculate score
            # Primary: 24h trade value (higher = more active)
            value_score = trade_value_24h / 1_000_000_000  # Normalize to billions

            # Secondary: 24h trade volume
            volume_score = min(trade_volume_24h / 1_000_000, 100)  # Cap at 100

            # Tertiary: Price level (prefer mid-range, avoid too cheap/expensive)
            if trade_price < 100:
                price_score = 0  # Too cheap (pump risk)
            elif trade_price < 1000:
                price_score = 10  # Good range
            elif trade_price < 100_000:
                price_score = 8   # Mid range
            elif trade_price < 10_000_000:
                price_score = 5   # High price
            else:
                price_score = 2   # Very high price (BTC/ETH)

            # Weighted total score
            total_score = (value_score * 0.7) + (volume_score * 0.2) + (price_score * 0.1)

            ranked.append({
                'market': market_id,
                'coin': market_id.replace('KRW-', ''),
                'score': total_score,
                'trade_value_24h': trade_value_24h,
                'trade_volume_24h': trade_volume_24h,
                'trade_price': trade_price,
                'market_warning': market.get('market_warning', 'NONE')
            })

        # Sort by score (descending)
        ranked.sort(key=lambda x: x['score'], reverse=True)

        logger.info(f"[MarketSelector] Ranked {len(ranked)} markets")
        return ranked

    def select_top_markets(self, ranked_markets: List[Dict]) -> List[str]:
        """
        Select top N markets

        Args:
            ranked_markets: Ranked list from rank_markets

        Returns:
            List of market IDs (e.g., ['KRW-BTC', 'KRW-ETH', ...])
        """
        top_markets = ranked_markets[:self.target_count]
        market_ids = [m['market'] for m in top_markets]

        logger.info(f"[MarketSelector] Selected top {len(market_ids)} markets")

        # Log top 10 for debugging
        for i, market in enumerate(top_markets[:10], 1):
            logger.info(
                f"  {i}. {market['market']} - "
                f"Score: {market['score']:.2f}, "
                f"24h Value: {market['trade_value_24h']/1_000_000_000:.2f}B KRW"
            )

        return market_ids

    def update_market_list(self) -> List[str]:
        """
        Update the monitored market list

        Full process:
        1. Fetch all KRW markets
        2. Filter valid markets (no warnings)
        3. Get trading volumes
        4. Rank by activity
        5. Select top N

        Returns:
            List of selected market IDs
        """
        logger.info(f"[MarketSelector] Updating market list (target: {self.target_count})...")

        # Step 1: Get all KRW markets
        all_markets = self.get_all_krw_markets()
        if not all_markets:
            logger.error("[MarketSelector] No markets found")
            return self.selected_markets  # Return previous list

        # Step 2: Filter valid markets
        valid_markets = self.filter_valid_markets(all_markets)
        if not valid_markets:
            logger.error("[MarketSelector] No valid markets found")
            return self.selected_markets

        # Step 3: Get volumes
        market_ids = [m['market'] for m in valid_markets]
        volume_data = self.get_market_volumes(market_ids)
        if not volume_data:
            logger.error("[MarketSelector] No volume data found")
            return self.selected_markets

        # Step 4: Rank markets
        ranked_markets = self.rank_markets(valid_markets, volume_data)
        if not ranked_markets:
            logger.error("[MarketSelector] No markets passed ranking")
            return self.selected_markets

        # Step 5: Select top N
        selected = self.select_top_markets(ranked_markets)

        # Update state
        self.selected_markets = selected
        self.last_update = datetime.now()

        logger.info(f"[MarketSelector] Market list updated: {len(selected)} markets selected")
        return selected

    def should_update(self, update_interval_hours: int = 24) -> bool:
        """
        Check if market list needs updating

        Args:
            update_interval_hours: Hours between updates (default: 24)

        Returns:
            True if update is needed
        """
        if not self.last_update:
            return True

        elapsed = datetime.now() - self.last_update
        return elapsed > timedelta(hours=update_interval_hours)

    def get_markets(self, force_update: bool = False, update_interval_hours: int = 24) -> List[str]:
        """
        Get monitored markets (with auto-update)

        Args:
            force_update: Force update regardless of interval
            update_interval_hours: Hours between updates

        Returns:
            List of market IDs to monitor
        """
        if force_update or self.should_update(update_interval_hours):
            return self.update_market_list()

        return self.selected_markets


# Singleton instance
_market_selector = None


def get_market_selector(target_count: int = 50) -> DynamicMarketSelector:
    """
    Get or create market selector singleton

    Args:
        target_count: Number of markets to select

    Returns:
        DynamicMarketSelector instance
    """
    global _market_selector

    if _market_selector is None:
        _market_selector = DynamicMarketSelector(target_count=target_count)

    return _market_selector


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)

    selector = DynamicMarketSelector(target_count=50)
    markets = selector.update_market_list()

    print("\n" + "="*60)
    print(f"Selected {len(markets)} markets:")
    print("="*60)
    for i, market in enumerate(markets, 1):
        print(f"{i:2d}. {market}")
