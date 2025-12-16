#!/bin/bash
# ============================================================================
# CoinPulse Integrated Server Startup Script (Linux/Mac)
# ============================================================================

set -e  # Exit on error

echo "================================================================================"
echo "CoinPulse Integrated Web Service"
echo "================================================================================"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "[WARNING] .env file not found!"
    echo "Please copy .env.example to .env and configure your settings"
    echo ""
    read -p "Would you like to continue with default settings? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 1
    fi
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "[OK] Python found"
python3 --version
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[INFO] Virtual environment not found, creating..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment"
        exit 1
    fi
    echo "[OK] Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to activate virtual environment"
    exit 1
fi
echo "[OK] Virtual environment activated"
echo ""

# Install/Update dependencies
echo "[INFO] Checking dependencies..."
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi
echo "[OK] Dependencies installed"
echo ""

# Create necessary directories
mkdir -p data logs
echo "[OK] Directories created"
echo ""

# Check if database exists
if [ ! -f "data/coinpulse.db" ]; then
    echo "[WARNING] Database not found"
    echo "Initializing database..."
    python init_auth_db.py
    if [ $? -ne 0 ]; then
        echo "[WARNING] Database initialization had issues, but continuing..."
    else
        echo "[OK] Database initialized"
    fi
    echo ""
fi

# Check if port 8080 is available
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "[WARNING] Port 8080 is already in use"
    echo "Attempting to terminate the process..."
    lsof -ti:8080 | xargs kill -9 2>/dev/null || true
    sleep 2
    echo ""
fi

# Start the server
echo "================================================================================"
echo "Starting CoinPulse Integrated Server..."
echo "================================================================================"
echo "Server will be available at: http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo "================================================================================"
echo ""

python app.py

# Cleanup on exit
echo ""
echo "Server stopped"
