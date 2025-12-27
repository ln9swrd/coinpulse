"""
Balance-Coin Price Correlation Analysis

사용자 잔고 변화와 주요 코인(BTC, ETH, XRP) 가격 간의 상관관계 분석

Usage:
    python scripts/analyze_correlation.py [user_id] [days]

Examples:
    python scripts/analyze_correlation.py 1 365  # User 1, 1년치
    python scripts/analyze_correlation.py 1 0    # User 1, 전체 기간
"""

import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.connection import get_db_session
from sqlalchemy import text


def calculate_correlation_coefficient(x, y):
    """
    Calculate Pearson correlation coefficient

    Args:
        x: List of values
        y: List of values

    Returns:
        float: Correlation coefficient (-1 to 1)
    """
    if len(x) != len(y) or len(x) == 0:
        return 0

    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n)) ** 0.5
    denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n)) ** 0.5

    if denominator_x == 0 or denominator_y == 0:
        return 0

    return numerator / (denominator_x * denominator_y)


def fetch_balance_history(db, user_id, days=0):
    """
    Fetch user's balance history

    Args:
        db: Database session
        user_id: User ID
        days: Number of days (0 = all)

    Returns:
        list of dicts with keys: date, total_value, krw_total, crypto_value
    """
    query_str = """
        SELECT
            DATE(snapshot_time) as date,
            total_value,
            krw_total,
            crypto_value,
            total_profit,
            total_profit_rate
        FROM holdings_history
        WHERE user_id = :user_id
    """

    if days > 0:
        query_str += " AND snapshot_time >= :start_date"

    query_str += " ORDER BY date"

    params = {'user_id': user_id}
    if days > 0:
        params['start_date'] = datetime.now() - timedelta(days=days)

    query = text(query_str)
    result = db.execute(query, params)

    data = []
    for row in result:
        data.append({
            'date': row[0],
            'total_value': float(row[1]) if row[1] else 0,
            'krw_total': float(row[2]) if row[2] else 0,
            'crypto_value': float(row[3]) if row[3] else 0,
            'total_profit': float(row[4]) if row[4] else 0,
            'total_profit_rate': float(row[5]) if row[5] else 0
        })

    return data


def fetch_coin_prices(db, days=0):
    """
    Fetch BTC/ETH/XRP prices

    Args:
        db: Database session
        days: Number of days (0 = all)

    Returns:
        list of dicts with keys: date, btc_price, eth_price, xrp_price
    """
    query_str = """
        SELECT
            date,
            market,
            close_price
        FROM coin_price_history
        WHERE market IN ('KRW-BTC', 'KRW-ETH', 'KRW-XRP')
    """

    if days > 0:
        query_str += " AND date >= :start_date"

    query_str += " ORDER BY date"

    params = {}
    if days > 0:
        params['start_date'] = (datetime.now() - timedelta(days=days)).date()

    query = text(query_str)
    result = db.execute(query, params)

    # Pivot data: date as key, market as columns
    data = {}
    for row in result:
        date = row[0]
        market = row[1]
        price = float(row[2])

        if date not in data:
            data[date] = {}

        data[date][market] = price

    # Convert to list of dicts
    result_data = []
    for date, prices in sorted(data.items()):
        result_data.append({
            'date': date,
            'btc_price': prices.get('KRW-BTC'),
            'eth_price': prices.get('KRW-ETH'),
            'xrp_price': prices.get('KRW-XRP')
        })

    return result_data


def calculate_correlation(balance_data, price_data):
    """
    Calculate correlation between balance and coin prices

    Args:
        balance_data: List of balance history dicts
        price_data: List of coin price dicts

    Returns:
        dict: Correlation results
    """
    # Merge data on date (inner join)
    balance_by_date = {item['date']: item for item in balance_data}
    price_by_date = {item['date']: item for item in price_data}

    merged = []
    for date in balance_by_date:
        if date in price_by_date:
            item = {**balance_by_date[date], **price_by_date[date]}
            # Skip if any price is None
            if item.get('btc_price') and item.get('eth_price') and item.get('xrp_price'):
                merged.append(item)

    if len(merged) == 0:
        return None

    # Extract data for calculations
    total_values = [item['total_value'] for item in merged]
    crypto_values = [item['crypto_value'] for item in merged]
    profit_rates = [item['total_profit_rate'] for item in merged]
    btc_prices = [item['btc_price'] for item in merged]
    eth_prices = [item['eth_price'] for item in merged]
    xrp_prices = [item['xrp_price'] for item in merged]

    # Calculate statistics
    dates = [item['date'] for item in merged]
    results = {
        'period': {
            'start_date': min(dates).strftime('%Y-%m-%d'),
            'end_date': max(dates).strftime('%Y-%m-%d'),
            'days': len(merged)
        },
        'balance_stats': {
            'avg_total_value': sum(total_values) / len(total_values),
            'min_total_value': min(total_values),
            'max_total_value': max(total_values),
            'avg_crypto_value': sum(crypto_values) / len(crypto_values)
        },
        'correlations': {}
    }

    # Correlation with total portfolio value
    results['correlations']['total_value'] = {
        'btc': calculate_correlation_coefficient(total_values, btc_prices),
        'eth': calculate_correlation_coefficient(total_values, eth_prices),
        'xrp': calculate_correlation_coefficient(total_values, xrp_prices)
    }

    # Correlation with crypto holdings only
    results['correlations']['crypto_value'] = {
        'btc': calculate_correlation_coefficient(crypto_values, btc_prices),
        'eth': calculate_correlation_coefficient(crypto_values, eth_prices),
        'xrp': calculate_correlation_coefficient(crypto_values, xrp_prices)
    }

    # Correlation with profit rate
    results['correlations']['profit_rate'] = {
        'btc': calculate_correlation_coefficient(profit_rates, btc_prices),
        'eth': calculate_correlation_coefficient(profit_rates, eth_prices),
        'xrp': calculate_correlation_coefficient(profit_rates, xrp_prices)
    }

    return results


