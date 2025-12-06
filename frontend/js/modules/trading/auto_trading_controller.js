/**
 * ========================================
 * AUTO TRADING CONTROLLER MODULE
 * ========================================
 * Manages frontend auto-trading controls and API communication
 *
 * @class AutoTradingController
 * @description Handles auto-trading toggle buttons, status polling, and policy settings
 */

class AutoTradingController {
    constructor() {
        this.holdingsAutoEnabled = false;
        this.activeAutoEnabled = false;
        this.tradingServerUrl = '';
        this.pollingInterval = null;
        this.setupConfig();
    }

    /**
     * Load configuration from config.json
     */
    async setupConfig() {
        try {
            const response = await fetch('config.json');
            const config = await response.json();
            this.tradingServerUrl = config.api.tradingServerUrl || 'http://localhost:8081';
            console.log('[AutoTrading] Config loaded:', this.tradingServerUrl);

            // Setup event listeners after config is loaded
            this.setupEventListeners();

            // Load initial status
            await this.loadCurrentStatus();

            // Start polling for status updates
            this.startPolling();
        } catch (error) {
            console.error('[AutoTrading] Failed to load config:', error);
            // Use default
            this.tradingServerUrl = 'http://localhost:8081';
            this.setupEventListeners();
        }
    }

    /**
     * Setup event listeners for all auto-trading buttons
     */
    setupEventListeners() {
        // Active trading auto button
        const activeAutoBtn = document.getElementById('active-auto-btn');
        if (activeAutoBtn) {
            activeAutoBtn.addEventListener('click', () => {
                this.toggleActiveAuto();
            });
            console.log('[AutoTrading] Active auto button listener attached');
        }

        // Policy settings button
        const policyBtn = document.getElementById('policy-btn');
        if (policyBtn) {
            policyBtn.addEventListener('click', () => {
                this.showPolicySettings();
            });
            console.log('[AutoTrading] Policy button listener attached');
        }
    }

    /**
     * Load current auto-trading status from server
     */
    async loadCurrentStatus() {
        try {
            const response = await fetch(`${this.tradingServerUrl}/api/trading/status`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log('[AutoTrading] Current status:', data);

            // Update UI with current status
            this.holdingsAutoEnabled = data.auto_trading_enabled || false;
            this.updateButtonStatus('holdings-status', this.holdingsAutoEnabled);

        } catch (error) {
            console.error('[AutoTrading] Failed to load status:', error);
            this.updateButtonStatus('holdings-status', false);
        }
    }

    /**
     * Toggle holdings auto-trading
     */
    async toggleHoldingsAuto() {
        const newState = !this.holdingsAutoEnabled;
        console.log('[AutoTrading] Toggling holdings auto to:', newState);

        try {
            const response = await fetch(`${this.tradingServerUrl}/api/trading/enable`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({enabled: newState})
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            this.holdingsAutoEnabled = data.enabled;
            this.updateButtonStatus('holdings-status', this.holdingsAutoEnabled);

            console.log('[AutoTrading] Holdings auto-trading', this.holdingsAutoEnabled ? 'enabled' : 'disabled');

        } catch (error) {
            console.error('[AutoTrading] Failed to toggle holdings auto:', error);
            alert('Failed to toggle auto-trading. Check if trading server is running on port 8081.');
        }
    }

    /**
     * Toggle active trading auto (for short-term investments)
     */
    async toggleActiveAuto() {
        const newState = !this.activeAutoEnabled;
        console.log('[AutoTrading] Toggling active auto to:', newState);

        // For now, this uses same backend as holdings
        // In future, could have separate endpoint for active trading
        try {
            const response = await fetch(`${this.tradingServerUrl}/api/trading/enable`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({enabled: newState, mode: 'active'})
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            this.activeAutoEnabled = data.enabled;
            this.updateButtonStatus('active-status', this.activeAutoEnabled);

            console.log('[AutoTrading] Active auto-trading', this.activeAutoEnabled ? 'enabled' : 'disabled');

        } catch (error) {
            console.error('[AutoTrading] Failed to toggle active auto:', error);
            alert('Failed to toggle active auto-trading. Check if trading server is running on port 8081.');
        }
    }

    /**
     * Update button status text and styling
     */
    updateButtonStatus(elementId, enabled) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = enabled ? 'Active' : 'Inactive';
            const parentBtn = element.closest('.btn');
            if (parentBtn) {
                if (enabled) {
                    parentBtn.classList.add('active');
                    parentBtn.style.background = 'rgba(38, 166, 154, 0.2)';
                    parentBtn.style.borderColor = '#26a69a';
                } else {
                    parentBtn.classList.remove('active');
                    parentBtn.style.background = '';
                    parentBtn.style.borderColor = '';
                }
            }
        }
    }

    /**
     * Show policy settings modal
     */
    async showPolicySettings() {
        try {
            console.log('[AutoTrading] Loading policies...');
            const response = await fetch(`${this.tradingServerUrl}/api/trading/policies`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const policies = await response.json();
            console.log('[AutoTrading] Current policies:', policies);

            // Policy modal UI handles this now - no alert needed

        } catch (error) {
            console.error('[AutoTrading] Failed to load policies:', error);
            // Policy modal UI handles errors - no alert needed
        }
    }

    /**
     * Start polling for status updates every 10 seconds
     */
    startPolling() {
        // Clear existing interval if any
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }

        // Poll every 10 seconds
        this.pollingInterval = setInterval(async () => {
            await this.loadCurrentStatus();
        }, 10000);

        console.log('[AutoTrading] Status polling started (10s interval)');
    }

    /**
     * Stop polling
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
            console.log('[AutoTrading] Status polling stopped');
        }
    }
}

// Initialize AutoTradingController when document is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.autoTradingController = new AutoTradingController();
        console.log('[AutoTrading] Controller initialized on DOMContentLoaded');
    });
} else {
    // Document already loaded
    window.autoTradingController = new AutoTradingController();
    console.log('[AutoTrading] Controller initialized immediately');
}

// Export for module usage
if (typeof window !== 'undefined') {
    window.AutoTradingController = AutoTradingController;
}
