"""
Generate DataLoader module with delegation pattern
"""

import re

# Read source file
with open('frontend/js/trading_chart_working.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Methods to extract
methods = [
    'loadData', 'loadInitialCandles', 'setupTradingViewStyleLoading',
    'loadHistoricalData', 'loadLatestData', 'loadBackgroundData',
    'loadHoldings', 'autoCreateManualPolicies', 'loadTradingHistory',
    'addTradingHistoryMarkers', 'loadCoinList', 'updateCoinSelectBox',
    'searchCoins', 'getCoinIcon'
]

def extract_method_body(lines, method_name):
    """Extract method body from lines"""
    method_lines = []
    in_method = False
    brace_count = 0

    for i, line in enumerate(lines):
        if not in_method:
            # Match method definition
            pattern = rf'^\s*(async\s+)?{method_name}\s*\('
            if re.search(pattern, line):
                in_method = True
                # Start collecting from the line with opening brace
                method_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                continue

        if in_method:
            method_lines.append(line)
            brace_count += line.count('{') - line.count('}')

            if brace_count == 0 and len(method_lines) > 1:
                return method_lines

    return method_lines

# Generate DataLoader class
output = []

# Header
output.append('/**\n')
output.append(' * ========================================\n')
output.append(' * DATA LOADER MODULE\n')
output.append(' * ========================================\n')
output.append(' * Handles all data loading operations for the trading chart\n')
output.append(' * Uses delegation pattern - holds reference to chart instance\n')
output.append(' *\n')
output.append(' * @class DataLoader\n')
output.append(' */\n')
output.append('\n')
output.append('class DataLoader {\n')
output.append('    constructor(chart) {\n')
output.append('        this.chart = chart;\n')
output.append('        console.log(\'[DataLoader] Module initialized\');\n')
output.append('    }\n')
output.append('\n')

# Extract each method
for method in methods:
    print(f'Extracting {method}...')
    method_body = extract_method_body(lines, method)

    if method_body:
        # Replace 'this.' with 'this.chart.' in method body
        for line in method_body:
            # Skip the method signature line
            if re.search(rf'^\s*(async\s+)?{method}\s*\(', line):
                output.append('    ' + line)
                continue

            # Replace this. with this.chart. (but not this.chart.chart.)
            modified_line = re.sub(r'\bthis\.(?!chart\.)', 'this.chart.', line)
            output.append('    ' + modified_line)

        output.append('\n')
        print(f'  OK: {method} extracted ({len(method_body)} lines)')
    else:
        print(f'  ERROR: {method} not found')

# Close class
output.append('}\n')
output.append('\n')
output.append('// Export for module usage\n')
output.append('if (typeof window !== \'undefined\') {\n')
output.append('    window.DataLoader = DataLoader;\n')
output.append('}\n')

# Write output file
with open('frontend/js/core/data_loader.js', 'w', encoding='utf-8') as f:
    f.writelines(output)

print(f'\nOK: DataLoader module generated: {len(output)} lines')
print('  Saved to: frontend/js/core/data_loader.js')
