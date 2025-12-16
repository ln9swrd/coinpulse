"""
CoinPulse Subscription API Server
Standalone server for testing subscription endpoints
"""

import os
import sys
from flask import Flask
from flask_cors import CORS

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from routes.subscription_routes import subscription_bp

# Create Flask app
app = Flask(__name__)

# Enable CORS
CORS(app, origins=['*'], supports_credentials=True)

# Register Blueprint
app.register_blueprint(subscription_bp)

# Root endpoint
@app.route('/')
def index():
    return {
        'service': 'CoinPulse Subscription API',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/subscription/upgrade': 'Create/Upgrade subscription',
            'POST /api/subscription/cancel': 'Cancel subscription',
            'GET /api/subscription/current': 'Get current subscription',
            'GET /api/subscription/transactions': 'Get transaction history',
            'GET /api/subscription/plans': 'Get available plans',
            'GET /api/subscription/health': 'Health check'
        },
        'status': 'running'
    }


@app.route('/health')
def health():
    return {
        'status': 'healthy',
        'service': 'subscription-api'
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8083))
    print(f"""
    ======================================================================
    CoinPulse Subscription API Server
    ======================================================================

    Running on: http://localhost:{port}

    Available Endpoints:
    - POST   /api/subscription/upgrade      Create/Upgrade subscription
    - POST   /api/subscription/cancel       Cancel subscription
    - GET    /api/subscription/current      Get current subscription
    - GET    /api/subscription/transactions Get transaction history
    - GET    /api/subscription/plans        Get available plans
    - GET    /api/subscription/health       Health check

    ======================================================================
    """)

    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        threaded=True
    )
