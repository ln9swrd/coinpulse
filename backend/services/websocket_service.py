"""
WebSocket Service for Real-time Updates

Provides real-time streaming for:
- Live price updates
- Order notifications
- Position changes

Uses Flask-SocketIO for WebSocket communication.
"""

import os
import time
import threading
from datetime import datetime
from typing import Dict, Set, Optional
import requests
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request

# Global SocketIO instance (will be initialized by app)
socketio = None


class WebSocketService:
    """Manages WebSocket connections and real-time updates"""

    def __init__(self, socketio_instance: SocketIO):
        global socketio
        socketio = socketio_instance
        self.socketio = socketio_instance

        # Track active subscriptions
        self.price_subscribers: Dict[str, Set[str]] = {}  # {market: set of session_ids}
        self.user_sessions: Dict[int, Set[str]] = {}  # {user_id: set of session_ids}

        # Background threads
        self.price_update_thread = None
        self.is_running = False

    def start(self):
        """Start background threads for real-time updates"""
        if self.is_running:
            print("[WebSocket] Already running")
            return

        self.is_running = True

        # Start price update thread
        self.price_update_thread = threading.Thread(
            target=self._price_update_loop,
            daemon=True
        )
        self.price_update_thread.start()

        print("[WebSocket] Service started")

    def stop(self):
        """Stop background threads"""
        self.is_running = False
        print("[WebSocket] Service stopped")

    def _price_update_loop(self):
        """Background thread that fetches and broadcasts price updates"""
        print("[WebSocket] Price update loop started")

        while self.is_running:
            try:
                # Get all subscribed markets
                markets = list(self.price_subscribers.keys())

                if markets:
                    # Fetch prices for all subscribed markets
                    prices = self._fetch_prices(markets)

                    # Broadcast to subscribers
                    for market, price_data in prices.items():
                        self._broadcast_price_update(market, price_data)

                # Wait before next update (1 second for real-time feel)
                time.sleep(1)

            except Exception as e:
                print(f"[WebSocket] Error in price update loop: {str(e)}")
                time.sleep(5)  # Wait longer on error

    def _fetch_prices(self, markets: list) -> Dict:
        """Fetch current prices from Upbit API"""
        try:
            # Upbit ticker API (supports multiple markets)
            markets_param = ','.join(markets)
            url = f"https://api.upbit.com/v1/ticker?markets={markets_param}"

            response = requests.get(url, timeout=5)
            response.raise_for_status()

            tickers = response.json()

            # Format price data
            prices = {}
            for ticker in tickers:
                market = ticker['market']
                prices[market] = {
                    'market': market,
                    'price': ticker['trade_price'],
                    'change': ticker['signed_change_rate'] * 100,  # Percentage
                    'change_price': ticker['signed_change_price'],
                    'volume': ticker['acc_trade_volume_24h'],
                    'timestamp': datetime.utcnow().isoformat()
                }

            return prices

        except Exception as e:
            print(f"[WebSocket] Error fetching prices: {str(e)}")
            return {}

    def _broadcast_price_update(self, market: str, price_data: dict):
        """Broadcast price update to all subscribers of a market"""
        if market in self.price_subscribers:
            # Emit to market room
            self.socketio.emit(
                'price_update',
                price_data,
                room=f"market:{market}"
            )

    def subscribe_to_market(self, session_id: str, market: str):
        """Subscribe a session to market price updates"""
        if market not in self.price_subscribers:
            self.price_subscribers[market] = set()

        self.price_subscribers[market].add(session_id)

        # Join Socket.IO room
        join_room(f"market:{market}")

        print(f"[WebSocket] Session {session_id[:8]} subscribed to {market}")

    def unsubscribe_from_market(self, session_id: str, market: str):
        """Unsubscribe a session from market price updates"""
        if market in self.price_subscribers:
            self.price_subscribers[market].discard(session_id)

            # Clean up empty market
            if not self.price_subscribers[market]:
                del self.price_subscribers[market]

            # Leave Socket.IO room
            leave_room(f"market:{market}")

            print(f"[WebSocket] Session {session_id[:8]} unsubscribed from {market}")

    def register_user_session(self, user_id: int, session_id: str):
        """Register a user session for notifications"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()

        self.user_sessions[user_id].add(session_id)

        # Join user-specific room
        join_room(f"user:{user_id}")

        print(f"[WebSocket] User {user_id} session registered: {session_id[:8]}")

    def unregister_user_session(self, user_id: int, session_id: str):
        """Unregister a user session"""
        if user_id in self.user_sessions:
            self.user_sessions[user_id].discard(session_id)

            # Clean up empty user
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]

            # Leave user-specific room
            leave_room(f"user:{user_id}")

            print(f"[WebSocket] User {user_id} session unregistered: {session_id[:8]}")

    def send_order_notification(self, user_id: int, order_data: dict):
        """Send order notification to user"""
        if user_id in self.user_sessions:
            self.socketio.emit(
                'order_notification',
                {
                    'type': 'order',
                    'data': order_data,
                    'timestamp': datetime.utcnow().isoformat()
                },
                room=f"user:{user_id}"
            )

            print(f"[WebSocket] Order notification sent to user {user_id}")

    def send_position_update(self, user_id: int, position_data: dict):
        """Send position update to user"""
        if user_id in self.user_sessions:
            self.socketio.emit(
                'position_update',
                {
                    'type': 'position',
                    'data': position_data,
                    'timestamp': datetime.utcnow().isoformat()
                },
                room=f"user:{user_id}"
            )

            print(f"[WebSocket] Position update sent to user {user_id}")

    def broadcast_to_all(self, event: str, data: dict):
        """Broadcast message to all connected clients"""
        self.socketio.emit(event, data)
        print(f"[WebSocket] Broadcast: {event}")


# Global WebSocket service instance
ws_service: Optional[WebSocketService] = None


def init_websocket_service(socketio_instance: SocketIO):
    """Initialize WebSocket service"""
    global ws_service
    ws_service = WebSocketService(socketio_instance)
    ws_service.start()
    return ws_service


def get_websocket_service() -> WebSocketService:
    """Get WebSocket service instance"""
    global ws_service
    if ws_service is None:
        raise RuntimeError("WebSocket service not initialized")
    return ws_service


# ==================== Socket.IO Event Handlers ====================

def setup_socketio_handlers(socketio_instance: SocketIO):
    """Set up Socket.IO event handlers"""

    @socketio_instance.on('connect')
    def handle_connect():
        """Handle client connection"""
        session_id = request.sid
        print(f"[WebSocket] Client connected: {session_id[:8]}")

        # Send welcome message
        emit('connected', {
            'message': 'Connected to CoinPulse WebSocket',
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        })

    @socketio_instance.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        session_id = request.sid
        print(f"[WebSocket] Client disconnected: {session_id[:8]}")

        # Clean up subscriptions
        ws = get_websocket_service()

        # Remove from all market subscriptions
        for market in list(ws.price_subscribers.keys()):
            ws.unsubscribe_from_market(session_id, market)

        # Remove from user sessions
        for user_id in list(ws.user_sessions.keys()):
            ws.unregister_user_session(user_id, session_id)

    @socketio_instance.on('subscribe_market')
    def handle_subscribe_market(data):
        """Handle market subscription"""
        session_id = request.sid
        market = data.get('market')

        if not market:
            emit('error', {'message': 'Market parameter required'})
            return

        ws = get_websocket_service()
        ws.subscribe_to_market(session_id, market)

        emit('subscribed', {
            'market': market,
            'timestamp': datetime.utcnow().isoformat()
        })

    @socketio_instance.on('unsubscribe_market')
    def handle_unsubscribe_market(data):
        """Handle market unsubscription"""
        session_id = request.sid
        market = data.get('market')

        if not market:
            emit('error', {'message': 'Market parameter required'})
            return

        ws = get_websocket_service()
        ws.unsubscribe_from_market(session_id, market)

        emit('unsubscribed', {
            'market': market,
            'timestamp': datetime.utcnow().isoformat()
        })

    @socketio_instance.on('authenticate')
    def handle_authenticate(data):
        """Handle user authentication for notifications"""
        session_id = request.sid
        user_id = data.get('user_id')

        if not user_id:
            emit('error', {'message': 'User ID required'})
            return

        # In production, verify JWT token here
        # For now, trust the user_id

        ws = get_websocket_service()
        ws.register_user_session(user_id, session_id)

        emit('authenticated', {
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        })

    @socketio_instance.on('ping')
    def handle_ping():
        """Handle ping (keep-alive)"""
        emit('pong', {'timestamp': datetime.utcnow().isoformat()})

    print("[WebSocket] Event handlers registered")
