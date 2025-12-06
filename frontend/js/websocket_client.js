/**
 * WebSocket Client for CoinPulse Real-time Updates
 *
 * Features:
 * - Live price updates
 * - Order notifications
 * - Position changes
 * - Auto-reconnection
 */

class CoinPulseWebSocket {
    constructor(serverUrl = 'http://localhost:8080') {
        this.serverUrl = serverUrl;
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second

        // Event callbacks
        this.onPriceUpdate = null;
        this.onOrderNotification = null;
        this.onPositionUpdate = null;
        this.onConnect = null;
        this.onDisconnect = null;
        this.onError = null;

        // Subscribed markets
        this.subscribedMarkets = new Set();
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        console.log('[WebSocket] Connecting to:', this.serverUrl);

        // Load Socket.IO client library if not already loaded
        if (typeof io === 'undefined') {
            console.error('[WebSocket] Socket.IO client library not loaded');
            console.log('[WebSocket] Add this to HTML: <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>');
            return;
        }

        // Create Socket.IO connection
        this.socket = io(this.serverUrl, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: this.reconnectDelay,
            reconnectionDelayMax: 10000,
            reconnectionAttempts: this.maxReconnectAttempts
        });

        this._setupEventHandlers();
    }

    /**
     * Set up Socket.IO event handlers
     */
    _setupEventHandlers() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('[WebSocket] Connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;

            // Re-subscribe to markets after reconnection
            this.subscribedMarkets.forEach(market => {
                this._subscribe(market);
            });

            if (this.onConnect) {
                this.onConnect();
            }
        });

        this.socket.on('disconnect', (reason) => {
            console.log('[WebSocket] Disconnected:', reason);
            this.isConnected = false;

            if (this.onDisconnect) {
                this.onDisconnect(reason);
            }
        });

        this.socket.on('connect_error', (error) => {
            console.error('[WebSocket] Connection error:', error);

            if (this.onError) {
                this.onError(error);
            }
        });

        // Custom events
        this.socket.on('connected', (data) => {
            console.log('[WebSocket] Server welcome:', data);
        });

        this.socket.on('price_update', (data) => {
            if (this.onPriceUpdate) {
                this.onPriceUpdate(data);
            }
        });

        this.socket.on('order_notification', (data) => {
            if (this.onOrderNotification) {
                this.onOrderNotification(data);
            }
        });

        this.socket.on('position_update', (data) => {
            if (this.onPositionUpdate) {
                this.onPositionUpdate(data);
            }
        });

        this.socket.on('error', (data) => {
            console.error('[WebSocket] Server error:', data);
        });

        this.socket.on('pong', (data) => {
            // Ping/pong for keep-alive
        });
    }

    /**
     * Subscribe to market price updates
     */
    subscribeToMarket(market) {
        if (!this.isConnected) {
            console.warn('[WebSocket] Not connected. Call connect() first');
            return;
        }

        this.subscribedMarkets.add(market);
        this._subscribe(market);
    }

    /**
     * Internal subscribe method
     */
    _subscribe(market) {
        this.socket.emit('subscribe_market', { market: market });
        console.log('[WebSocket] Subscribed to:', market);

        this.socket.once('subscribed', (data) => {
            console.log('[WebSocket] Subscription confirmed:', data.market);
        });
    }

    /**
     * Unsubscribe from market price updates
     */
    unsubscribeFromMarket(market) {
        if (!this.isConnected) {
            return;
        }

        this.subscribedMarkets.delete(market);
        this.socket.emit('unsubscribe_market', { market: market });
        console.log('[WebSocket] Unsubscribed from:', market);
    }

    /**
     * Authenticate for user-specific notifications
     */
    authenticate(userId) {
        if (!this.isConnected) {
            console.warn('[WebSocket] Not connected');
            return;
        }

        this.socket.emit('authenticate', { user_id: userId });
        console.log('[WebSocket] Authenticating user:', userId);

        this.socket.once('authenticated', (data) => {
            console.log('[WebSocket] Authentication confirmed for user:', data.user_id);
        });
    }

    /**
     * Send ping to keep connection alive
     */
    ping() {
        if (this.isConnected) {
            this.socket.emit('ping');
        }
    }

    /**
     * Disconnect from server
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            console.log('[WebSocket] Disconnected by client');
        }
    }

    /**
     * Check connection status
     */
    isConnectedToServer() {
        return this.isConnected;
    }
}


// ==================== Usage Example ====================

/**
 * Example usage:
 *
 * // Initialize WebSocket
 * const ws = new CoinPulseWebSocket('http://localhost:8080');
 *
 * // Set up event handlers
 * ws.onConnect = () => {
 *     console.log('Connected to WebSocket!');
 *
 *     // Subscribe to Bitcoin price
 *     ws.subscribeToMarket('KRW-BTC');
 *
 *     // Authenticate user (if logged in)
 *     ws.authenticate(123);
 * };
 *
 * ws.onPriceUpdate = (data) => {
 *     console.log('Price update:', data.market, data.price);
 *     // Update UI with new price
 *     document.getElementById('btc-price').textContent = data.price.toLocaleString();
 * };
 *
 * ws.onOrderNotification = (notification) => {
 *     console.log('Order notification:', notification.data);
 *     // Show toast notification
 *     showToast(`Order ${notification.data.side}: ${notification.data.market}`);
 * };
 *
 * ws.onPositionUpdate = (update) => {
 *     console.log('Position update:', update.data);
 *     // Update portfolio display
 *     updatePortfolio(update.data);
 * };
 *
 * ws.onDisconnect = (reason) => {
 *     console.log('Disconnected:', reason);
 *     // Show reconnecting message
 * };
 *
 * // Connect
 * ws.connect();
 *
 * // Keep alive (optional - Socket.IO has built-in heartbeat)
 * setInterval(() => {
 *     if (ws.isConnectedToServer()) {
 *         ws.ping();
 *     }
 * }, 30000); // Every 30 seconds
 */


// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CoinPulseWebSocket;
}

// Make available globally
if (typeof window !== 'undefined') {
    window.CoinPulseWebSocket = CoinPulseWebSocket;
}
