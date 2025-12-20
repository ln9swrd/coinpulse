/**
 * CoinPulse API Client
 * Centralized API communication library for frontend
 *
 * Features:
 * - JWT token management
 * - Automatic token refresh
 * - Error handling
 * - Request/Response interceptors
 * - TypeScript-style JSDoc annotations
 */

class CoinPulseAPI {
    /**
     * Initialize the API client
     * @param {string} baseURL - Base URL for API (default: current origin)
     */
    constructor(baseURL = window.location.origin) {
        this.baseURL = baseURL;
        this.accessToken = this.getAccessToken();
        this.refreshToken = this.getRefreshToken();
    }

    // ========================================================================
    // Token Management
    // ========================================================================

    /**
     * Get access token from localStorage
     * @returns {string|null}
     */
    getAccessToken() {
        return localStorage.getItem('access_token');
    }

    /**
     * Get refresh token from localStorage
     * @returns {string|null}
     */
    getRefreshToken() {
        return localStorage.getItem('refresh_token');
    }

    /**
     * Set access token in localStorage
     * @param {string} token
     */
    setAccessToken(token) {
        localStorage.setItem('access_token', token);
        this.accessToken = token;
    }

    /**
     * Set refresh token in localStorage
     * @param {string} token
     */
    setRefreshToken(token) {
        localStorage.setItem('refresh_token', token);
        this.refreshToken = token;
    }

