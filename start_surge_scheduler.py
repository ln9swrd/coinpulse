#!/usr/bin/env python3
"""
Surge Alert Scheduler Startup Script

This script starts the surge alert scheduler service with proper path configuration.
"""
import sys
import asyncio
sys.path.insert(0, '/opt/coinpulse')

if __name__ == '__main__':
    print('[INFO] Starting Surge Alert Scheduler...')
    from backend.services.surge_alert_scheduler import main
    print('[INFO] Scheduler module loaded. Starting async main loop...')
    asyncio.run(main())
