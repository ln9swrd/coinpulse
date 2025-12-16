"""
Fix cross-module method calls and chart object access
"""

import re

# Read DataLoader
with open('frontend/js/core/data_loader.js', 'r', encoding='utf-8') as f:
    dataloader_content = f.read()

# Read RealtimeUpdates
with open('frontend/js/core/realtime_updates.js', 'r', encoding='utf-8') as f:
    realtime_content = f.read()

print('=== Fixing DataLoader ===')

# Fix RealtimeUpdates method calls in DataLoader
realtime_methods = [
    'startAutoUpdate', 'stopAutoUpdate', 'updatePriceInfo',
    'updateMAValues', 'updateRealTimeAnalysis', 'updateTrendDirection',
    'updateVolatility', 'updateSupportResistanceLevels', 'updateMAs'
]

dl_changes = 0
for method in realtime_methods:
    pattern = rf'\bthis\.chart\.{method}\('
    replacement = f'this.chart.realtimeUpdates.{method}('

    count = len(re.findall(pattern, dataloader_content))
    if count > 0:
        dataloader_content = re.sub(pattern, replacement, dataloader_content)
        print(f'  {method}(): {count} calls fixed to realtimeUpdates')
        dl_changes += count

# Fix direct chart property access (this.chart.chartData, etc.)
# These should remain as this.chart.xxx
# But fix chart object methods (this.chart.timeScale -> this.chart.chart.timeScale)

# Fix chart object method calls
chart_methods = ['timeScale', 'removeSeries']
for method in chart_methods:
    # Match: this.chart.timeScale() but not this.chart.chart.timeScale()
    pattern = rf'\bthis\.chart\.{method}\('
    # Check if not already this.chart.chart.method(
    matches = re.findall(pattern, dataloader_content)

    for match in matches:
        # Check if it's not already this.chart.chart.xxx
        context_pattern = rf'this\.chart\.chart\.{method}\('
        if not re.search(context_pattern, dataloader_content):
            replacement = f'this.chart.chart.{method}('
            dataloader_content = re.sub(pattern, replacement, dataloader_content, count=1)
            print(f'  {method}(): chart object access fixed')
            dl_changes += 1

print(f'Total DataLoader fixes: {dl_changes}')

# Write DataLoader
with open('frontend/js/core/data_loader.js', 'w', encoding='utf-8') as f:
    f.write(dataloader_content)

print('\n=== Fixing RealtimeUpdates ===')

ru_changes = 0

# RealtimeUpdates might also need fixes
# (currently none expected, but check)

print(f'Total RealtimeUpdates fixes: {ru_changes}')

print(f'\n=== Summary ===')
print(f'DataLoader: {dl_changes} fixes')
print(f'RealtimeUpdates: {ru_changes} fixes')
print(f'Total: {dl_changes + ru_changes} fixes')
print('\nFix complete!')
