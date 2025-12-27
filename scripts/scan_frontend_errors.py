#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Frontend Error Scanner
Scans all frontend HTML pages for potential JavaScript errors
"""

import os
import re
from pathlib import Path

# Pages to scan
PAGES = [
    'dashboard.html',
    'overview.html',
    'trading_chart.html',
    'portfolio.html',
    'history.html',
    'surge_monitoring.html',
    'my_signals.html',
    'surge_auto_trading.html',
    'telegram_settings.html',
    'pricing.html',
    'referral.html',
    'my_feedback.html',
    'settings.html',
    'admin.html',
    'surge_history.html'
]

FRONTEND_DIR = Path(__file__).parent.parent / 'frontend'

# Common error patterns
ERROR_PATTERNS = {
    'undefined_var': r'(^|\W)(console\.log|alert|if|while|for)\s*\(\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*[,\)]',
    'missing_semicolon': r'}[\s]*\n[\s]*[a-zA-Z]',
    'fetch_without_catch': r'fetch\([^)]+\)(?!.*\.catch)',
    'getelement_by_id': r'document\.getElementById\(["\']([^"\']+)["\']\)',
    'query_selector': r'document\.querySelector\(["\']([^"\']+)["\']\)',
    'event_listener': r'addEventListener\(["\']([^"\']+)["\']',
    'api_endpoint': r'fetch\([^)]*["\']([^"\']*\/api\/[^"\']+)["\']',
    'window_object': r'window\.([a-zA-Z_$][a-zA-Z0-9_$]*)',
    'localStorage': r'localStorage\.(getItem|setItem|removeItem)\(["\']([^"\']+)["\']',
}

def scan_file(filepath):
    """Scan a single HTML file for errors"""
    errors = []
    warnings = []
    info = []

    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            lines = content.split('\n')

        # Extract script sections
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, content, re.DOTALL)

        if not scripts:
            warnings.append("No JavaScript found in file")
            return {'errors': errors, 'warnings': warnings, 'info': info}

        all_script = '\n'.join(scripts)
        script_lines = all_script.split('\n')

        # Check for common issues

        # 1. Undefined API_BASE
        if 'API_BASE' in all_script and 'window.API_BASE' not in all_script and 'const API_BASE' not in all_script:
            errors.append("API_BASE may be undefined - check if it's set globally")

        # 2. Missing error handling on fetch
        fetch_calls = re.findall(r'fetch\([^)]+\)', all_script)
        for call in fetch_calls:
            if '.catch' not in all_script[all_script.index(call):all_script.index(call)+200]:
                warnings.append(f"Fetch call without .catch(): {call[:50]}...")

        # 3. getElementById without null check
        element_ids = re.findall(r'document\.getElementById\(["\']([^"\']+)["\']\)', all_script)
        for element_id in set(element_ids):
            # Check if it's used without null check nearby
            pattern = rf'getElementById\(["\']({element_id})["\']\)'
            matches = list(re.finditer(pattern, all_script))
            for match in matches:
                context = all_script[max(0, match.start()-100):min(len(all_script), match.end()+100)]
                if ' if ' not in context and ' && ' not in context:
                    warnings.append(f"getElementById('{element_id}') used without null check")

        # 4. API endpoints used
        api_endpoints = re.findall(r'["\']([^"\']*\/api\/[^"\']+)["\']', all_script)
        if api_endpoints:
            info.append(f"API endpoints: {', '.join(set(api_endpoints))}")

        # 5. Event listeners
        events = re.findall(r'addEventListener\(["\']([^"\']+)["\']', all_script)
        if events:
            info.append(f"Event listeners: {', '.join(set(events))}")

        # 6. Window objects accessed
        window_objects = re.findall(r'window\.([a-zA-Z_$][a-zA-Z0-9_$]*)', all_script)
        if window_objects:
            info.append(f"Window objects: {', '.join(set(window_objects)[:5])}")  # First 5 only

        # 7. LocalStorage keys
        ls_keys = re.findall(r'localStorage\.(getItem|setItem|removeItem)\(["\']([^"\']+)["\']', all_script)
        if ls_keys:
            keys = set([k[1] for k in ls_keys])
            info.append(f"LocalStorage keys: {', '.join(keys)}")

        # 8. Check for common typos
        if 'console.log' in all_script:
            count = all_script.count('console.log')
            if count > 10:
                warnings.append(f"Too many console.log statements ({count}) - consider removing for production")

        # 9. Check for TODO/FIXME comments
        todos = re.findall(r'// TODO:([^\n]+)', all_script)
        if todos:
            info.append(f"TODOs found: {len(todos)}")

        fixmes = re.findall(r'// FIXME:([^\n]+)', all_script)
        if fixmes:
            warnings.append(f"FIXMEs found: {len(fixmes)}")

    except Exception as e:
        errors.append(f"Error reading file: {str(e)}")

    return {'errors': errors, 'warnings': warnings, 'info': info}

def main():
    """Main scanning function"""
    print("="*80)
    print("Frontend Error Scanner")
    print("="*80)
    print(f"\nScanning {len(PAGES)} pages...\n")

    results = {}
    total_errors = 0
    total_warnings = 0

    for page in PAGES:
        filepath = FRONTEND_DIR / page

        if not filepath.exists():
            print(f"❌ {page}: FILE NOT FOUND")
            continue

        result = scan_file(filepath)
        results[page] = result

        errors = len(result['errors'])
        warnings = len(result['warnings'])
        total_errors += errors
        total_warnings += warnings

        # Print status
        if errors > 0:
            status = f"[ERROR] {errors} errors, {warnings} warnings"
        elif warnings > 0:
            status = f"[WARN] {warnings} warnings"
        else:
            status = "[OK] No issues"

        print(f"{page:30s} {status}")

        # Print details
        if errors > 0 or warnings > 0:
            for error in result['errors']:
                print(f"  ERROR: {error}")
            for warning in result['warnings']:
                print(f"  WARNING: {warning}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total pages scanned: {len(PAGES)}")
    print(f"Total errors: {total_errors}")
    print(f"Total warnings: {total_warnings}")

    if total_errors == 0 and total_warnings == 0:
        print("\n[OK] All pages passed basic checks!")
    else:
        print(f"\n[WARNING] Found {total_errors} errors and {total_warnings} warnings")
        print("Review the output above for details.")

    # Save detailed report
    report_path = Path(__file__).parent / 'frontend_error_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Frontend Error Report\n")
        f.write("="*80 + "\n\n")

        for page, result in results.items():
            f.write(f"\n{page}\n")
            f.write("-"*len(page) + "\n")

            if result['errors']:
                f.write("\nErrors:\n")
                for error in result['errors']:
                    f.write(f"  - {error}\n")

            if result['warnings']:
                f.write("\nWarnings:\n")
                for warning in result['warnings']:
                    f.write(f"  - {warning}\n")

            if result['info']:
                f.write("\nInfo:\n")
                for info_item in result['info']:
                    f.write(f"  - {info_item}\n")

    print(f"\n📄 Detailed report saved to: {report_path}")

if __name__ == '__main__':
    main()
