#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Kill process by PID"""
import os
import sys

if len(sys.argv) < 2:
    print("Usage: python kill_process.py <PID>")
    sys.exit(1)

pid = sys.argv[1]
os.system(f'taskkill /PID {pid} /F')