def interpret_correlation(corr_value):
    """
    Interpret correlation coefficient

    Args:
        corr_value: Correlation coefficient (-1 to 1)

    Returns:
        str: Interpretation
    """
    abs_corr = abs(corr_value)

    if abs_corr >= 0.9:
        strength = "매우 강한"
    elif abs_corr >= 0.7:
        strength = "강한"
    elif abs_corr >= 0.5:
        strength = "중간"
    elif abs_corr >= 0.3:
        strength = "약한"
    else:
        strength = "거의 없는"

    direction = "양의" if corr_value > 0 else "음의"

    return f"{strength} {direction} 상관관계 ({corr_value:.3f})"


def print_results(results):
    """Print analysis results"""
    if not results:
        print("데이터가 충분하지 않습니다.")
        return

    print("=" * 80)
    print("  잔고-코인 가격 상관관계 분석")
    print("=" * 80)
    print()

    # Period
    period = results['period']
    print(f"[분석 기간]")
    print(f"  기간: {period['start_date']} ~ {period['end_date']} ({period['days']}일)")
    print()

    # Balance stats
    stats = results['balance_stats']
    print(f"[잔고 통계]")
    print(f"  평균 총액: {stats['avg_total_value']:,.0f}원")
    print(f"  최소 총액: {stats['min_total_value']:,.0f}원")
    print(f"  최대 총액: {stats['max_total_value']:,.0f}원")
    print(f"  평균 암호화폐 가치: {stats['avg_crypto_value']:,.0f}원")
    print()

    # Correlations
    corrs = results['correlations']

    print("[상관관계 분석]")
    print()
    print("1. 포트폴리오 총액 vs 코인 가격:")
    for coin, corr in corrs['total_value'].items():
        print(f"   {coin.upper()}: {interpret_correlation(corr)}")
    print()

    print("2. 암호화폐 보유액 vs 코인 가격:")
    for coin, corr in corrs['crypto_value'].items():
        print(f"   {coin.upper()}: {interpret_correlation(corr)}")
    print()

    if 'profit_rate' in corrs:
        print("3. 수익률 vs 코인 가격:")
        for coin, corr in corrs['profit_rate'].items():
            print(f"   {coin.upper()}: {interpret_correlation(corr)}")
        print()

    # Interpretation
    print("=" * 80)
    print("[해석]")
    print()

    # Find highest correlation
    max_corr_coin = max(corrs['total_value'], key=lambda k: abs(corrs['total_value'][k]))
    max_corr_value = corrs['total_value'][max_corr_coin]

    print(f"가장 강한 상관관계: {max_corr_coin.upper()} (상관계수: {max_corr_value:.3f})")
    print()

    if abs(max_corr_value) >= 0.7:
        print(f"→ 포트폴리오가 {max_corr_coin.upper()} 가격과 강하게 연동되어 있습니다.")
        print(f"   {max_corr_coin.upper()} 보유 비중이 높거나, 전체 시장이 {max_corr_coin.upper()}를 따라가는 경향이 있습니다.")
    elif abs(max_corr_value) >= 0.5:
        print(f"→ 포트폴리오가 {max_corr_coin.upper()} 가격과 중간 수준의 연관성을 보입니다.")
        print(f"   일부 영향을 받지만 다른 요인들도 중요한 역할을 합니다.")
    else:
        print("→ 특정 코인 가격과 강한 상관관계가 없습니다.")
        print("   포트폴리오가 다양하게 분산되어 있거나, KRW 보유 비중이 높을 수 있습니다.")

    print()
    print("=" * 80)


def main():
    """Main function"""
    # Get parameters
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
    else:
        user_id = 1
        print(f"[Info] Using default user_id: {user_id}")

    if len(sys.argv) > 2:
        days = int(sys.argv[2])
    else:
        days = 0  # All available data
        print(f"[Info] Using all available data")

    print()

    # Get database session
    db = get_db_session()

    try:
        print("[1/3] Fetching balance history...")
        balance_df = fetch_balance_history(db, user_id, days)
        print(f"      Loaded {len(balance_df)} balance snapshots")

        print("[2/3] Fetching coin prices...")
        price_df = fetch_coin_prices(db, days)
        print(f"      Loaded {len(price_df)} price records")

        print("[3/3] Calculating correlations...")
        results = calculate_correlation(balance_df, price_df)
        print()

        print_results(results)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
