"""
Fix internal method calls in DataLoader and RealtimeUpdates modules
Methods within the same class should use this.method(), not this.chart.method()
"""

import re

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

def fix_file(filepath, method_list):
    """Fix internal method calls in a module file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes = 0

    for method in method_list:
        # Replace this.chart.method( with this.method(
        # But only for methods in the same class
        pattern = rf'\bthis\.chart\.{method}\('
        replacement = f'this.{method}('

        count = len(re.findall(pattern, content))
        if count > 0:
            content = re.sub(pattern, replacement, content)
            print(f'  {method}(): {count} internal calls fixed')
            changes += count

    if changes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Total: {changes} fixes applied')
    else:
        print('No fixes needed')

    return changes

print('=== Fixing DataLoader internal calls ===')
dataloader_changes = fix_file('frontend/js/core/data_loader.js', dataloader_methods)

print('\n=== Fixing RealtimeUpdates internal calls ===')
realtime_changes = fix_file('frontend/js/core/realtime_updates.js', realtime_methods)

print(f'\n=== Summary ===')
print(f'DataLoader: {dataloader_changes} fixes')
print(f'RealtimeUpdates: {realtime_changes} fixes')
print(f'Total: {dataloader_changes + realtime_changes} fixes')
print('\nFix complete!')
