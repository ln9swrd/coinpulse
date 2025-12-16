# CoinPulse Manager - Usage Guide

## Overview
`coinpulse_manager.bat` is a comprehensive batch file tool for managing CoinPulse servers on Windows. It provides an easy-to-use menu interface for starting, stopping, and monitoring servers.

## Features

### 1. Start All Servers
- Automatically checks port availability
- Kills conflicting processes if ports are in use
- Starts Chart Server (port 8080)
- Starts Trading Server (port 8081)
- Verifies servers are running correctly
- Displays access URLs

### 2. Stop All Servers
- Gracefully terminates all server processes
- Kills processes on ports 8080 and 8081
- Ensures clean shutdown

### 3. Check Server Status
- Shows which servers are running
- Displays process IDs (PIDs)
- Shows port usage information
- Lists all Python processes

### 4. Fix Port Conflicts
- Scans for processes using ports 8080 and 8081
- Automatically terminates conflicting processes
- Resolves port conflicts without manual intervention

### 5. View Server Logs
- Displays Chart Server logs
- Displays Trading Server logs
- Automatically creates logs directory if missing
- Helps diagnose server issues

### 6. Restart Servers
- Stops all running servers
- Waits 2 seconds for clean shutdown
- Starts servers again
- Quick way to apply configuration changes

### 7. Run Diagnostics
- Performs comprehensive system check
- Verifies required files exist
- Checks configuration files
- Tests network ports
- Displays disk space information
- Shows Python installation status

### 8. Exit
- Cleanly exits the manager
- Displays thank you message

## How to Use

### Method 1: Double-click from Explorer
1. Navigate to the CoinPulse directory in Windows Explorer
2. Double-click `coinpulse_manager.bat`
3. The menu will appear automatically
4. Select options by typing numbers 1-8

### Method 2: Run from Command Prompt
```cmd
cd "D:\Claude\Projects\Active\코인펄스"
coinpulse_manager.bat
```

### Method 3: Create Desktop Shortcut
1. Right-click `coinpulse_manager.bat`
2. Select "Create Shortcut"
3. Drag shortcut to Desktop
4. Double-click shortcut to launch

## Troubleshooting

### Problem: Servers won't start
**Solution:**
1. Run option [7] Run Diagnostics
2. Check if Python is installed: `python --version`
3. Verify server files exist in current directory
4. Check logs in `logs\chart_server.log` and `logs\trading_server.log`

### Problem: Port conflicts
**Solution:**
1. Run option [4] Fix Port Conflicts
2. This will automatically kill processes on ports 8080 and 8081
3. Then run option [1] Start All Servers

### Problem: Cannot find server files
**Solution:**
1. Make sure you're in the correct directory
2. The batch file automatically changes to its own directory
3. Verify `clean_upbit_server.py` and `simple_dual_server.py` exist

### Problem: Encoding errors (Korean characters)
**Solution:**
- The batch file uses UTF-8 encoding (`chcp 65001`)
- All output should display correctly
- If you see garbled text, check your terminal encoding

## System Requirements

- Windows 10 or later
- Python 3.7 or later installed
- Required Python packages installed
- Ports 8080 and 8081 available

## File Structure

```
코인펄스/
├── coinpulse_manager.bat          # Main manager script
├── clean_upbit_server.py          # Chart Server
├── simple_dual_server.py          # Trading Server
├── chart_server_config.json       # Chart Server config
├── trading_server_config.json     # Trading Server config
├── logs/                          # Server logs (auto-created)
│   ├── chart_server.log
│   └── trading_server.log
└── frontend/
    ├── config.json               # Frontend config
    └── trading_chart.html        # Main interface
```

## Error Detection

The manager automatically detects and reports:
- Missing Python installation
- Missing server files
- Port conflicts
- Missing configuration files
- Missing logs directory (creates automatically)
- Server startup failures
- Process termination failures

## Logs

Server logs are stored in the `logs/` directory:
- `chart_server.log` - Chart API Server logs
- `trading_server.log` - Trading API Server logs

View logs using option [5] or open files directly in a text editor.

## Tips

1. **First Time Setup**: Run option [7] Run Diagnostics to ensure everything is configured correctly
2. **Quick Restart**: Use option [6] to restart servers after code changes
3. **Clean Shutdown**: Always use option [2] to stop servers gracefully
4. **Monitor Status**: Use option [3] to check if servers are running properly
5. **View Logs**: If something isn't working, check logs with option [5]

## Advanced Usage

### Running Specific Commands
You can modify the batch file to add custom commands. The structure is:
```batch
:YOUR_COMMAND
cls
echo Your message here
REM Your commands here
pause
goto MAIN_MENU
```

### Changing Ports
Ports are configured in JSON files, not hardcoded:
- `chart_server_config.json` for port 8080
- `trading_server_config.json` for port 8081

Follow the project guidelines - never hardcode port numbers!

## Safety Features

1. **Automatic Directory Change**: Always runs from its own directory
2. **Error Counting**: Tracks and reports errors during system check
3. **Process Verification**: Confirms servers started successfully
4. **Graceful Fallback**: Returns to menu on errors
5. **Log Creation**: Automatically creates logs directory
6. **Port Checking**: Verifies ports before starting servers

## Project Guidelines Compliance

This manager follows all CoinPulse project guidelines:
- ✅ No hardcoded ports
- ✅ No hardcoded URLs
- ✅ UTF-8 encoding
- ✅ English-only output (no emojis)
- ✅ Error handling
- ✅ Configuration file based
- ✅ Modular structure
- ✅ Port conflict resolution

## Support

If you encounter issues:
1. Run diagnostics (option 7)
2. Check server logs (option 5)
3. Verify system requirements
4. Check project documentation in CLAUDE.md

## Version History

- v1.0 (2025-10-18): Initial release with full feature set
  - Menu-based interface
  - Automatic error detection
  - Port conflict resolution
  - Comprehensive diagnostics
  - Log viewing
  - System checks
