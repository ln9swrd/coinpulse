#!/usr/bin/env python3
"""
Signal Monitor Service Startup Script

This script starts the signal monitoring service with proper path configuration.
"""
import sys
sys.path.insert(0, '/opt/coinpulse')

if __name__ == '__main__':
    print('[INFO] Starting Signal Monitor Service...')
    from backend.services.signal_monitor_service import main
    main()
