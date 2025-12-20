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
        this.pollingInterval = null;
        this.apiClient = null;
        this.init();
    }

    /**
     * Initialize the controller
     */
    async init() {
        // Wait for API client to be available
        await this.waitForAPIClient();

        // Setup event listeners
        this.setupEventListeners();

        // Load initial status
        await this.loadCurrentStatus();

        // Start polling for status updates
        this.startPolling();
    }

    /**
     * Wait for API client to be initialized
     */
    async waitForAPIClient() {
        let attempts = 0;
        while (!window.api && attempts < 50) {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }

        if (window.api) {
            this.apiClient = window.api;
            console.log('[AutoTrading] API client ready');
        } else {
            console.error('[AutoTrading] API client not available');
            throw new Error('API client not initialized');
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
            const response = await this.apiClient.getAutoTradingStatus();
            console.log('[AutoTrading] Current status:', response);

            if (response.success) {
                // Update UI with current status
                this.holdingsAutoEnabled = response.auto_trading_enabled || false;
                this.updateButtonStatus('holdings-status', this.holdingsAutoEnabled);
            } else {
                throw new Error(response.error || 'Failed to load status');
            }

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
            const response = newState
                ? await this.apiClient.startAutoTrading()
                : await this.apiClient.stopAutoTrading();

            if (response.success) {
                this.holdingsAutoEnabled = newState;
                this.updateButtonStatus('holdings-status', this.holdingsAutoEnabled);
                console.log('[AutoTrading] Holdings auto-trading', this.holdingsAutoEnabled ? 'enabled' : 'disabled');
            } else {
                throw new Error(response.error || 'Failed to toggle auto-trading');
            }

        } catch (error) {
            console.error('[AutoTrading] Failed to toggle holdings auto:', error);
            alert(`자동 거래 ${newState ? '시작' : '중지'} 실패: ${error.message}`);
        }
    }

    /**
     * Toggle active trading auto (for short-term investments)
     */
    async toggleActiveAuto() {
        const newState = !this.activeAutoEnabled;
        console.log('[AutoTrading] Toggling active auto to:', newState);

        try {
            // For now, this uses same backend as holdings
            // In future, could have separate endpoint for active trading
            const response = newState
                ? await this.apiClient.startAutoTrading()
                : await this.apiClient.stopAutoTrading();

            if (response.success) {
                this.activeAutoEnabled = newState;
                this.updateButtonStatus('active-status', this.activeAutoEnabled);
                console.log('[AutoTrading] Active auto-trading', this.activeAutoEnabled ? 'enabled' : 'disabled');
            } else {
                throw new Error(response.error || 'Failed to toggle auto-trading');
            }

        } catch (error) {
            console.error('[AutoTrading] Failed to toggle active auto:', error);
            alert(`활성 자동 거래 ${newState ? '시작' : '중지'} 실패: ${error.message}`);
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
            console.log('[AutoTrading] Loading auto-trading config...');
            const response = await this.apiClient.getAutoTradingConfig();

            if (response.success) {
                console.log('[AutoTrading] Current config:', response.config);
                // Policy modal UI handles this now - no alert needed
            } else {
                throw new Error(response.error || 'Failed to load config');
            }

        } catch (error) {
            console.error('[AutoTrading] Failed to load config:', error);
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
