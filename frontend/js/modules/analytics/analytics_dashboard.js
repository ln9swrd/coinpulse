/**
 * Analytics Dashboard Module
 *
 * Displays trading statistics from database
 */

class AnalyticsDashboard {
    constructor(apiHandler) {
        this.apiHandler = apiHandler;
        this.stats = null;
        this.updateInterval = null;
    }

    /**
     * Initialize analytics dashboard
     */
    async init() {
        console.log('[Analytics] Initializing dashboard');

        // Create dashboard UI if not exists
        this.createDashboardUI();

        // Load initial data
        await this.loadStatistics();

        // Auto-refresh every 30 seconds
        this.startAutoRefresh(30000);
    }

    /**
     * Create dashboard UI elements
     */
    createDashboardUI() {
        // Check if dashboard already exists
        if (document.getElementById('analytics-dashboard')) {
            return;
        }

        const dashboard = document.createElement('div');
        dashboard.id = 'analytics-dashboard';
        dashboard.className = 'analytics-dashboard';
        dashboard.innerHTML = `
            <div class="analytics-header">
                <h3>Trading Statistics (DB)</h3>
                <button id="refresh-analytics" class="btn-small">Refresh</button>
            </div>
            <div class="analytics-content">
                <div class="stat-card">
                    <div class="stat-label">Total Orders</div>
                    <div class="stat-value" id="stat-total-orders">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Fees</div>
                    <div class="stat-value" id="stat-total-fees">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Buy Orders</div>
                    <div class="stat-value" id="stat-buy-orders">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Sell Orders</div>
                    <div class="stat-value" id="stat-sell-orders">-</div>
                </div>
            </div>
            <div class="analytics-markets" id="analytics-markets">
                <h4>Top Markets</h4>
                <div id="markets-list"></div>
            </div>
        `;

        // Insert before chart container
        const chartContainer = document.getElementById('chart-container');
        if (chartContainer && chartContainer.parentElement) {
            chartContainer.parentElement.insertBefore(dashboard, chartContainer);
        } else {
            document.body.appendChild(dashboard);
        }

        // Add event listeners
        document.getElementById('refresh-analytics').addEventListener('click', () => {
            this.loadStatistics();
        });

        console.log('[Analytics] Dashboard UI created');
    }

    /**
     * Load statistics from database
     */
    async loadStatistics() {
        console.log('[Analytics] Loading statistics');

        try {
            const result = await this.apiHandler.getOrderStatistics();

            if (!result.success) {
                throw new Error(result.error || 'Failed to load statistics');
            }

            this.stats = result.stats;
            this.updateDisplay();

        } catch (error) {
            console.error('[Analytics] Error loading statistics:', error);
            this.showError('Failed to load statistics');
        }
    }

    /**
     * Update dashboard display with loaded data
     */
    updateDisplay() {
        if (!this.stats) return;

        // Update total orders
        document.getElementById('stat-total-orders').textContent =
            this.stats.total_orders || 0;

        // Update total fees
        document.getElementById('stat-total-fees').textContent =
            window.formatPrice(this.stats.total_fees || 0);

        // Update buy/sell counts
        const bidStats = this.stats.by_side.find(s => s.side === 'bid');
        const askStats = this.stats.by_side.find(s => s.side === 'ask');

        document.getElementById('stat-buy-orders').textContent =
            bidStats ? bidStats.count : 0;

        document.getElementById('stat-sell-orders').textContent =
            askStats ? askStats.count : 0;

        // Update markets list (top 5)
        this.updateMarketsList();

        console.log('[Analytics] Display updated');
    }

    /**
     * Update top markets list
     */
    updateMarketsList() {
        if (!this.stats || !this.stats.by_market) return;

        const marketsList = document.getElementById('markets-list');
        const topMarkets = this.stats.by_market
            .sort((a, b) => b.count - a.count)
            .slice(0, 5);

        marketsList.innerHTML = topMarkets.map(market => `
            <div class="market-row">
                <span class="market-name">${market.market}</span>
                <span class="market-count">${market.count} orders</span>
            </div>
        `).join('');
    }

    /**
     * Show error message
     */
    showError(message) {
        const dashboard = document.getElementById('analytics-dashboard');
        if (dashboard) {
            dashboard.classList.add('error');
            setTimeout(() => {
                dashboard.classList.remove('error');
            }, 3000);
        }
        window.showNotification(message, 'error');
    }

    /**
     * Start auto-refresh
     */
    startAutoRefresh(interval = 30000) {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        this.updateInterval = setInterval(() => {
            this.loadStatistics();
        }, interval);

        console.log('[Analytics] Auto-refresh started (interval:', interval, 'ms)');
    }

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
            console.log('[Analytics] Auto-refresh stopped');
        }
    }

    /**
     * Destroy dashboard
     */
    destroy() {
        this.stopAutoRefresh();

        const dashboard = document.getElementById('analytics-dashboard');
        if (dashboard) {
            dashboard.remove();
        }

        console.log('[Analytics] Dashboard destroyed');
    }
}

// Export to window
if (typeof window !== 'undefined') {
    window.AnalyticsDashboard = AnalyticsDashboard;
}
