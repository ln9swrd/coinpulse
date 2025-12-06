"""
Chart Service Module

Provides chart data retrieval functionality from Upbit API.
"""

import requests
import time
import urllib.parse


class ChartService:
    """
    Service class for retrieving chart data from Upbit API.

    This class handles:
    - Candle data retrieval (minutes, days, weeks, months)
    - Retry logic with exponential backoff
    - Rate limit handling
    - Request timeout management
    """

    def __init__(self, config=None):
        """
        Initialize ChartService with configuration.

        Args:
            config (dict): Configuration dictionary containing:
                - api.upbit_base_url: Base URL for Upbit API
                - api.request_timeout: Timeout for API requests
                - api.max_retries: Maximum number of retry attempts
        """
        self.config = config or {}
        self.base_url = self.config.get('api', {}).get('upbit_base_url', 'https://api.upbit.com')
        self.request_timeout = self.config.get('api', {}).get('request_timeout', 5)
        self.max_retries = self.config.get('api', {}).get('max_retries', 3)

    def get_candles(self, timeframe, market, count=200, unit=None, to=None):
        """
        Retrieve candle data from Upbit API.

        Args:
            timeframe (str): Timeframe for candles ('minutes', 'days', 'weeks', 'months')
            market (str): Market symbol (e.g., 'KRW-BTC')
            count (int): Number of candles to retrieve (max 200)
            unit (int): Unit for minute candles (1, 3, 5, 10, 15, 30, 60, 240)
            to (str): End datetime for candles (ISO format or 'YYYY-MM-DD HH:MM:SS')

        Returns:
            list: List of candle data dictionaries, or None if error
        """
        max_retries = self.max_retries
        base_timeout = self.request_timeout

        for attempt in range(max_retries):
            try:
                # API path setup
                if timeframe == 'minutes':
                    if unit is None:
                        unit = 1
                    url = f"{self.base_url}/v1/candles/minutes/{unit}"
                elif timeframe == 'days':
                    url = f"{self.base_url}/v1/candles/days"
                elif timeframe == 'weeks':
                    url = f"{self.base_url}/v1/candles/weeks"
                elif timeframe == 'months':
                    url = f"{self.base_url}/v1/candles/months"
                else:
                    print(f"[ChartService] ERROR: Invalid timeframe: {timeframe}")
                    return None

                # Parameters
                params = {
                    'market': market,
                    'count': min(count, 200)
                }

                # Handle 'to' parameter for historical data
                if to:
                    # Decode URL-encoded parameter
                    to_param = urllib.parse.unquote(str(to).strip())

                    # Convert ISO format to Upbit API format
                    if 'T' in to_param:
                        to_param = to_param.replace('T', ' ')
                    if to_param.endswith('Z'):
                        to_param = to_param.replace('Z', '')

                    params['to'] = to_param
                    print(f"[ChartService] TO parameter: {to_param}")

                print(f"[ChartService] API CALL: {url} with params: {params}, timeout: {base_timeout}s, attempt: {attempt + 1}")

                # API call with session and timeout
                session = requests.Session()
                session.headers.update({'User-Agent': 'CoinPulse/1.0'})
                response = session.get(url, params=params, timeout=base_timeout)

                if response.status_code == 200:
                    data = response.json()
                    print(f"[ChartService] SUCCESS: {timeframe} data for {market}, count={len(data)}")
                    return data
                elif response.status_code == 429:  # Too Many Requests
                    print(f"[ChartService] RATE LIMIT: attempt {attempt + 1}, waiting...")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return None
                else:
                    print(f"[ChartService] ERROR: API error {response.status_code}, attempt {attempt + 1}")
                    print(f"[ChartService] ERROR: Response text: {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(0.5)
                        continue
                    return None

            except requests.exceptions.Timeout:
                print(f"[ChartService] TIMEOUT: attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue
                return None
            except Exception as e:
                print(f"[ChartService] ERROR: {str(e)}, attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue
                return None

        return None
