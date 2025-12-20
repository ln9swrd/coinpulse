# -*- coding: utf-8 -*-
"""
Market Filter Service
거래량 상위 코인 필터링 및 투자유의 종목 제외
"""

from backend.common import UpbitAPI
import time


class MarketFilter:
    """업비트 마켓 필터링 서비스"""

    def __init__(self):
        self.upbit_api = UpbitAPI(None, None)  # Public API only

    def get_top_coins_by_volume(self, count=50, exclude_caution=True):
        """
        거래량 상위 N개 코인 조회

        Args:
            count (int): 조회할 코인 개수 (기본: 50)
            exclude_caution (bool): 투자유의 종목 제외 여부

        Returns:
            list: 마켓 코드 리스트 (예: ['KRW-BTC', 'KRW-ETH', ...])
        """
        try:
            # 1. 전체 KRW 마켓 조회
            all_markets = self.upbit_api.get_markets()
            if not all_markets:
                print("[MarketFilter] Failed to fetch markets")
                return []

            # 2. KRW 마켓만 필터링
            krw_markets = [
                m for m in all_markets
                if m.get('market', '').startswith('KRW-')
            ]

            print(f"[MarketFilter] Total KRW markets: {len(krw_markets)}")

            # 3. 투자유의 종목 제외
            if exclude_caution:
                caution_markets = self.get_caution_markets(all_markets)
                krw_markets = [
                    m for m in krw_markets
                    if m['market'] not in caution_markets
                ]
                print(f"[MarketFilter] After excluding caution: {len(krw_markets)}")

            # 4. 24시간 거래대금으로 정렬
            market_codes = [m['market'] for m in krw_markets]

            # Ticker 조회 (25개씩 나눠서 요청)
            all_tickers = []
            batch_size = 25

            for i in range(0, len(market_codes), batch_size):
                batch = market_codes[i:i+batch_size]
                tickers = self.upbit_api.get_current_prices(markets=batch)
                if tickers:
                    all_tickers.extend(tickers.values())  # Convert dict to list
                time.sleep(0.1)  # Rate limit

            # 5. 거래대금 기준 정렬 (내림차순)
            all_tickers.sort(
                key=lambda x: float(x.get('acc_trade_price_24h', 0)),
                reverse=True
            )

            # 6. 상위 N개 반환
            top_coins = [t['market'] for t in all_tickers[:count]]

            print(f"[MarketFilter] Top {count} coins by volume:")
            for i, coin in enumerate(top_coins[:10], 1):
                ticker = next(t for t in all_tickers if t['market'] == coin)
                volume = ticker.get('acc_trade_price_24h', 0)
                print(f"  {i}. {coin}: KRW {volume:,.0f}")

            return top_coins

        except Exception as e:
            print(f"[MarketFilter] Error: {e}")
            return []

    def get_caution_markets(self, markets=None):
        """
        투자유의 종목 조회

        Args:
            markets (list): 전체 마켓 리스트 (없으면 새로 조회)

        Returns:
            list: 투자유의 종목 마켓 코드 리스트
        """
        try:
            if markets is None:
                markets = self.upbit_api.get_markets()

            if not markets:
                return []

            # market_warning: "CAUTION" 필터링
            caution = [
                m['market'] for m in markets
                if m.get('market_warning') == 'CAUTION'
            ]

            if caution:
                print(f"[MarketFilter] [CAUTION] Excluding {len(caution)} markets:")
                for coin in caution:
                    print(f"  - {coin}")
            else:
                print(f"[MarketFilter] [OK] No caution markets")

            return caution

        except Exception as e:
            print(f"[MarketFilter] Error getting caution markets: {e}")
            return []

    def get_market_info(self, market_code):
        """
        특정 마켓의 상세 정보 조회

        Args:
            market_code (str): 마켓 코드 (예: 'KRW-BTC')

        Returns:
            dict: 마켓 정보
        """
        try:
            all_markets = self.upbit_api.get_markets()
            market_info = next(
                (m for m in all_markets if m['market'] == market_code),
                None
            )

            if market_info:
                ticker = self.upbit_api.get_current_prices(markets=[market_code])
                if ticker:
                    market_info['ticker'] = ticker[0]

            return market_info

        except Exception as e:
            print(f"[MarketFilter] Error getting market info: {e}")
            return None

    def is_caution_market(self, market_code):
        """
        특정 마켓이 투자유의 종목인지 확인

        Args:
            market_code (str): 마켓 코드

        Returns:
            bool: 투자유의 여부
        """
        try:
            caution_markets = self.get_caution_markets()
            return market_code in caution_markets
        except:
            return False


# Test function
if __name__ == "__main__":
    print("=" * 60)
    print("Market Filter Service Test")
    print("=" * 60)

    filter_service = MarketFilter()

    # Test 1: 거래량 상위 50개 조회
    print("\n[Test 1] Top 50 coins by volume:")
    top_50 = filter_service.get_top_coins_by_volume(count=50)
    print(f"Result: {len(top_50)} coins")

    # Test 2: 투자유의 종목 조회
    print("\n[Test 2] Caution markets:")
    caution = filter_service.get_caution_markets()
    print(f"Result: {len(caution)} caution markets")

    # Test 3: 특정 코인 정보
    if top_50:
        print(f"\n[Test 3] Market info for {top_50[0]}:")
        info = filter_service.get_market_info(top_50[0])
        if info:
            print(f"  Korean name: {info.get('korean_name')}")
            print(f"  English name: {info.get('english_name')}")
            print(f"  Warning: {info.get('market_warning', 'NONE')}")
