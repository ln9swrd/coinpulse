"""
Script to extract DataLoader and RealtimeUpdates modules from trading_chart_working.js
"""

import re

# Read the source file
with open('frontend/js/trading_chart_working.js', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# Define methods for each module
dataloader_methods = [
    'loadData',
    'loadInitialCandles',
    'setupTradingViewStyleLoading',
    'loadHistoricalData',
    'loadLatestData',
    'loadBackgroundData',
    'loadHoldings',
    'autoCreateManualPolicies',
    'loadTradingHistory',
    'addTradingHistoryMarkers',
    'loadCoinList',
    'updateCoinSelectBox',
    'searchCoins',
    'getCoinIcon'
]

realtime_methods = [
    'startAutoUpdate',
    'stopAutoUpdate',
    'updatePriceInfo',
    'updateMAValues',
    'updateRealTimeAnalysis',
    'updateTrendDirection',
    'updateVolatility',
    'updateSupportResistanceLevels',
    'updateMAs'
]

def extract_method(lines, method_name):
    """Extract a method from lines"""
    method_lines = []
    in_method = False
    brace_count = 0
    start_line = -1

    for i, line in enumerate(lines):
        # Look for method definition
        if not in_method:
            # Match: async methodName( or methodName(
            pattern = rf'^\s*(async\s+)?{method_name}\s*\('
            if re.search(pattern, line):
                in_method = True
                start_line = i + 1  # 1-indexed for display
                method_lines.append(line)
                # Count braces in first line
                brace_count += line.count('{') - line.count('}')
                continue

        if in_method:
            method_lines.append(line)
            brace_count += line.count('{') - line.count('}')

            # Method ends when braces balance
            if brace_count == 0 and len(method_lines) > 1:
                end_line = i + 1
                print(f'  {method_name}: Lines {start_line}-{end_line} ({len(method_lines)} lines)')
                return method_lines

    if in_method:
        print(f'  WARNING: {method_name} found but braces did not balance')
        return method_lines

    print(f'  WARNING: {method_name} not found')
    return []

# Extract DataLoader methods
print('\n=== Extracting DataLoader methods ===')
dataloader_code = []
for method in dataloader_methods:
    extracted = extract_method(lines, method)
    if extracted:
        dataloader_code.extend(extracted)
        dataloader_code.append('')  # Empty line between methods

# Extract RealtimeUpdates methods
print('\n=== Extracting RealtimeUpdates methods ===')
realtime_code = []
for method in realtime_methods:
    extracted = extract_method(lines, method)
    if extracted:
        realtime_code.extend(extracted)
        realtime_code.append('')  # Empty line between methods

print(f'\n=== Summary ===')
print(f'DataLoader: {len(dataloader_code)} lines extracted')
print(f'RealtimeUpdates: {len(realtime_code)} lines extracted')

# Save extraction info
with open('scripts/extraction_info.txt', 'w', encoding='utf-8') as f:
    f.write(f'DataLoader: {len(dataloader_code)} lines\n')
    f.write(f'RealtimeUpdates: {len(realtime_code)} lines\n')

print('\nExtraction info saved to scripts/extraction_info.txt')
