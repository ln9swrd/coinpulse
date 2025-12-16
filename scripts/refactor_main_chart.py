"""
Refactor WorkingTradingChart to use delegated modules
1. Remove extracted methods
2. Add module initialization
3. Replace method calls with delegation
"""

import re

# Read original file
with open('frontend/js/trading_chart_working.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Methods to remove (already extracted to modules)
dataloader_methods = [
    'loadData', 'loadInitialCandles', 'setupTradingViewStyleLoading',
    'loadHistoricalData', 'loadLatestData', 'loadBackgroundData',
    'loadHoldings', 'autoCreateManualPolicies', 'loadTradingHistory',
    'addTradingHistoryMarkers', 'loadCoinList', 'updateCoinSelectBox',
    'searchCoins', 'getCoinIcon'
]

realtime_methods = [
    'startAutoUpdate', 'stopAutoUpdate', 'updatePriceInfo',
    'updateMAValues', 'updateRealTimeAnalysis', 'updateTrendDirection',
    'updateVolatility', 'updateSupportResistanceLevels', 'updateMAs'
]

all_methods_to_remove = dataloader_methods + realtime_methods

def should_skip_line(lines, index, methods_to_remove):
    """Check if we're inside a method that should be removed"""
    line = lines[index]

    # Check if this line starts a method we want to remove
    for method in methods_to_remove:
        pattern = rf'^\s*(async\s+)?{method}\s*\('
        if re.search(pattern, line):
            return True, method

    return False, None

# Process lines
output = []
i = 0
removed_count = 0
current_method = None
brace_count = 0
in_removed_method = False

while i < len(lines):
    line = lines[i]

    # Check if we're starting a method to remove
    if not in_removed_method:
        should_skip, method_name = should_skip_line(lines, i, all_methods_to_remove)

        if should_skip:
            print(f'Removing method: {method_name}')
            in_removed_method = True
            current_method = method_name
            brace_count = line.count('{') - line.count('}')
            removed_count += 1
            i += 1
            continue

    # If we're in a method to remove, track braces
    if in_removed_method:
        brace_count += line.count('{') - line.count('}')

        # Method ends when braces balance
        if brace_count == 0:
            in_removed_method = False
            current_method = None
            print(f'  Method removed')

        i += 1
        continue

    # Check for AutoTradingController class (remove entirely)
    if 'class AutoTradingController' in line:
        print('Removing AutoTradingController class')
        # Skip until end of file or next class
        while i < len(lines):
            i += 1
            if i >= len(lines):
                break
        continue

    # Keep this line
    output.append(line)
    i += 1

print(f'\nRemoved {removed_count} methods')
print(f'Original: {len(lines)} lines')
print(f'After removal: {len(output)} lines')
print(f'Reduction: {len(lines) - len(output)} lines ({((len(lines) - len(output)) / len(lines) * 100):.1f}%)')

# Now add module initialization in constructor
final_output = []
for i, line in enumerate(output):
    final_output.append(line)

    # Add module initialization after constructor properties
    if 'console.log(\'[Working] Chart class initialized\')' in line:
        final_output.append('\n')
        final_output.append('        // Initialize delegated modules\n')
        final_output.append('        this.dataLoader = null; // Will be initialized after chart is ready\n')
        final_output.append('        this.realtimeUpdates = null; // Will be initialized after chart is ready\n')
        print('Added module initialization placeholders in constructor')

    # Add actual module creation in init()
    if 'console.log(\'[Working] Main initialization completed\')' in line:
        final_output.append('\n')
        final_output.append('            // Initialize DataLoader module\n')
        final_output.append('            this.dataLoader = new DataLoader(this);\n')
        final_output.append('            console.log(\'[Working] DataLoader module initialized\');\n')
        final_output.append('\n')
        final_output.append('            // Initialize RealtimeUpdates module\n')
        final_output.append('            this.realtimeUpdates = new RealtimeUpdates(this);\n')
        final_output.append('            console.log(\'[Working] RealtimeUpdates module initialized\');\n')
        print('Added module initialization in init() method')

# Write result
with open('frontend/js/trading_chart_working.js', 'w', encoding='utf-8') as f:
    f.writelines(final_output)

print(f'\nFinal output: {len(final_output)} lines')
print('Refactoring complete!')
print('\nNext steps:')
print('1. Update method calls to use delegation (this.loadData() -> this.dataLoader.loadData())')
print('2. Update HTML to import new modules')
print('3. Test in browser')
