"""
Update method calls in WorkingTradingChart to use delegation
"""

import re

# Read file
with open('frontend/js/trading_chart_working.js', 'r', encoding='utf-8') as f:
    content = f.read()

# DataLoader methods
dataloader_methods = [
    'loadData', 'loadInitialCandles', 'setupTradingViewStyleLoading',
    'loadHistoricalData', 'loadLatestData', 'loadBackgroundData',
    'loadHoldings', 'autoCreateManualPolicies', 'loadTradingHistory',
    'addTradingHistoryMarkers', 'loadCoinList', 'updateCoinSelectBox',
    'searchCoins', 'getCoinIcon'
]

# RealtimeUpdates methods
realtime_methods = [
    'startAutoUpdate', 'stopAutoUpdate', 'updatePriceInfo',
    'updateMAValues', 'updateRealTimeAnalysis', 'updateTrendDirection',
    'updateVolatility', 'updateSupportResistanceLevels', 'updateMAs'
]

# Replace this.method() with this.dataLoader.method()
for method in dataloader_methods:
    # Match: this.method( but not this.chart.method( or this.dataLoader.method(
    pattern = rf'\bthis\.{method}\('
    replacement = f'this.dataLoader.{method}('

    count = len(re.findall(pattern, content))
    if count > 0:
        content = re.sub(pattern, replacement, content)
        print(f'DataLoader: {method}() - {count} calls updated')

# Replace this.method() with this.realtimeUpdates.method()
for method in realtime_methods:
    pattern = rf'\bthis\.{method}\('
    replacement = f'this.realtimeUpdates.{method}('

    count = len(re.findall(pattern, content))
    if count > 0:
        content = re.sub(pattern, replacement, content)
        print(f'RealtimeUpdates: {method}() - {count} calls updated')

# Write updated file
with open('frontend/js/trading_chart_working.js', 'w', encoding='utf-8') as f:
    f.write(content)

print('\nMethod calls updated successfully!')
print('File: frontend/js/trading_chart_working.js')
