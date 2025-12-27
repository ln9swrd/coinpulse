#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add error-handler.js to all HTML pages
"""

import os
import re
from pathlib import Path

FRONTEND_DIR = Path(__file__).parent.parent / 'frontend'
ERROR_HANDLER_SCRIPT = '<script src="js/error-handler.js?v=20251227"></script>'

# Pages to update (excluding ones already done)
PAGES = [
    'overview.html',
    'surge_monitoring.html',
    'my_signals.html',
    'surge_auto_trading.html',
    'telegram_settings.html',
    'referral.html',
    'my_feedback.html',
    'settings.html',
    'admin.html',
    'surge_history.html'
]

def add_error_handler_to_file(filepath):
    """Add error-handler.js script tag to HTML file"""
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()

        # Check if already added
        if 'error-handler.js' in content:
            print(f"  [SKIP] {filepath.name} - Already has error-handler.js")
            return False

        # Find </head> tag and insert before it
        if '</head>' not in content:
            print(f"  [ERROR] {filepath.name} - No </head> tag found")
            return False

        # Insert before </head>
        new_content = content.replace('</head>', f'    {ERROR_HANDLER_SCRIPT}\n</head>')

        # Write back
        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write(new_content)

        print(f"  [OK] {filepath.name} - Added error-handler.js")
        return True

    except Exception as e:
        print(f"  [ERROR] {filepath.name} - {str(e)}")
        return False

def main():
    """Main function"""
    print("="*80)
    print("Adding error-handler.js to all pages")
    print("="*80)
    print()

    updated = 0
    skipped = 0
    errors = 0

    for page in PAGES:
        filepath = FRONTEND_DIR / page

        if not filepath.exists():
            print(f"  [NOT FOUND] {page}")
            errors += 1
            continue

        result = add_error_handler_to_file(filepath)

        if result is True:
            updated += 1
        elif result is False:
            skipped += 1
        else:
            errors += 1

    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")
    print(f"Errors: {errors}")
    print()

    if updated > 0:
        print(f"Successfully added error-handler.js to {updated} pages!")
    else:
        print("No pages were updated.")

if __name__ == '__main__':
    main()
