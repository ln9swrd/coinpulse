"""Analyze large JavaScript file structure"""
import re

file_path = 'frontend/js/trading_chart_working.js'

print(f"Analyzing: {file_path}")
print("=" * 60)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# Count lines
print(f"Total lines: {len(lines)}")

# Find class definition
class_match = re.search(r'class\s+(\w+)', content)
if class_match:
    print(f"Main class: {class_match.group(1)}")

# Find methods
methods = re.findall(r'^\s{4}(async\s+)?(\w+)\s*\(', content, re.MULTILINE)
print(f"\nTotal methods: {len(methods)}")

# Find specific patterns
constructors = len(re.findall(r'constructor\s*\(', content))
async_methods = len(re.findall(r'async\s+\w+\s*\(', content))

print(f"Constructors: {constructors}")
print(f"Async methods: {async_methods}")

# Sample methods (first 20)
print("\nFirst 20 methods:")
for i, (async_kw, method_name) in enumerate(methods[:20], 1):
    prefix = "async " if async_kw else ""
    print(f"  {i}. {prefix}{method_name}()")

print("\n" + "=" * 60)
print("Analysis complete. File needs modularization!")
