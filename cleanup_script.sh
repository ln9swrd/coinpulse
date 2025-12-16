#!/bin/bash
echo "======================================"
echo "  CoinPulse Cleanup Script"
echo "======================================"
echo ""

# Old Backups
echo "[1/6] Removing old backup directories..."
rm -rf backup_20251010/
rm -rf backup_20251010_volume_fix/

# Test/Debug Python Scripts
echo "[2/6] Removing test/debug Python scripts..."
rm -f check_unicode.py check_orders.py check_xrp_detail.py check_2024_orders.py
rm -f test_upbit_direct.py check_all_states.py find_order_by_details.py check_api_account.py
rm -f diagnose_history_issue.py test_all_xrp_sources.py critical_diagnosis.py
rm -f find_api_key_creation_date.py test_trades_endpoint.py test_trades_fills.py
rm -f check_order_trades_array.py find_all_execution_times.py test_new_api.py test_performance.py

# Utility Scripts
echo "[3/6] Removing utility scripts..."
rm -f generate_config.py remove_korean_emoji.py cleanup_css.py
rm -f modify_chart_for_multi_panel.py update_rsi_position.py start_coinpulse.py

# Duplicate Batch Files
echo "[4/6] Removing duplicate batch files..."
rm -f coinpulse_manager.bat start_coinpulse.bat stop_coinpulse.bat restart_coinpulse.bat
rm -f test_manager.bat test_manager_simple.bat restart_server.bat check_all_october.bat
rm -f start_servers_background.bat stop_servers.bat check_servers_status.bat

# Test/Debug HTML Files
echo "[5/6] Removing test/debug HTML files..."
rm -f frontend/test_null_fix.html frontend/debug_info.html frontend/test_chart.html
rm -f frontend/verify_features.html frontend/test_upbit_chart_local.html
rm -f frontend/test_simple_chart.html frontend/test_upbit_chart.html frontend/trading_chart_simple.html
rm -f frontend/test_candle_loading.html frontend/debug_simple.html frontend/debug_test.html
rm -f frontend/test_horizontal_lines.html frontend/test_api_debug.html
rm -f frontend/test_support_resistance.html frontend/test_chart_actions.html
rm -f frontend/debug_avg_price.html frontend/test_force_lines.html frontend/test_null_debug.html
rm -f frontend/test_drawing_horizontal.html frontend/test_drawing_list.html
rm -f frontend/test_holdings.html frontend/test_drawing_debug.html frontend/clear_cache.html
rm -f frontend/force_fix_drawings.html frontend/inspect_modal.html

# Legacy JavaScript Files
echo "[6/6] Removing legacy JavaScript files (from backups/modularization)..."
# These are already in backups, so safe to remove from old backup location

echo ""
echo "======================================"
echo "  Cleanup Complete!"
echo "======================================"
echo ""
echo "Summary:"
echo "- Old backups: 2 directories removed"
echo "- Python scripts: ~23 files removed"
echo "- Batch files: ~11 files removed"
echo "- HTML test files: ~25 files removed"
echo ""
echo "Kept essential files:"
echo "- Core servers: clean_upbit_server.py, simple_dual_server.py"
echo "- Manager: coinpulse_manager_v2.bat, QUICK_START.bat"
echo "- Frontend: trading_chart.html, policy_manager.html, test_modular.html"
echo "- Modules: 6 modular JavaScript files"
echo ""