    /**
     * Clear all tokens (logout)
     */
    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        this.accessToken = null;
        this.refreshToken = null;
    }

    /**
     * Check if user is authenticated
     * @returns {boolean}
     */
    isAuthenticated() {
        // Always check localStorage for latest token state
        const token = this.getAccessToken();
        this.accessToken = token; // Update cached value
        return token !== null && token !== '';
    }

    // ========================================================================
    // HTTP Request Methods
    // ========================================================================

    /**
     * Make HTTP request
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise<any>}
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        // Default headers
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        // Add authorization header if token exists
        if (this.accessToken && !options.skipAuth) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        }

        // Make request
        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            // Handle 401 Unauthorized (token expired)
            if (response.status === 401 && this.refreshToken && !options.skipRefresh) {
                // Try to refresh token
                const refreshed = await this.refreshAccessToken();
                if (refreshed) {
                    // Retry original request with new token
                    return this.request(endpoint, { ...options, skipRefresh: true });
                } else {
                    // Refresh failed, logout
                    this.clearTokens();
                    window.location.href = '/login.html';
                    throw new Error('Session expired, please login again');
                }
            }

            // Parse response
            const data = await response.json();

            // Handle non-2xx responses
            if (!response.ok) {
                throw new APIError(
                    data.error || 'Request failed',
                    response.status,
                    data.code || 'UNKNOWN_ERROR',
                    data
                );
            }

            return data;
        } catch (error) {
            // Network error or parsing error
            if (error instanceof APIError) {
                throw error;
            }
            throw new APIError(
                error.message || 'Network error',
                0,
                'NETWORK_ERROR'
            );
        }
    }

    /**
     * GET request
     * @param {string} endpoint
     * @param {Object} params - Query parameters
     * @returns {Promise<any>}
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST request
     * @param {string} endpoint
     * @param {Object} data - Request body
     * @returns {Promise<any>}
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     * @param {string} endpoint
     * @param {Object} data - Request body
     * @returns {Promise<any>}
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     * @param {string} endpoint
     * @returns {Promise<any>}
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // ========================================================================
    // Authentication APIs
    // ========================================================================

    /**
     * Register new user
     * @param {Object} userData
     * @param {string} userData.email
     * @param {string} userData.username
     * @param {string} userData.password
     * @param {string} [userData.full_name]
     * @returns {Promise<Object>}
     */
    async register(userData) {
        const response = await this.request('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData),
            skipAuth: true
        });
        return response;
    }

    /**
     * Login user
     * @param {string} email
     * @param {string} password
     * @returns {Promise<Object>}
     */
    async login(email, password) {
        const response = await this.request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
            skipAuth: true
        });

        // Save tokens
        if (response.success && response.access_token) {
            this.setAccessToken(response.access_token);
            this.setRefreshToken(response.refresh_token);
        }

        return response;
    }

    /**
     * Logout user
     * @returns {Promise<Object>}
     */
    async logout() {
        try {
            await this.request('/api/auth/logout', { method: 'POST' });
        } finally {
            // Always clear tokens, even if request fails
            this.clearTokens();
        }
    }

    /**
     * Refresh access token
     * @returns {Promise<boolean>} - True if refresh successful
     */
    async refreshAccessToken() {
        try {
            const response = await this.request('/api/auth/refresh', {
                method: 'POST',
                body: JSON.stringify({ refresh_token: this.refreshToken }),
                skipAuth: true,
                skipRefresh: true
            });

            if (response.success && response.access_token) {
                this.setAccessToken(response.access_token);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Token refresh failed:', error);
            return false;
        }
    }

    /**
     * Get current user info
     * @returns {Promise<Object>}
     */
    async getCurrentUser() {
        return this.get('/api/auth/me');
    }

    /**
     * Update user profile
     * @param {Object} profileData
     * @returns {Promise<Object>}
     */
    async updateProfile(profileData) {
        return this.put('/api/auth/profile', profileData);
    }

    /**
     * Update Upbit API keys
     * @param {string} accessKey
     * @param {string} secretKey
     * @returns {Promise<Object>}
     */
    async updateUpbitKeys(accessKey, secretKey) {
        return this.put('/api/auth/update-upbit-keys', {
            access_key: accessKey,
            secret_key: secretKey
        });
    }

    // ========================================================================
    // Portfolio APIs
    // ========================================================================

    /**
     * Get user holdings
     * @returns {Promise<Object>}
     */
    async getHoldings() {
        return this.get('/api/holdings');
    }

    /**
     * Get order history
     * @param {Object} params
     * @param {string} [params.market]
     * @param {string} [params.state]
     * @param {number} [params.limit]
     * @returns {Promise<Object>}
     */
    async getOrders(params = {}) {
        return this.get('/api/orders', params);
    }

    // ========================================================================
    // Auto Trading APIs
    // ========================================================================

    /**
     * Start auto trading
     * @param {Object} config - Optional configuration (budget, positions, etc.)
     * @returns {Promise<Object>}
     */
    async startAutoTrading(config = {}) {
        // Get current user to extract user_id
        const userResponse = await this.getCurrentUser();
        if (!userResponse || !userResponse.user || !userResponse.user.id) {
            throw new Error('User not authenticated');
        }

        const userId = userResponse.user.id;
        const updateData = {
            auto_trading_enabled: true,
            ...config
        };

        return this.put(`/api/auto-trading/config/${userId}`, updateData);
    }

    /**
     * Stop auto trading
     * @returns {Promise<Object>}
     */
    async stopAutoTrading() {
        // Get current user to extract user_id
        const userResponse = await this.getCurrentUser();
        if (!userResponse || !userResponse.user || !userResponse.user.id) {
            throw new Error('User not authenticated');
        }

        const userId = userResponse.user.id;
        const updateData = {
            auto_trading_enabled: false
        };

        return this.put(`/api/auto-trading/config/${userId}`, updateData);
    }

    /**
     * Get auto trading status
     * @returns {Promise<Object>}
     */
    async getAutoTradingStatus() {
        // Get current user to extract user_id
        const response = await this.getCurrentUser();
        if (!response || !response.user || !response.user.id) {
            throw new Error('User not authenticated');
        }
        return this.get(`/api/auto-trading/status/${response.user.id}`);
    }

    /**
     * Get auto trading configuration
     * @returns {Promise<Object>}
     */
    async getAutoTradingConfig() {
        // Get current user to extract user_id
        const response = await this.getCurrentUser();
        if (!response || !response.user || !response.user.id) {
            throw new Error('User not authenticated');
        }
        return this.get(`/api/auto-trading/config/${response.user.id}`);
    }

    /**
     * Update auto trading configuration
     * @param {Object} config - Configuration to update
     * @returns {Promise<Object>}
     */
    async updateAutoTradingConfig(config) {
        // Get current user to extract user_id
        const response = await this.getCurrentUser();
        if (!response || !response.user || !response.user.id) {
            throw new Error('User not authenticated');
        }
        return this.put(`/api/auto-trading/config/${response.user.id}`, config);
    }

    /**
     * Get open trading positions
     * @returns {Promise<Object>}
     */
    async getAutoTradingPositions() {
        // Get current user to extract user_id
        const response = await this.getCurrentUser();
        if (!response || !response.user || !response.user.id) {
            throw new Error('User not authenticated');
        }
        return this.get(`/api/auto-trading/positions/${response.user.id}`);
    }

    /**
     * Get auto trading history
     * @param {number} limit - Number of records to fetch
     * @returns {Promise<Object>}
     */
    async getAutoTradingHistory(limit = 50) {
        // Get current user to extract user_id
        const response = await this.getCurrentUser();
        if (!response || !response.user || !response.user.id) {
            throw new Error('User not authenticated');
        }
        return this.get(`/api/auto-trading/history/${response.user.id}`, { limit });
    }

    // ========================================================================
    // Subscription APIs
    // ========================================================================

    /**
     * Get subscription plans
     * @returns {Promise<Object>}
     */
    async getSubscriptionPlans() {
        return this.get('/api/subscription/plans');
    }

    /**
     * Subscribe to a plan
     * @param {string} planId
     * @returns {Promise<Object>}
     */
    async subscribe(planId) {
        return this.post('/api/subscription/subscribe', { plan_id: planId });
    }

    /**
     * Get current subscription
     * @returns {Promise<Object>}
     */
    async getCurrentSubscription() {
        return this.get('/api/subscription/current');
    }

    // ========================================================================
    // Utility Methods
    // ========================================================================

    /**
     * Check server health
     * @returns {Promise<Object>}
     */
    async checkHealth() {
        return this.get('/health', {}, { skipAuth: true });
    }

    /**
     * Get API status
     * @returns {Promise<Object>}
     */
    async getStatus() {
        return this.get('/api/status', {}, { skipAuth: true });
    }
}

// ============================================================================
// Custom Error Class
// ============================================================================

class APIError extends Error {
    /**
     * @param {string} message
     * @param {number} status
     * @param {string} code
     * @param {Object} [details]
     */
    constructor(message, status, code, details = {}) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.code = code;
        this.details = details;
    }
}

// ============================================================================
// Export (for use in HTML files)
// ============================================================================

// Create global instance
window.api = new CoinPulseAPI();
window.APIError = APIError;

// For module systems (if needed later)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CoinPulseAPI, APIError };
}
